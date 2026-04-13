"""Folder controller for managing folder operations with SQLite persistence."""
from typing import List, Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QVariant
import uuid

from services.database import Database
from services.folder_service import FolderService


class FolderController(QObject):
    """Controller for folder management with SQLite persistence and QML integration."""
    
    # Signals
    foldersChanged = pyqtSignal()
    currentFolderChanged = pyqtSignal()
    folderAdded = pyqtSignal(str)  # folder_id
    folderRemoved = pyqtSignal(str)  # folder_id
    folderRenamed = pyqtSignal(str, str)  # folder_id, new_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_folder_id: Optional[str] = None
        
        # Initialize database
        self._db = Database()
        self._db.init_schema()
        
        # Initialize service
        self._folder_service = FolderService(self._db)
        
        # Load or create default folders
        self._load_folders()
    
    def _load_folders(self):
        """Load folders from database or create defaults."""
        folders = self._folder_service.get_all()
        
        if not folders:
            # Create default folders
            defaults = [
                ("아리랑", "#3B82F6"),
                ("토토넵", "#F97316"),
                ("디아라", "#FDBA74"),
                ("갈꺼냐", "#FDA4AF"),
                ("여기야", "#F97316"),
            ]
            for name, color in defaults:
                folder_id = str(uuid.uuid4())[:8]
                self._folder_service.create(folder_id, name, color)
            
            folders = self._folder_service.get_all()
        
        # Select first folder by default
        if folders and not self._current_folder_id:
            self._current_folder_id = folders[0]['id']
    
    # Properties
    @pyqtProperty(list, notify=foldersChanged)
    def folders(self):
        """Get all folders as list of dicts for QML."""
        folders = self._folder_service.get_all()
        # Add note count to each folder
        for folder in folders:
            folder['note_count'] = self._folder_service.get_note_count(folder['id'])
        return folders
    
    @pyqtProperty(str, notify=currentFolderChanged)
    def currentFolderId(self) -> str:
        """Get current folder ID."""
        return self._current_folder_id or ""
    
    @currentFolderId.setter
    def currentFolderId(self, folder_id: str):
        """Set current folder ID."""
        if self._current_folder_id != folder_id:
            self._current_folder_id = folder_id
            self.currentFolderChanged.emit()
    
    @pyqtProperty(str, notify=currentFolderChanged)
    def currentFolderName(self) -> str:
        """Get current folder name."""
        if not self._current_folder_id:
            return "모든 노트"
        folder = self._folder_service.get_by_id(self._current_folder_id)
        return folder['name'] if folder else "모든 노트"
    
    # Slots
    @pyqtSlot(str, str, result=str)
    def createFolder(self, name: str, color: str = "#3B82F6") -> str:
        """Create a new folder and return its ID."""
        folder_id = str(uuid.uuid4())[:8]
        
        if self._folder_service.create(folder_id, name, color):
            self.foldersChanged.emit()
            self.folderAdded.emit(folder_id)
            
            # Auto-select the new folder
            self.currentFolderId = folder_id
            return folder_id
        
        return ""
    
    @pyqtSlot(str, result=bool)
    def deleteFolder(self, folder_id: str) -> bool:
        """Delete a folder by ID."""
        if not self._folder_service.exists(folder_id):
            return False
        
        # Delete from database (cascades to notes)
        if self._folder_service.delete(folder_id):
            # Update current folder if deleted
            if self._current_folder_id == folder_id:
                folders = self._folder_service.get_all()
                self._current_folder_id = folders[0]['id'] if folders else None
                self.currentFolderChanged.emit()
            
            self.foldersChanged.emit()
            self.folderRemoved.emit(folder_id)
            return True
        
        return False
    
    @pyqtSlot(str, str, result=bool)
    def renameFolder(self, folder_id: str, new_name: str) -> bool:
        """Rename a folder."""
        if not new_name.strip():
            return False
        
        if self._folder_service.update(folder_id, name=new_name.strip()):
            self.foldersChanged.emit()
            self.folderRenamed.emit(folder_id, new_name)
            return True
        
        return False
    
    @pyqtSlot(str, result=QVariant)
    def getFolder(self, folder_id: str) -> QVariant:
        """Get a single folder by ID."""
        folder = self._folder_service.get_by_id(folder_id)
        if folder:
            folder['note_count'] = self._folder_service.get_note_count(folder_id)
            return QVariant(folder)
        return QVariant()
    
    @pyqtSlot(str, result=bool)
    def selectFolder(self, folder_id: str) -> bool:
        """Select a folder (set as current)."""
        if self._folder_service.exists(folder_id):
            self.currentFolderId = folder_id
            return True
        return False
    
    @pyqtSlot(result=int)
    def getFolderCount(self) -> int:
        """Get total folder count."""
        return len(self._folder_service.get_all())
    
    @pyqtSlot(str, result=int)
    def getNoteCount(self, folder_id: str) -> int:
        """Get note count for a folder."""
        return self._folder_service.get_note_count(folder_id)
    
    # Helper methods
    def get_db(self) -> Database:
        """Get database instance (for NoteController)."""
        return self._db
