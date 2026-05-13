from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_BOOTSTRAP_SOURCE = ROOT_DIR / "app_bootstrap.py"
CONTEXT_DOC_SOURCE = ROOT_DIR / "packages" / "editor_ui" / "context_properties.md"


class AppBootstrapContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP_BOOTSTRAP_SOURCE.read_text(encoding="utf-8")
        cls.context_docs = CONTEXT_DOC_SOURCE.read_text(encoding="utf-8")

    def test_context_property_names_are_still_in_source(self):
        expected_names = [
            "libraryService",
            "folderController",
            "noteController",
            "templateController",
            "currentExportController",
            "folderImportController",
            "appBrand",
            "appName",
            "appLogoPath",
            "folderControllerReady",
        ]

        for name in expected_names:
            with self.subTest(context_property=name):
                self.assertIn(f'setContextProperty("{name}"', self.source)
                self.assertIn(name, self.context_docs)

    def test_settings_service_is_constructed_and_qml_context_property(self):
        self.assertIn("settings_service = SettingsService()", self.source)
        self.assertIn('setContextProperty("settingsService"', self.source)
        self.assertIn("settingsService", self.context_docs)

    def test_qml_import_path_setup_is_present(self):
        self.assertIn("engine.addImportPath", self.source)
        self.assertIn("config.qml_import_path", self.source)


if __name__ == "__main__":
    unittest.main()
