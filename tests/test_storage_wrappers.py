import unittest

from packages.storage.database import Database as WrappedDatabase
from packages.storage.folder_repository import FolderRepository, FolderService as WrappedFolderService
from packages.storage.library_repository import LibraryRepository, LibraryService as WrappedLibraryService
from packages.storage.note_repository import NoteRepository, NoteService as WrappedNoteService
from packages.storage.settings_repository import SettingsRepository, SettingsService as WrappedSettingsService
from services.database import Database
from services.folder_service import FolderService
from services.library_service import LibraryService
from services.note_service import NoteService
from services.settings_service import SettingsService


class StorageWrappersTest(unittest.TestCase):
    def test_database_wrapper_reexports_service_class(self):
        self.assertIs(WrappedDatabase, Database)

    def test_note_repository_alias_reexports_note_service(self):
        self.assertIs(NoteRepository, NoteService)
        self.assertIs(WrappedNoteService, NoteService)

    def test_folder_repository_alias_reexports_folder_service(self):
        self.assertIs(FolderRepository, FolderService)
        self.assertIs(WrappedFolderService, FolderService)

    def test_library_repository_alias_reexports_library_service(self):
        self.assertIs(LibraryRepository, LibraryService)
        self.assertIs(WrappedLibraryService, LibraryService)

    def test_settings_repository_alias_reexports_settings_service(self):
        self.assertIs(SettingsRepository, SettingsService)
        self.assertIs(WrappedSettingsService, SettingsService)


if __name__ == "__main__":
    unittest.main()
