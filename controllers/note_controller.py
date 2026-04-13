"""Note controller for managing note operations with SQLite persistence."""
from typing import List, Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QTimer, QVariant
from PyQt6.QtGui import QClipboard, QImage
from PyQt6.QtWidgets import QApplication
import uuid

from services.database import Database
from services.note_service import NoteService
from services.image_service import ImageService


class NoteController(QObject):
    """Controller for note management with SQLite persistence and QML integration."""
    
    # Signals
    notesChanged = pyqtSignal()
    filteredNotesChanged = pyqtSignal()
    noteAdded = pyqtSignal(str)  # note_id
    noteRemoved = pyqtSignal(str)  # note_id
    noteUpdated = pyqtSignal(str)  # note_id
    saveStatusChanged = pyqtSignal()  # For save status updates
    
    def __init__(self, folder_controller, parent=None):
        super().__init__(parent)
        self._folder_controller = folder_controller
        
        # Get database from folder controller
        self._db = folder_controller.get_db()
        self._note_service = NoteService(self._db)
        self._image_service = ImageService()
        
        # Current state
        self._current_note_id: Optional[str] = None
        self._is_dirty: bool = False
        self._is_saving: bool = False
        self._save_status: str = "saved"  # saved, saving, dirty
        
        # Auto-save timer (debounce)
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._perform_auto_save)
        
        # Connect to folder changes
        self._folder_controller.currentFolderChanged.connect(self._on_folder_changed)
        
        # Initialize default notes if needed
        self._initialize_default_notes()
    
    def _initialize_default_notes(self):
        """Initialize with default notes if database is empty."""
        existing_notes = self._note_service.get_all()
        if existing_notes:
            return
        
        # Get first folder for default notes
        folders = self._folder_controller.folders
        if not folders:
            return
        
        folder_id = folders[0]['id'] if folders else None
        if not folder_id:
            return
        
        # Create default notes
        defaults = [
            ("아침 루틴 정리", "매일 아침 6시에 일어나서 물 한 잔 마시기.\n스트레칭 10분 하고 명상하기."),
            ("프로젝트 아이디어", "새로운 노트 앱 UI 디자인 컨셉.\niOS 스타일의 부드러움과 금융 앱의 신뢰감을 결합."),
            ("회의록: 디자인 팀", "GlassCard 컴포넌트 구현 완료.\nSidebarSection 작업 진행중..."),
        ]
        
        for title, content in defaults:
            note_id = str(uuid.uuid4())[:8]
            self._note_service.create(note_id, folder_id, title, content)
        
        self.notesChanged.emit()
        self.filteredNotesChanged.emit()
    
    def _on_folder_changed(self):
        """Handle folder change - emit filtered notes changed."""
        self.filteredNotesChanged.emit()
    
    def _perform_auto_save(self):
        """Perform actual save operation."""
        if not self._is_dirty or not self._current_note_id:
            return
        
        self._is_saving = True
        self._save_status = "saving"
        self.saveStatusChanged.emit()
        
        # Note is already saved via updateNote, just update status
        self._is_dirty = False
        self._is_saving = False
        self._save_status = "saved"
        self.saveStatusChanged.emit()
    
    # Properties
    @pyqtProperty(list, notify=notesChanged)
    def allNotes(self):
        """Get all notes as list of dicts for QML."""
        return self._note_service.get_all()
    
    @pyqtProperty(list, notify=filteredNotesChanged)
    def filteredNotes(self):
        """Get notes filtered by current folder."""
        current_folder_id = self._folder_controller.currentFolderId
        return self._note_service.get_all(folder_id=current_folder_id or None)
    
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
    
    # Slots
    @pyqtSlot(str, str, str, result=str)
    def createNote(self, title: str, content: str = "", folder_id: str = "") -> str:
        """Create a new note in the specified folder."""
        # Use current folder if not specified
        if not folder_id:
            folder_id = self._folder_controller.currentFolderId
        
        if not folder_id:
            return ""
        
        note_id = str(uuid.uuid4())[:8]
        
        if self._note_service.create(note_id, folder_id, title, content):
            self._current_note_id = note_id
            self._is_dirty = False
            self._save_status = "saved"
            
            self.notesChanged.emit()
            self.filteredNotesChanged.emit()
            self.noteAdded.emit(note_id)
            self.saveStatusChanged.emit()
            
            return note_id
        
        return ""
    
    @pyqtSlot(str, result=bool)
    def deleteNote(self, note_id: str) -> bool:
        """Soft delete a note by ID."""
        if self._note_service.soft_delete(note_id):
            if self._current_note_id == note_id:
                self._current_note_id = None
            
            self.notesChanged.emit()
            self.filteredNotesChanged.emit()
            self.noteRemoved.emit(note_id)
            return True
        
        return False
    
    @pyqtSlot(str, str, str, result=bool)
    def updateNote(self, note_id: str, title: str, content: str) -> bool:
        """Update note title and content."""
        if not note_id:
            return False
        
        # Perform immediate update to database
        if self._note_service.update(note_id, title=title, content=content):
            self._current_note_id = note_id
            self._is_dirty = True
            self._save_status = "dirty"
            
            # Emit immediate status change
            self.saveStatusChanged.emit()
            
            # Start auto-save timer (debounce)
            self._auto_save_timer.start(1000)  # 1 second debounce
            
            # Also emit note changes for list update
            self.notesChanged.emit()
            self.filteredNotesChanged.emit()
            self.noteUpdated.emit(note_id)
            
            return True
        
        return False
    
    @pyqtSlot(result=bool)
    def saveCurrentNote(self) -> bool:
        """Force save current note immediately."""
        self._auto_save_timer.stop()
        self._perform_auto_save()
        return True
    
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
        """Get a single note by ID."""
        note = self._note_service.get_by_id(note_id)
        if note:
            return QVariant(note)
        return QVariant()
    
    @pyqtSlot(str, result=bool)
    def selectNote(self, note_id: str) -> bool:
        """Select a note (set as current)."""
        # Save current note if dirty before switching
        if self._is_dirty and self._current_note_id and self._current_note_id != note_id:
            self.saveCurrentNote()
        
        note = self._note_service.get_by_id(note_id)
        if note:
            self._current_note_id = note_id
            self._is_dirty = False
            self._save_status = "saved"
            self.notesChanged.emit()
            self.saveStatusChanged.emit()
            return True
        return False
    
    @pyqtSlot(str, result=int)
    def getNoteCountForFolder(self, folder_id: str) -> int:
        """Get note count for a specific folder."""
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
        
        # Save image
        image_path = self._image_service.save_clipboard_image(image, note_id)
        if not image_path:
            return False
        
        # Get current note content
        note = self._note_service.get_by_id(note_id)
        if not note:
            return False
        
        # Insert markdown image at end of content
        content = note.get('content', '')
        new_content = self._image_service.insert_image_markdown(
            content, len(content), image_path, "이미지"
        )
        
        # Update note with new content
        if self._note_service.update(note_id, content=new_content):
            self._current_note_id = note_id
            self._is_dirty = False
            self._save_status = "saved"
            
            self.notesChanged.emit()
            self.filteredNotesChanged.emit()
            self.noteUpdated.emit(note_id)
            self.saveStatusChanged.emit()
            
            return True
        
        return False
    
    @pyqtSlot(str, result=str)
    def getImageDataUrl(self, image_path: str) -> str:
        """Get base64 data URL for an image (for inline preview).
        
        Handles both relative paths (from images directory) and absolute paths (from file picker).
        """
        if not image_path:
            return ""
        
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
        """Save base64 image data and return the file path."""
        if not note_id or not base64_data:
            return ""
        
        try:
            # Parse base64 data
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]
            
            # Decode base64
            from PyQt6.QtCore import QByteArray
            byte_array = QByteArray.fromBase64(base64_data.encode())
            
            # Create QImage from data
            image = QImage()
            if image.loadFromData(byte_array):
                # Save image
                image_path = self._image_service.save_clipboard_image(image, note_id)
                return image_path if image_path else ""
        except Exception as e:
            print(f"[NoteController] Save base64 image error: {e}")
        
        return ""
    
    @pyqtSlot(str, str, result=str)
    def saveLocalImage(self, note_id: str, file_path: str) -> str:
        """Save a local image file to note storage and return the relative path."""
        if not note_id or not file_path:
            return ""
        
        try:
            from pathlib import Path
            
            # Load image from file path
            path_obj = Path(file_path)
            if not path_obj.exists():
                return ""
            
            image = QImage(str(path_obj))
            if image.isNull():
                return ""
            
            # Save to note storage
            image_path = self._image_service.save_clipboard_image(image, note_id)
            return image_path if image_path else ""
        except Exception as e:
            print(f"[NoteController] Save local image error: {e}")
        
        return ""
