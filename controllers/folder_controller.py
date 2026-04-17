"""Folder controller for managing folder operations with SQLite persistence."""
from typing import List, Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QVariant
import uuid

from services.database import Database
from services.folder_service import FolderService
from services.library_service import LibraryService


class FolderController(QObject):
    """Controller for folder management with SQLite persistence and QML integration."""

    SMART_FOLDER_PREFIX = "smart:"
    SMART_FOLDERS = [
        {"id": "smart:all", "name": "전체 노트", "color": "#64748B"},
        {"id": "smart:favorites", "name": "즐겨 찾기", "color": "#F59E0B"},
    ]
    
    # Signals
    foldersChanged = pyqtSignal()
    currentFolderChanged = pyqtSignal()
    folderAdded = pyqtSignal(str)  # folder_id
    folderRemoved = pyqtSignal(str)  # folder_id
    folderRenamed = pyqtSignal(str, str)  # folder_id, new_name
    libraryChanged = pyqtSignal()  # Emitted when library changes
    
    def __init__(self, library_service: LibraryService, parent=None):
        super().__init__(parent)
        self._current_folder_id: Optional[str] = None
        self._library_service = library_service
        self._collapsed_folder_ids: set = set()  # Track collapsed (hidden) folders
        
        # Connect to library changes
        self._library_service.currentLibraryChanged.connect(self._on_library_changed)

        # Initialize with current library
        self._on_library_changed()
    
    def _on_library_changed(self):
        """Handle library change - reload folders from new database."""
        db = self._library_service.get_current_database()
        if db:
            self._db = db
            self._folder_service = FolderService(self._db)
            self._current_folder_id = None
            self._load_folders()
            self.libraryChanged.emit()
            self.foldersChanged.emit()
            self.currentFolderChanged.emit()
        
    def _get_db(self) -> Database:
        """Get current database, refreshing if needed."""
        db = self._library_service.get_current_database()
        if db:
            return db
        return self._db  # Fallback
    
    def get_db(self) -> Database:
        """Get current database for other controllers."""
        return self._get_db()
    
    def _load_folders(self):
        """Load folders from database."""
        folders = self._folder_service.get_all()
        
        # Select first folder by default if any exist
        if folders and not self._current_folder_id:
            self._current_folder_id = folders[0]['id']

    def _is_smart_folder_id(self, folder_id: Optional[str]) -> bool:
        return bool(folder_id) and folder_id.startswith(self.SMART_FOLDER_PREFIX)
    
    def _get_folder_depth(self, folder_id: str, folders_map: dict, cache: dict = None) -> int:
        """Calculate depth of folder in hierarchy (0 = root)."""
        if cache is None:
            cache = {}
        if folder_id in cache:
            return cache[folder_id]

        folder = folders_map.get(folder_id)
        if not folder:
            return 0

        parent_id = folder.get('parent_id')
        if not parent_id:
            cache[folder_id] = 0
            return 0

        depth = 1 + self._get_folder_depth(parent_id, folders_map, cache)
        cache[folder_id] = depth
        return depth

    # Properties
    @pyqtProperty(list, notify=foldersChanged)
    def folders(self):
        """Get all folders as list of dicts for QML with hierarchy info."""
        folders = self._folder_service.get_all()

        # Build id -> folder map for depth calculation
        folders_map = {f['id']: f for f in folders}
        depth_cache = {}

        # Add note count and depth to each folder
        for folder in folders:
            folder['note_count'] = self._folder_service.get_note_count(folder['id'])
            folder['depth'] = self._get_folder_depth(folder['id'], folders_map, depth_cache)
            folder['has_children'] = any(f.get('parent_id') == folder['id'] for f in folders)

        # Build tree and traverse in pre-order (parent -> children -> grandchildren)
        def sort_key(f):
            return (f.get('sort_order', 0), f.get('created_at', ''))
        
        # Group children by parent_id
        children_map = {}
        roots = []
        for f in folders:
            parent_id = f.get('parent_id')
            if parent_id:
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(f)
            else:
                roots.append(f)
        
        # Pre-order traversal: parent first, then children recursively
        # Skip children of collapsed folders
        sorted_folders = []
        def traverse(folder_list):
            for f in sorted(folder_list, key=sort_key):
                sorted_folders.append(f)
                # Only traverse children if folder is not collapsed
                if f['id'] not in self._collapsed_folder_ids:
                    children = children_map.get(f['id'], [])
                    traverse(children)
        
        traverse(roots)

        smart_folders = []
        for smart in self.SMART_FOLDERS:
            smart_folders.append({
                "id": smart["id"],
                "name": smart["name"],
                "color": smart["color"],
                "note_count": 0,
                "depth": 0,
                "has_children": False,
                "parent_id": None,
                "is_smart": True,
            })

        return smart_folders + sorted_folders
    
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
        if self._is_smart_folder_id(self._current_folder_id):
            for smart in self.SMART_FOLDERS:
                if smart["id"] == self._current_folder_id:
                    return smart["name"]
            return "스마트 폴더"
        folder = self._folder_service.get_by_id(self._current_folder_id)
        return folder['name'] if folder else "모든 노트"
    
    # Slots
    @pyqtSlot(str, str, str, result=str)
    def createFolder(self, name: str, color: str = "#3B82F6", parent_id: str = "") -> str:
        """Create a new folder and return its ID. Max depth is 2 (root + child only)."""
        folder_id = str(uuid.uuid4())[:8]
        
        # Empty string means None (root level)
        actual_parent_id = parent_id if parent_id else None

        # Check depth limit: max depth is 3 (0=root, 1=child, 2=grandchild)
        if actual_parent_id:
            folders = self._folder_service.get_all()
            folders_map = {f['id']: f for f in folders}
            parent_depth = self._get_folder_depth(actual_parent_id, folders_map)
            if parent_depth >= 2:  # Parent is already at depth 2, child would be depth 3 - not allowed
                return ""

        if self._folder_service.create(folder_id, name, color, actual_parent_id):
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
        result = self._folder_service.delete(folder_id)
        if result:
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

        result = self._folder_service.update(folder_id, name=new_name.strip())
        if result:
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
        if self._is_smart_folder_id(folder_id):
            self.currentFolderId = folder_id
            return True
        if self._folder_service.exists(folder_id):
            self.currentFolderId = folder_id
            return True
        return False

    @pyqtSlot(str, result=bool)
    def isSmartFolder(self, folder_id: str) -> bool:
        """Check if folder ID is a built-in smart folder."""
        return self._is_smart_folder_id(folder_id)

    @pyqtSlot(result=str)
    def getFirstRegularFolderId(self) -> str:
        """Get first regular (DB) folder id for note creation fallback."""
        folders = self._folder_service.get_all()
        if folders:
            return folders[0]["id"]
        return ""
    
    @pyqtSlot(result=int)
    def getFolderCount(self) -> int:
        """Get total folder count."""
        return len(self._folder_service.get_all())
    
    @pyqtSlot(str, result=int)
    def getNoteCount(self, folder_id: str) -> int:
        """Get note count for a folder."""
        return self._folder_service.get_note_count(folder_id)
    
    @pyqtSlot(str, result=bool)
    def isFolderCollapsed(self, folder_id: str) -> bool:
        """Check if a folder is collapsed (children hidden)."""
        return folder_id in self._collapsed_folder_ids
    
    @pyqtSlot(str)
    def toggleFolderExpanded(self, folder_id: str):
        """Toggle folder expanded/collapsed state."""
        if folder_id in self._collapsed_folder_ids:
            self._collapsed_folder_ids.discard(folder_id)
        else:
            self._collapsed_folder_ids.add(folder_id)
        self.foldersChanged.emit()
    
    # Helper methods
    def get_db(self) -> Database:
        """Get database instance (for NoteController)."""
        return self._db
