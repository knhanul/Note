"""Note controller for managing note operations."""
from typing import List, Optional, Callable
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot

from models.note import Note


class NoteController(QObject):
    """Controller for note management with QML integration."""
    
    # Signals
    notesChanged = pyqtSignal()
    filteredNotesChanged = pyqtSignal()
    noteAdded = pyqtSignal(str)  # note_id
    noteRemoved = pyqtSignal(str)  # note_id
    noteUpdated = pyqtSignal(str)  # note_id
    
    def __init__(self, folder_controller, parent=None):
        super().__init__(parent)
        self._folder_controller = folder_controller
        self._notes: List[Note] = []
        self._initialize_default_notes()
        
        # Connect to folder changes
        self._folder_controller.currentFolderChanged.connect(self._on_folder_changed)
    
    def _initialize_default_notes(self):
        """Initialize with some default notes."""
        folders = self._folder_controller._folders if hasattr(self._folder_controller, '_folders') else []
        
        default_notes = [
            Note(title="아침 루틴 정리", content="매일 아침 6시에 일어나서 물 한 잔 마시기.\n스트레칭 10분 하고 명상하기.", 
                 folder_id=folders[0].id if len(folders) > 0 else None, is_pinned=True,
                 tags=["루틴", "건강"]),
            Note(title="프로젝트 아이디어", content="새로운 노트 앱 UI 디자인 컨셉.\niOS 스타일의 부드러움과 금융 앱의 신뢰감을 결합.",
                 folder_id=folders[0].id if len(folders) > 0 else None, is_pinned=True,
                 tags=["아이디어", "디자인"]),
            Note(title="회의록: 디자인 팀", content="GlassCard 컴포넌트 구현 완료.\nSidebarSection 작업 진행중...",
                 folder_id=folders[1].id if len(folders) > 1 else None,
                 tags=["업무", "회의록"]),
            Note(title="주말 계획", content="토요일: 친구와 브런치, 영화관.\n일요일: 집에서 휴식...",
                 folder_id=folders[1].id if len(folders) > 1 else None,
                 tags=["일상"]),
            Note(title="독서 노트: Atomic Habits", content="작은 습관의 힘이 누적되어 큰 변화를 만든다.\n1% 매일 개선하면 1년 후 37배 성장.",
                 folder_id=folders[2].id if len(folders) > 2 else None,
                 tags=["독서", "자기계발"]),
        ]
        for note in default_notes:
            self._notes.append(note)
        
        self._update_folder_note_counts()
    
    def _on_folder_changed(self):
        """Handle folder change - emit filtered notes changed."""
        self.filteredNotesChanged.emit()
    
    def _update_folder_note_counts(self):
        """Update note counts for all folders."""
        if not hasattr(self._folder_controller, '_folders'):
            return
            
        for folder in self._folder_controller._folders:
            count = len([n for n in self._notes if n.folder_id == folder.id])
            self._folder_controller.updateNoteCount(folder.id, count)
    
    # Properties
    @pyqtProperty(list, notify=notesChanged)
    def allNotes(self) -> List[dict]:
        """Get all notes as list of dicts for QML."""
        return [n.to_dict() for n in self._notes]
    
    @pyqtProperty(list, notify=filteredNotesChanged)
    def filteredNotes(self) -> List[dict]:
        """Get notes filtered by current folder."""
        current_folder_id = self._folder_controller.currentFolderId
        if not current_folder_id:
            return [n.to_dict() for n in self._notes]
        
        filtered = [n for n in self._notes if n.folder_id == current_folder_id]
        return [n.to_dict() for n in filtered]
    
    @pyqtProperty(str, notify=filteredNotesChanged)
    def currentFolderName(self) -> str:
        """Get current folder name for display."""
        folder = self._folder_controller.getFolder(self._folder_controller.currentFolderId)
        return folder.get('name', '모든 노트') if folder else '모든 노트'
    
    # Slots
    @pyqtSlot(str, str, str, result=str)
    def createNote(self, title: str, content: str = "", folder_id: str = "") -> str:
        """Create a new note in the specified folder."""
        # Use current folder if not specified
        if not folder_id:
            folder_id = self._folder_controller.currentFolderId
        
        note = Note(title=title, content=content, folder_id=folder_id or None)
        self._notes.append(note)
        
        self.notesChanged.emit()
        self.filteredNotesChanged.emit()
        self.noteAdded.emit(note.id)
        self._update_folder_note_counts()
        
        return note.id
    
    @pyqtSlot(str, result=bool)
    def deleteNote(self, note_id: str) -> bool:
        """Delete a note by ID."""
        note = self._get_note_by_id(note_id)
        if not note:
            return False
        
        self._notes = [n for n in self._notes if n.id != note_id]
        
        self.notesChanged.emit()
        self.filteredNotesChanged.emit()
        self.noteRemoved.emit(note_id)
        self._update_folder_note_counts()
        return True
    
    @pyqtSlot(str, str, str, result=bool)
    def updateNote(self, note_id: str, title: str, content: str) -> bool:
        """Update note title and content."""
        note = self._get_note_by_id(note_id)
        if not note:
            return False
        
        note.update_content(title, content)
        
        self.notesChanged.emit()
        self.filteredNotesChanged.emit()
        self.noteUpdated.emit(note_id)
        return True
    
    @pyqtSlot(str, str, result=bool)
    def moveNoteToFolder(self, note_id: str, folder_id: str) -> bool:
        """Move a note to a different folder."""
        note = self._get_note_by_id(note_id)
        if not note:
            return False
        
        note.move_to_folder(folder_id or None)
        
        self.notesChanged.emit()
        self.filteredNotesChanged.emit()
        self._update_folder_note_counts()
        return True
    
    @pyqtSlot(str, result=dict)
    def getNote(self, note_id: str) -> Optional[dict]:
        """Get a single note by ID."""
        note = self._get_note_by_id(note_id)
        return note.to_dict() if note else None
    
    @pyqtSlot(str, result=int)
    def getNoteCountForFolder(self, folder_id: str) -> int:
        """Get note count for a specific folder."""
        return len([n for n in self._notes if n.folder_id == folder_id])
    
    @pyqtSlot(result=int)
    def getTotalNoteCount(self) -> int:
        """Get total note count."""
        return len(self._notes)
    
    # Helper methods
    def _get_note_by_id(self, note_id: str) -> Optional[Note]:
        """Get note object by ID."""
        for note in self._notes:
            if note.id == note_id:
                return note
        return None
    
    def get_notes_for_folder(self, folder_id: str) -> List[Note]:
        """Get all notes for a specific folder."""
        return [n for n in self._notes if n.folder_id == folder_id]
