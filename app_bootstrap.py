import sys
from dataclasses import dataclass

from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlApplicationEngine

from app_config import AppConfig
from controllers.current_export_controller import CurrentExportController
from controllers.folder_controller import FolderController
from controllers.folder_import_controller import FolderImportController
from controllers.note_controller import NoteController
from controllers.template_controller import TemplateController
from packages.storage.library_repository import LibraryService
from packages.storage.settings_repository import SettingsService


@dataclass
class AppServices:
    settings_service: SettingsService
    library_service: LibraryService
    folder_controller: FolderController
    note_controller: NoteController
    template_controller: TemplateController
    current_export_controller: CurrentExportController
    folder_import_controller: FolderImportController


def create_services(engine: QQmlApplicationEngine) -> AppServices:
    settings_service = SettingsService()
    library_service = LibraryService(engine, settings_service)
    folder_controller = FolderController(library_service, settings_service, engine)
    note_controller = NoteController(library_service, folder_controller, engine)
    template_controller = TemplateController(library_service, folder_controller, engine)
    current_export_controller = CurrentExportController(library_service, engine)
    folder_import_controller = FolderImportController(
        library_service, folder_controller, note_controller, engine
    )

    return AppServices(
        settings_service=settings_service,
        library_service=library_service,
        folder_controller=folder_controller,
        note_controller=note_controller,
        template_controller=template_controller,
        current_export_controller=current_export_controller,
        folder_import_controller=folder_import_controller,
    )


def configure_qml_engine(engine: QQmlApplicationEngine, config: AppConfig, services: AppServices) -> None:
    engine.addImportPath(str(config.qml_import_path))

    engine.rootContext().setContextProperty("libraryService", services.library_service)
    engine.rootContext().setContextProperty("folderController", services.folder_controller)
    engine.rootContext().setContextProperty("noteController", services.note_controller)
    engine.rootContext().setContextProperty("templateController", services.template_controller)
    engine.rootContext().setContextProperty("currentExportController", services.current_export_controller)
    engine.rootContext().setContextProperty("folderImportController", services.folder_import_controller)

    engine.rootContext().setContextProperty("appBrand", config.brand)
    engine.rootContext().setContextProperty("appName", config.app_name)
    engine.rootContext().setContextProperty("appLogoPath", config.logo_path)

    engine.rootContext().setContextProperty("folderControllerReady", True)


def load_main_qml(engine: QQmlApplicationEngine, config: AppConfig) -> None:
    if not config.main_qml_path.exists():
        sys.exit(1)

    engine.load(QUrl.fromLocalFile(str(config.main_qml_path)))

    if not engine.rootObjects():
        sys.exit(1)


def bootstrap_app(engine: QQmlApplicationEngine, config: AppConfig) -> AppServices:
    services = create_services(engine)
    configure_qml_engine(engine, config, services)
    load_main_qml(engine, config)
    return services
