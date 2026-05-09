import importlib
import unittest


class PackageImportsTest(unittest.TestCase):
    def test_boundary_packages_import(self):
        package_names = [
            "packages.storage",
            "packages.import_export",
            "packages.markdown_engine",
            "packages.editor_ui",
            "packages.editor_core",
            "packages.plugin_api",
        ]

        for package_name in package_names:
            with self.subTest(package=package_name):
                module = importlib.import_module(package_name)
                self.assertIsNotNone(module)


if __name__ == "__main__":
    unittest.main()
