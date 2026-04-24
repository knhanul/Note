"""Note controller for managing note operations with SQLite persistence."""
from typing import List, Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QVariant, QThread
from PyQt6.QtGui import QClipboard, QImage
from PyQt6.QtWidgets import QApplication, QCalendarWidget, QVBoxLayout, QPushButton, QDialog, QHBoxLayout
from datetime import datetime, date
import uuid
import re
import hashlib

from services.database import Database
from services.note_service import NoteService
from services.image_service import ImageService
from services.library_service import LibraryService


class _NoteSaveWorker(QObject):
    finished = pyqtSignal(bool)

    def __init__(self, db_path: str, note_id: str,
                 title: Optional[str], content: str, content_json: Optional[str]):
        super().__init__()
        self._db_path = db_path
        self._note_id = note_id
        self._title = title
        self._content = content
        self._content_json = content_json

    @pyqtSlot()
    def run(self):
        ok = False
        db = None
        try:
            db = Database(self._db_path)
            note_service = NoteService(db)
            ok = note_service.update(
                self._note_id,
                title=self._title,
                content=self._content,
                content_json=self._content_json
            )
        except Exception:
            ok = False
        finally:
            try:
                if db:
                    db.close()
            except Exception:
                pass
            self.finished.emit(ok)


class NoteController(QObject):
    """Controller for note management with SQLite persistence and QML integration."""

    SMART_ALL = "smart:all"
    SMART_FAVORITES = "smart:favorites"
    
    # Signals
    notesChanged = pyqtSignal()
    filteredNotesChanged = pyqtSignal()
    tagsChanged = pyqtSignal()
    noteAdded = pyqtSignal(str)  # note_id
    noteRemoved = pyqtSignal(str)  # note_id
    noteUpdated = pyqtSignal(str)  # note_id
    saveStatusChanged = pyqtSignal()  # For save status updates
    libraryChanged = pyqtSignal()  # Emitted when library changes

    _DATA_URL_PATTERN = re.compile(r"data:(image/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=\r\n]+)")
    _TOKEN_PATTERN = re.compile(r"note-image://([a-zA-Z0-9_-]+)")
    
    def __init__(self, library_service: LibraryService, folder_controller, parent=None):
        super().__init__(parent)
        self._folder_controller = folder_controller
        self._library_service = library_service
        
        # Services will be initialized when library is set
        self._note_service: Optional[NoteService] = None
        self._image_service = ImageService()

        # Current state
        self._current_note_id: Optional[str] = None
        self._is_dirty: bool = False
        self._is_saving: bool = False
        self._save_status: str = "saved"  # saved, saving, dirty

        # Sorting and filtering state
        self._sort_field: str = "updated_at"  # updated_at, created_at, title
        self._sort_order: str = "desc"        # asc, desc
        self._search_keyword: str = ""
        self._filter_from_date: str = ""      # YYYY-MM-DD
        self._filter_to_date: str = ""        # YYYY-MM-DD
        self._selected_tag: str = ""          # active tag filter

        # Pending data for deferred save (for batching until explicit save)
        self._pending_title = None
        self._pending_content = None
        self._pending_json = None
        self._current_note_data = {}
        self._save_thread: Optional[QThread] = None
        self._save_worker: Optional[_NoteSaveWorker] = None
        self._save_queued: bool = False

        # Connect to signals
        self._folder_controller.currentFolderChanged.connect(self._on_folder_changed)
        self._library_service.currentLibraryChanged.connect(self._on_library_changed)
        self._folder_controller.libraryChanged.connect(self._on_folder_changed)

        # Initialize with current library
        self._on_library_changed()
    
    def _on_library_changed(self):
        """Handle library change - reload notes from new database."""
        db = self._library_service.get_current_database()
        if db:
            self._note_service = NoteService(db)
            self._current_note_id = None
            self._is_dirty = False
            self._save_status = "saved"
            self._selected_tag = ""
            self.notesChanged.emit()  # Clear notes view immediately
            self.filteredNotesChanged.emit()
            self.tagsChanged.emit()
            self._on_folder_changed()  # Reload notes for current folder
            self.libraryChanged.emit()
            self.saveStatusChanged.emit()
    
    # Default notes initialization removed - app starts with empty state
    def _on_folder_changed(self):
        """Handle folder change - emit filtered notes changed."""
        self.filteredNotesChanged.emit()
    
    def _perform_save(self):
        """Perform save operation asynchronously (called on Enter/focus-out)."""
        if not self._is_dirty or not self._current_note_id:
            return False

        # If a save is already in-flight, queue another save pass.
        if self._is_saving:
            self._save_queued = True
            return True

        if not self._note_service or not self._note_service.db:
            return False

        self._is_saving = True
        self._save_status = "saving"
        self.saveStatusChanged.emit()

        note_id = self._current_note_id
        title_to_save = self._pending_title if self._pending_title is not None else None
        content_to_save = self._pending_content if self._pending_content is not None else self._current_note_data.get('content', '')
        json_to_save = self._pending_json if self._pending_json is not None else self._current_note_data.get('content_json', '')

        # Tokenize image payloads in main thread, then persist note row in worker thread.
        if self._pending_title is not None or self._pending_content is not None or self._pending_json is not None:
            tok_content, tok_json = self._store_data_urls_and_tokenize(
                note_id,
                content_to_save,
                json_to_save
            )

            content_to_save = tok_content
            json_to_save = tok_json if tok_json else None

        # Clear pending data snapshot; if new edits come in during save,
        # updateNoteWithJson will repopulate pending fields and mark dirty again.
        self._pending_title = None
        self._pending_content = None
        self._pending_json = None
        self._is_dirty = False

        db_path = self._note_service.db.db_path
        self._start_async_note_update(note_id, title_to_save, content_to_save, json_to_save)
        return True

    def _start_async_note_update(self, note_id: str, title: Optional[str],
                                 content: str, content_json: Optional[str]) -> None:
        self._save_thread = QThread(self)
        self._save_worker = _NoteSaveWorker(
            db_path=self._note_service.db.db_path,
            note_id=note_id,
            title=title,
            content=content,
            content_json=content_json
        )
        self._save_worker.moveToThread(self._save_thread)

        self._save_thread.started.connect(self._save_worker.run)
        self._save_worker.finished.connect(self._on_async_save_finished)
        self._save_worker.finished.connect(self._save_thread.quit)
        self._save_worker.finished.connect(self._save_worker.deleteLater)
        self._save_thread.finished.connect(self._save_thread.deleteLater)

        self._save_thread.start()

    @pyqtSlot(bool)
    def _on_async_save_finished(self, ok: bool) -> None:
        self._save_worker = None
        self._save_thread = None
        self._is_saving = False

        if not ok:
            self._is_dirty = True
            self._save_status = "dirty"
            self.saveStatusChanged.emit()
            return

        has_new_pending = (
            self._pending_title is not None or
            self._pending_content is not None or
            self._pending_json is not None
        )

        if self._save_queued or has_new_pending:
            self._save_queued = False
            self._is_dirty = True
            self._save_status = "dirty"
            self.saveStatusChanged.emit()
            self._perform_save()
            return

        self._save_status = "saved"
        self.saveStatusChanged.emit()

    def _extract_tokens(self, content: str) -> List[str]:
        return [m.group(1) for m in self._TOKEN_PATTERN.finditer(content or "")]

    def _store_data_urls_and_tokenize(self, note_id: str,
                                        content: str,
                                        content_json: str = "") -> tuple:
        """Replace data URLs in markdown+json with note-image:// tokens.

        Returns (tokenized_content, tokenized_json).
        """
        def _replace(match):
            mime_type  = match.group(1)
            data_b64   = match.group(2).replace("\n", "").replace("\r", "")
            checksum   = hashlib.sha256(f"{mime_type}:{data_b64}".encode()).hexdigest()
            image_id   = self._note_service.upsert_note_image(note_id, mime_type, data_b64, checksum)
            return f"note-image://{image_id}"

        tok_content = self._DATA_URL_PATTERN.sub(_replace, content) if content else content
        tok_json    = self._DATA_URL_PATTERN.sub(_replace, content_json) if content_json else content_json

        all_ids = self._extract_tokens(tok_content) + self._extract_tokens(tok_json)
        keep_ids = list(dict.fromkeys(all_ids))
        self._note_service.delete_unused_note_images(note_id, keep_ids)
        return tok_content, tok_json

    def _hydrate_image_tokens(self, content: str) -> str:
        """Replace note-image:// tokens with data URLs for editor rendering."""
        if not content:
            return content

        def _replace(match):
            row = self._note_service.get_note_image(match.group(1))
            if not row:
                return ""
            return f"data:{row['mime_type']};base64,{row['data_base64']}"

        return self._TOKEN_PATTERN.sub(_replace, content)
    
    # Properties
    @pyqtProperty(list, notify=notesChanged)
    def allNotes(self):
        """Get all notes as list of dicts for QML."""
        return self._note_service.get_all()
    
    @pyqtProperty(list, notify=filteredNotesChanged)
    def filteredNotes(self):
        """Get notes filtered by current folder with sorting and search."""
        current_folder_id = self._folder_controller.currentFolderId
        tag_filter = self._selected_tag or None
        if current_folder_id == self.SMART_ALL:
            notes = self._note_service.get_all(tag=tag_filter)
        elif current_folder_id == self.SMART_FAVORITES:
            notes = self._note_service.get_pinned(ensure_note_id=self._current_note_id)
            if tag_filter:
                notes = [n for n in notes if any(
                    t == tag_filter or t.startswith(tag_filter + '/') for t in n.get('tags', [])
                )]
        else:
            notes = self._note_service.get_all(folder_id=current_folder_id or None, tag=tag_filter)

        return self._apply_sort_and_filter(notes)

    @pyqtProperty(list, notify=tagsChanged)
    def allTags(self):
        """Get all tags with counts for the current library."""
        if not self._note_service:
            return []
        return self._note_service.get_all_tags()

    @pyqtProperty(str, notify=tagsChanged)
    def selectedTag(self) -> str:
        """Get currently selected tag filter."""
        return self._selected_tag
    
    @pyqtProperty(str, notify=filteredNotesChanged)
    def currentFolderName(self) -> str:
        """Get current folder name for display."""
        return self._folder_controller.currentFolderName
    
    @pyqtProperty(str, notify=saveStatusChanged)
    def saveStatus(self) -> str:
        """Get current save status."""
        return self._save_status
    
    @pyqtProperty(str, notify=notesChanged)
    def currentNoteId(self) -> str:
        """Get currently selected note ID."""
        return self._current_note_id or ""
    
    @pyqtProperty(bool, notify=saveStatusChanged)
    def isDirty(self) -> bool:
        """Check if there are unsaved changes."""
        return self._is_dirty
    
    @pyqtProperty(bool, notify=saveStatusChanged)
    def isSaving(self) -> bool:
        """Check if currently saving."""
        return self._is_saving

    # Sorting and filtering properties
    @pyqtProperty(str, notify=filteredNotesChanged)
    def sortField(self) -> str:
        """Get current sort field."""
        return self._sort_field

    @pyqtProperty(str, notify=filteredNotesChanged)
    def sortOrder(self) -> str:
        """Get current sort order."""
        return self._sort_order

    @pyqtProperty(str, notify=filteredNotesChanged)
    def searchKeyword(self) -> str:
        """Get current search keyword."""
        return self._search_keyword

    @pyqtSlot()
    def toggleSortOrder(self):
        """Toggle between asc and desc order."""
        self._sort_order = "asc" if self._sort_order == "desc" else "desc"
        self.filteredNotesChanged.emit()

    @pyqtSlot(str)
    def setSearchKeyword(self, keyword: str):
        """Set search keyword and refresh notes."""
        self._search_keyword = keyword.strip()
        self.filteredNotesChanged.emit()

    @pyqtProperty(str, notify=filteredNotesChanged)
    def filterFromDate(self) -> str:
        """Get from-date filter (YYYY-MM-DD)."""
        return self._filter_from_date

    @pyqtProperty(str, notify=filteredNotesChanged)
    def filterToDate(self) -> str:
        """Get to-date filter (YYYY-MM-DD)."""
        return self._filter_to_date

    @pyqtProperty(bool, notify=filteredNotesChanged)
    def isFilterActive(self) -> bool:
        """Check if any filter condition is active."""
        return (self._search_keyword != "" or
                self._filter_from_date != "" or
                self._filter_to_date != "")

    @pyqtSlot(str)
    def setFilterFromDate(self, date: str):
        """Set start date filter (YYYY-MM-DD)."""
        self._filter_from_date = date.strip()
        self.filteredNotesChanged.emit()

    @pyqtSlot(str)
    def setFilterToDate(self, date: str):
        """Set end date filter (YYYY-MM-DD)."""
        self._filter_to_date = date.strip()
        self.filteredNotesChanged.emit()

    @pyqtSlot(str, result=str)
    def showCalendarDialog(self, currentDate: str = "") -> str:
        """Show calendar dialog and return selected date (YYYY-MM-DD)."""
        dialog = QDialog()
        dialog.setWindowTitle("날짜 선택")
        dialog.setMinimumWidth(280)
        dialog.setMinimumHeight(320)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        calendar = QCalendarWidget()
        if currentDate:
            try:
                d = datetime.strptime(currentDate, "%Y-%m-%d").date()
                calendar.setSelectedDate(d)
            except:
                pass
        layout.addWidget(calendar)

        result = {"date": ""}

        def onSelect():
            selected = calendar.selectedDate().toPyDate()
            result["date"] = selected.strftime("%Y-%m-%d")
            dialog.close()

        def onCancel():
            dialog.close()

        btnLayout = QHBoxLayout()
        selectBtn = QPushButton("선택")
        selectBtn.clicked.connect(onSelect)
        cancelBtn = QPushButton("취소")
        cancelBtn.clicked.connect(onCancel)
        btnLayout.addStretch()
        btnLayout.addWidget(cancelBtn)
        btnLayout.addWidget(selectBtn)
        layout.addLayout(btnLayout)

        dialog.exec()
        return result["date"]

    @pyqtSlot(str)
    def setSortField(self, field: str):
        """Set sort field, reset date filters when switching to title or content."""
        if field in ("updated_at", "created_at", "title", "content"):
            if field in ("title", "content"):
                self._filter_from_date = ""
                self._filter_to_date = ""
            self._sort_field = field
            self.filteredNotesChanged.emit()

    def _apply_sort_and_filter(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply search filter and sorting to notes list."""
        # Filter by search keyword (title + content)
        if self._search_keyword:
            keyword_lower = self._search_keyword.lower()
            notes = [
                n for n in notes
                if keyword_lower in (n.get("title") or "").lower()
                or keyword_lower in (n.get("content") or "").lower()
            ]

        # Filter by date range (only when sort field is date-based)
        if self._sort_field in ("created_at", "updated_at"):
            field = self._sort_field
            if self._filter_from_date:
                notes = [n for n in notes if (n.get(field) or "")[:10] >= self._filter_from_date]
            if self._filter_to_date:
                notes = [n for n in notes if (n.get(field) or "")[:10] <= self._filter_to_date]

        # Sort notes
        reverse = self._sort_order == "desc"
        if self._sort_field == "title":
            notes = sorted(notes, key=lambda n: (n.get("title") or "").lower(), reverse=reverse)
        elif self._sort_field == "content":
            # Sort by content length (longer first if desc)
            notes = sorted(notes, key=lambda n: len(n.get("content") or ""), reverse=reverse)
        else:
            notes = sorted(notes, key=lambda n: n.get(self._sort_field) or "", reverse=reverse)

        return notes
    
    # Slots
    @pyqtSlot(str, str, str, result=str)
    def createNote(self, title: str, content: str = "", folder_id: str = "") -> str:
        """Create a new note in the specified folder."""
        # Use current folder if not specified
        if not folder_id:
            folder_id = self._folder_controller.currentFolderId

        # Smart folders are virtual, so fallback to first regular folder
        if self._folder_controller.isSmartFolder(folder_id):
            folder_id = self._folder_controller.getFirstRegularFolderId()
        
        if not folder_id:
            return ""
        
        note_id = str(uuid.uuid4())[:8]
        
        tok_content, tok_json = self._store_data_urls_and_tokenize(note_id, content)

        if self._note_service.create(note_id, folder_id, title, tok_content):
            self._current_note_id = note_id
            self._is_dirty = False
            self._save_status = "saved"
            
            self.notesChanged.emit()
            self.filteredNotesChanged.emit()
            self.noteAdded.emit(note_id)
            self.saveStatusChanged.emit()
            
            return note_id
        
        return ""
    
    @pyqtSlot(str)
    def selectTag(self, tag: str):
        """Set active tag filter; selecting the same tag clears it."""
        if self._selected_tag == tag:
            self._selected_tag = ""
        else:
            self._selected_tag = tag
        self.tagsChanged.emit()
        self.filteredNotesChanged.emit()

    @pyqtSlot()
    def clearTagFilter(self):
        """Clear active tag filter."""
        if self._selected_tag:
            self._selected_tag = ""
            self.tagsChanged.emit()
            self.filteredNotesChanged.emit()

    @pyqtSlot(str, 'QVariantList', result=bool)
    def updateNoteTags(self, note_id: str, tags: list) -> bool:
        """Update the tags for a note."""
        if not note_id or not self._note_service:
            return False
        tag_list = [str(t).strip() for t in tags if str(t).strip()]
        if self._note_service.update_tags(note_id, tag_list):
            self.tagsChanged.emit()
            self.filteredNotesChanged.emit()
            return True
        return False

    @pyqtSlot(str, result=bool)
    def deleteNote(self, note_id: str) -> bool:
        """Soft delete a note by ID."""
        if self._note_service.soft_delete(note_id):
            if self._current_note_id == note_id:
                self._current_note_id = None
            
            self.notesChanged.emit()
            self.filteredNotesChanged.emit()
            self.tagsChanged.emit()
            self.noteRemoved.emit(note_id)
            return True
        
        return False
    
    @pyqtSlot(str, str, str, result=bool)
    def updateNote(self, note_id: str, title: str, content: str) -> bool:
        """Update note title and content (Markdown only, backward-compatible)."""
        return self.updateNoteWithJson(note_id, title, content, "")

    @pyqtSlot(str, str, str, str, result=bool)
    def updateNoteWithJson(self, note_id: str, title: str, content: str, content_json: str) -> bool:
        """Update note with both Markdown and TipTap JSON content (deferred save)."""
        if not note_id:
            return False

        self._current_note_id = note_id
        
        # Track pending changes
        self._pending_title = title if title != self._current_note_data.get('title') else None
        self._pending_content = content if content != self._current_note_data.get('content') else None
        self._pending_json = content_json if content_json != self._current_note_data.get('content_json') else None
        
        # Update cached data immediately for UI responsiveness
        self._current_note_data['title'] = title
        self._current_note_data['content'] = content
        self._current_note_data['content_json'] = content_json
        
        self._is_dirty = True
        self._save_status = "dirty"
        
        # Emit immediate status change
        self.saveStatusChanged.emit()
        
        # Note: auto-save now happens on Enter key or focus out, not on timer
        
        # Only emit list signals on title change (expensive)
        if self._pending_title is not None:
            self.notesChanged.emit()
            self.filteredNotesChanged.emit()
        
        # Always emit noteUpdated for content updates (lightweight)
        self.noteUpdated.emit(note_id)
        
        return True
    
    @pyqtSlot(result=bool)
    def saveCurrentNote(self) -> bool:
        """Save current note (called on Enter or focus out)."""
        return self._perform_save()
    
    @pyqtSlot(str, str, result=bool)
    def moveNoteToFolder(self, note_id: str, folder_id: str) -> bool:
        """Move a note to a different folder."""
        if self._note_service.move_to_folder(note_id, folder_id):
            self.notesChanged.emit()
            self.filteredNotesChanged.emit()
            return True
        return False
    
    @pyqtSlot(str, result=QVariant)
    def getNote(self, note_id: str) -> QVariant:
        """Get a single note by ID, with image tokens hydrated in both formats."""
        note = self._note_service.get_by_id(note_id)
        if note:
            note['content']      = self._hydrate_image_tokens(note.get('content', ''))
            note['content_json'] = self._hydrate_image_tokens(note.get('content_json', '') or '')
            return QVariant(note)
        return QVariant()
    
    def _is_note_empty(self, note_id: str) -> bool:
        """Check if note is effectively empty (default title + no content)."""
        note = self._note_service.get_by_id(note_id)
        if not note:
            return False
        title = note.get('title', '') or ''
        content = note.get('content', '') or ''
        normalized = content.strip()
        lowered = normalized.lower()

        has_media = bool(re.search(r"<(img|video|audio|iframe|embed|object)\\b", content, re.IGNORECASE))
        has_image_token = "note-image://" in content or "data:image/" in content

        # TipTap/HTML editor often stores placeholder markup even when user entered nothing.
        if has_media or has_image_token:
            is_empty_content = False
        elif lowered in ("<p></p>", "<p><br></p>", "<p><br/></p>", "<div><br></div>"):
            is_empty_content = True
        else:
            plain = re.sub(r"<[^>]+>", "", content)
            plain = plain.replace("&nbsp;", " ").replace("\u00a0", " ").replace("\u200b", "").strip()
            is_empty_content = plain == ""

        # Empty if title is default/blank and content is effectively empty
        is_default_title = title in ('', '새 노트', '제목 없는 노트')
        return is_default_title and is_empty_content

    @pyqtSlot(str, result=bool)
    def selectNote(self, note_id: str) -> bool:
        """Select a note (set as current)."""
        # If switching to different note, check if current note is empty and delete it
        if self._current_note_id and self._current_note_id != note_id:
            if self._is_note_empty(self._current_note_id):
                # Delete empty note without saving
                self._note_service.hard_delete(self._current_note_id)  # Hard delete empty note
                self.notesChanged.emit()
                self.filteredNotesChanged.emit()
                self.tagsChanged.emit()
                self.noteRemoved.emit(self._current_note_id)
            elif self._is_dirty:
                # Save current note if dirty before switching
                self.saveCurrentNote()

        note = self._note_service.get_by_id(note_id)
        if note:
            self._current_note_id = note_id
            self._is_dirty = False
            self._save_status = "saved"
            self._current_note_data = {
                'title': note.get('title', ''),
                'content': note.get('content', ''),
                'content_json': note.get('content_json', '')
            }
            self._pending_title = None
            self._pending_content = None
            self._pending_json = None
            self.notesChanged.emit()
            self.filteredNotesChanged.emit()
            self.saveStatusChanged.emit()
            return True
        return False
    
    @pyqtSlot(str, result=bool)
    def togglePinned(self, note_id: str) -> bool:
        """Toggle pinned status for a note."""
        note = self._note_service.get_by_id(note_id)
        if not note:
            return False

        current_pinned = note.get('is_pinned', 0) == 1
        new_pinned = not current_pinned

        if self._note_service.set_pinned(note_id, new_pinned):
            self.notesChanged.emit()
            self.filteredNotesChanged.emit()
            return True
        return False
    
    @pyqtSlot(str, result=bool)
    def isNotePinned(self, note_id: str) -> bool:
        """Check if a note is pinned."""
        note = self._note_service.get_by_id(note_id)
        if note:
            return note.get('is_pinned', 0) == 1
        return False
    
    @pyqtSlot(str, result=int)
    def getNoteCountForFolder(self, folder_id: str) -> int:
        """Get note count for a specific folder."""
        if folder_id == self.SMART_ALL:
            return len(self._note_service.get_all())
        if folder_id == self.SMART_FAVORITES:
            return len(self._note_service.get_pinned())
        return len(self._note_service.get_all(folder_id=folder_id))
    
    @pyqtSlot(result=int)
    def getTotalNoteCount(self) -> int:
        """Get total note count."""
        return len(self._note_service.get_all())
    
    @pyqtSlot(str, result=str)
    def getPreviewText(self, note_id: str) -> str:
        """Get preview text for a note."""
        note = self._note_service.get_by_id(note_id)
        if note:
            return self._note_service.get_preview_text(note.get('content', ''), max_length=80)
        return ""
    
    @pyqtSlot(str, result=str)
    def formatDate(self, iso_date: str) -> str:
        """Format ISO date for display."""
        if not iso_date:
            return ""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_date)
            return dt.strftime("%Y.%m.%d %H:%M")
        except:
            return iso_date

    @pyqtSlot(str, result=str)
    def getFolderPathForNote(self, note_id: str) -> str:
        """Get folder path for a note (e.g., 'Folder1/SubFolder')."""
        if not note_id or not self._note_service:
            return ""

        note = self._note_service.get_by_id(note_id)
        if not note:
            return ""

        folder_id = note.get('folder_id')
        if not folder_id:
            return "미분류"

        # Build path by traversing parent folders
        path_parts = []
        visited = set()  # Prevent infinite loop

        while folder_id and folder_id not in visited:
            visited.add(folder_id)
            folder = self._folder_controller._folder_service.get_by_id(folder_id)
            if not folder:
                break
            path_parts.append(folder.get('name', 'Unnamed'))
            folder_id = folder.get('parent_id')

        if not path_parts:
            return "미분류"

        # Reverse to get root -> leaf order
        path_parts.reverse()
        return " / ".join(path_parts)

    @pyqtSlot(result=bool)
    def hasClipboardImage(self) -> bool:
        """Check if clipboard contains an image."""
        clipboard = QApplication.clipboard()
        if clipboard:
            mime_data = clipboard.mimeData()
            return mime_data and mime_data.hasImage()
        return False
    
    @pyqtSlot(str, result=bool)
    def pasteImageFromClipboard(self, note_id: str) -> bool:
        """Paste image from clipboard into note."""
        if not note_id:
            return False
        
        clipboard = QApplication.clipboard()
        if not clipboard:
            return False
        
        mime_data = clipboard.mimeData()
        if not mime_data or not mime_data.hasImage():
            return False
        
        # Get image from clipboard
        image = clipboard.image()
        if image.isNull():
            return False
        
        # Convert image to data URL so it is stored directly in DB content
        image_data_url = self._image_service.get_image_data_url(image)
        if not image_data_url:
            return False
        
        # Get current note content
        note = self._note_service.get_by_id(note_id)
        if not note:
            return False
        
        # Insert markdown image at end of content
        content = note.get('content', '')
        new_content = self._image_service.insert_image_markdown(
            content, len(content), image_data_url, "이미지"
        )
        
        # Reuse update pipeline (tokenize image payload into note_images table)
        return self.updateNote(note_id, note.get('title', ''), new_content)
    
    @pyqtSlot(str, result=str)
    def getImageDataUrl(self, image_path: str) -> str:
        """Get base64 data URL for an image (for inline preview).
        
        Handles both relative paths (from images directory) and absolute paths (from file picker).
        """
        if not image_path:
            return ""

        # If already data URL, return as-is (DB-stored image format)
        if image_path.startswith("data:image"):
            return image_path
        
        from pathlib import Path
        
        # Check if it's an absolute path or relative path
        path_obj = Path(image_path)
        if path_obj.is_absolute():
            # Absolute path from file picker
            full_path = path_obj
        else:
            # Relative path from images directory
            full_path = self._image_service.images_dir.parent / image_path
            
        if not full_path.exists():
            return ""
        
        image = QImage(str(full_path))
        if image.isNull():
            return ""
        
        return self._image_service.get_image_data_url(image)
    
    @pyqtSlot(str, str, result=str)
    def saveBase64Image(self, note_id: str, base64_data: str) -> str:
        """Normalize base64 image data and return data URL for DB storage."""
        if not note_id or not base64_data:
            return ""
        
        try:
            # Keep DB format as data URL
            if base64_data.startswith("data:image"):
                return base64_data

            # Support raw base64 payloads by normalizing to data URL
            from PyQt6.QtCore import QByteArray
            byte_array = QByteArray.fromBase64(base64_data.encode())
            image = QImage()
            if image.loadFromData(byte_array):
                return self._image_service.get_image_data_url(image)
        except Exception as e:
            print(f"[NoteController] Save base64 image error: {e}")
        
        return ""
    
    @pyqtSlot(str, str, result=str)
    def saveLocalImage(self, note_id: str, file_path: str) -> str:
        """Convert local image file to data URL for DB storage and return it."""
        if not note_id or not file_path:
            return ""
        
        try:
            return self._image_service.load_image_file_as_data_url(file_path)
        except Exception as e:
            print(f"[NoteController] Save local image error: {e}")
        
        return ""
