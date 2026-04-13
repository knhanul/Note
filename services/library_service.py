"""Library service for managing multiple database files per library."""
import sqlite3
import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty

from services.database import Database


class LibraryService(QObject):
    """Manages multiple libraries, each with its own SQLite database."""
    
    # Signals
    currentLibraryChanged = pyqtSignal()
    librariesChanged = pyqtSignal()
    libraryAdded = pyqtSignal(str)  # library_id
    libraryRemoved = pyqtSignal(str)  # library_id
    libraryRenamed = pyqtSignal(str, str)  # library_id, new_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Program directory (where the main script is located)
        prog_dir = Path(__file__).parent.parent
        
        # Main database for storing library metadata (in program directory)
        self._meta_db = Database(str(prog_dir / "nuni_note.db"))
        self._meta_db.init_schema()
        self._init_libraries_table()
        
        # Libraries directory (in program directory)
        self._libraries_dir = prog_dir / "libraries"
        self._libraries_dir.mkdir(exist_ok=True)
        
        # Current library
        self._current_library_id: Optional[str] = None
        self._current_db: Optional[Database] = None
        
        # Load default library or create one
        self._ensure_default_library()
    
    def _init_libraries_table(self):
        """Initialize libraries metadata table."""
        conn = self._meta_db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS libraries (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                db_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_default INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
    
    def _ensure_default_library(self):
        """Create or load default library."""
        libraries = self.get_all_libraries()
        
        if not libraries:
            # Create default library
            self.create_library("내 서재", "기본 서재입니다", is_default=True)
        else:
            # Find default library
            default = next((lib for lib in libraries if lib.get('is_default')), None)
            if default:
                self.set_current_library(default['id'])
            else:
                self.set_current_library(libraries[0]['id'])
    
    def get_all_libraries(self) -> List[Dict[str, Any]]:
        """Get all libraries."""
        return self._meta_db.fetch_all(
            "SELECT * FROM libraries ORDER BY created_at ASC"
        )
    
    def get_library(self, library_id: str) -> Optional[Dict[str, Any]]:
        """Get library by ID."""
        return self._meta_db.fetch_one(
            "SELECT * FROM libraries WHERE id = ?", (library_id,)
        )
    
    def create_library(self, name: str, description: str = "", is_default: bool = False) -> str:
        """Create a new library with its own database."""
        library_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        
        # Database file path
        db_filename = f"{library_id}.db"
        db_path = str(self._libraries_dir / db_filename)
        
        # Insert into metadata table
        self._meta_db.execute(
            """INSERT INTO libraries (id, name, description, db_path, created_at, updated_at, is_default)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (library_id, name, description, db_path, now, now, 1 if is_default else 0)
        )
        self._meta_db.commit()
        
        # Create and initialize the library database
        lib_db = Database(db_path)
        lib_db.init_schema()
        lib_db.close()
        
        # Create images directory for this library
        images_dir = self._libraries_dir / f"{library_id}_images"
        images_dir.mkdir(exist_ok=True)
        
        self.librariesChanged.emit()
        self.libraryAdded.emit(library_id)
        
        # Set as current if it's the first one or default
        if is_default or not self._current_library_id:
            self.set_current_library(library_id)
        
        return library_id
    
    def delete_library(self, library_id: str) -> bool:
        """Delete a library and its database file."""
        library = self.get_library(library_id)
        if not library:
            return False
        
        # Don't allow deleting the last library
        libraries = self.get_all_libraries()
        if len(libraries) <= 1:
            return False
        
        # Remove from metadata
        self._meta_db.execute("DELETE FROM libraries WHERE id = ?", (library_id,))
        self._meta_db.commit()
        
        # Delete database file
        try:
            db_path = Path(library['db_path'])
            if db_path.exists():
                db_path.unlink()
        except Exception as e:
            print(f"[LibraryService] Error deleting DB file: {e}")
        
        # Delete images directory
        try:
            images_dir = self._libraries_dir / f"{library_id}_images"
            if images_dir.exists():
                import shutil
                shutil.rmtree(images_dir)
        except Exception as e:
            print(f"[LibraryService] Error deleting images dir: {e}")
        
        # If this was the current library, switch to another one
        if self._current_library_id == library_id:
            remaining = self.get_all_libraries()
            if remaining:
                self.set_current_library(remaining[0]['id'])
            else:
                self._current_library_id = None
                self._current_db = None
        
        self.librariesChanged.emit()
        self.libraryRemoved.emit(library_id)
        return True
    
    def rename_library(self, library_id: str, new_name: str) -> bool:
        """Rename a library."""
        if not new_name.strip():
            return False
        
        now = datetime.now().isoformat()
        self._meta_db.execute(
            "UPDATE libraries SET name = ?, updated_at = ? WHERE id = ?",
            (new_name.strip(), now, library_id)
        )
        self._meta_db.commit()
        
        self.librariesChanged.emit()
        self.libraryRenamed.emit(library_id, new_name)
        return True
    
    def set_current_library(self, library_id: str) -> bool:
        """Set the current active library."""
        library = self.get_library(library_id)
        if not library:
            return False
        
        # Close previous connection if any
        if self._current_db:
            self._current_db.close()
        
        # Open new database connection
        self._current_db = Database(library['db_path'])
        self._current_db.init_schema()
        self._current_library_id = library_id
        
        print(f"[LibraryService] Switched to library: {library['name']} ({library_id})")
        self.currentLibraryChanged.emit()
        return True
    
    @pyqtProperty(str, notify=currentLibraryChanged)
    def currentLibraryId(self) -> str:
        """Get current library ID."""
        return self._current_library_id or ""
    
    @pyqtProperty(str, notify=currentLibraryChanged)
    def currentLibraryName(self) -> str:
        """Get current library name."""
        if not self._current_library_id:
            return ""
        library = self.get_library(self._current_library_id)
        return library['name'] if library else ""
    
    def get_current_database(self) -> Optional[Database]:
        """Get the database instance for the current library."""
        return self._current_db
    
    def get_library_images_dir(self, library_id: str) -> Path:
        """Get the images directory path for a library."""
        return self._libraries_dir / f"{library_id}_images"
    
    @pyqtSlot(str, result=str)
    def createLibrary(self, name: str, description: str = "") -> str:
        """QML accessible: Create a new library."""
        return self.create_library(name, description)
    
    @pyqtSlot(str, result=bool)
    def deleteLibrary(self, library_id: str) -> bool:
        """QML accessible: Delete a library."""
        return self.delete_library(library_id)
    
    @pyqtSlot(str, str, result=bool)
    def renameLibrary(self, library_id: str, new_name: str) -> bool:
        """QML accessible: Rename a library."""
        return self.rename_library(library_id, new_name)
    
    @pyqtSlot(str, result=bool)
    def setCurrentLibrary(self, library_id: str) -> bool:
        """QML accessible: Set current library."""
        return self.set_current_library(library_id)
    
    @pyqtSlot(result=list)
    def getAllLibraries(self) -> List[Dict[str, Any]]:
        """QML accessible: Get all libraries."""
        return self.get_all_libraries()
