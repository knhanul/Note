"""Folder controller for managing folder operations."""
from typing import List, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot

from models.folder import Folder


class FolderController(QObject):
    """Controller for folder management with QML integration."""
    
    # Signals
    foldersChanged = pyqtSignal()
    currentFolderChanged = pyqtSignal()
    folderAdded = pyqtSignal(str)  # folder_id
    folderRemoved = pyqtSignal(str)  # folder_id
    folderRenamed = pyqtSignal(str, str)  # folder_id, new_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._folders: List[Folder] = []
        self._current_folder_id: Optional[str] = None
        self._initialize_default_folders()
    
    def _initialize_default_folders(self):
        """Initialize with some default folders."""
        default_folders = [
            Folder(name="아리랑", color="#3B82F6"),
            Folder(name="토토넵", color="#F97316"),
            Folder(name="디아라", color="#FDBA74"),
            Folder(name="갈꺼냐", color="#FDA4AF"),
            Folder(name="여기야", color="#F97316"),
        ]
        for folder in default_folders:
            self._folders.append(folder)
        
        # Select first folder by default
        if self._folders:
            self._current_folder_id = self._folders[0].id
    
    # Properties
    @pyqtProperty(list, notify=foldersChanged)
    def folders(self):
        """Get all folders as list of dicts for QML."""
        result = []
        for f in self._folders:
            result.append(f.to_dict())
        return result
    
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
    
    # Slots
    @pyqtSlot(str, str, result=str)
    def createFolder(self, name: str, color: str = "#3B82F6") -> str:
        """Create a new folder and return its ID."""
        folder = Folder(name=name, color=color)
        self._folders.append(folder)
        self.foldersChanged.emit()
        self.folderAdded.emit(folder.id)
        
        # Auto-select the new folder
        self.currentFolderId = folder.id
        return folder.id
    
    @pyqtSlot(str, result=bool)
    def deleteFolder(self, folder_id: str) -> bool:
        """Delete a folder by ID. Notes in this folder move to no folder."""
        folder = self._get_folder_by_id(folder_id)
        if not folder:
            return False
        
        # Remove folder
        self._folders = [f for f in self._folders if f.id != folder_id]
        
        # Update current folder if deleted
        if self._current_folder_id == folder_id:
            self._current_folder_id = self._folders[0].id if self._folders else None
            self.currentFolderChanged.emit()
        
        self.foldersChanged.emit()
        self.folderRemoved.emit(folder_id)
        return True
    
    @pyqtSlot(str, str, result=bool)
    def renameFolder(self, folder_id: str, new_name: str) -> bool:
        """Rename a folder."""
        folder = self._get_folder_by_id(folder_id)
        if not folder or not new_name.strip():
            return False
        
        folder.update_name(new_name.strip())
        self.foldersChanged.emit()
        self.folderRenamed.emit(folder_id, new_name)
        return True
    
    @pyqtSlot(str, result=dict)
    def getFolder(self, folder_id: str) -> Optional[dict]:
        """Get a single folder by ID."""
        folder = self._get_folder_by_id(folder_id)
        return folder.to_dict() if folder else None
    
    @pyqtSlot(str, result=bool)
    def selectFolder(self, folder_id: str) -> bool:
        """Select a folder (set as current)."""
        folder = self._get_folder_by_id(folder_id)
        if folder:
            self.currentFolderId = folder_id
            return True
        return False
    
    @pyqtSlot(result=int)
    def getFolderCount(self) -> int:
        """Get total folder count."""
        return len(self._folders)
    
    # Helper methods
    def _get_folder_by_id(self, folder_id: str) -> Optional[Folder]:
        """Get folder object by ID."""
        for folder in self._folders:
            if folder.id == folder_id:
                return folder
        return None
    
    def updateNoteCount(self, folder_id: str, count: int):
        """Update note count for a folder (called by NoteController)."""
        folder = self._get_folder_by_id(folder_id)
        if folder:
            folder.note_count = count
            self.foldersChanged.emit()
