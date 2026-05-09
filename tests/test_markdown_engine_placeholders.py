import unittest

import packages.markdown_engine
import packages.markdown_engine.normalizer as normalizer


class MarkdownEnginePlaceholdersTest(unittest.TestCase):
    def test_markdown_engine_imports(self):
        self.assertIsNotNone(packages.markdown_engine)
        self.assertIsNotNone(normalizer)

    def test_normalizer_is_placeholder_only(self):
        self.assertEqual(getattr(normalizer, "__all__", None), [])
        self.assertFalse(hasattr(normalizer, "normalize_markdown"))
        self.assertIn("Placeholder", normalizer.__doc__ or "")


if __name__ == "__main__":
    unittest.main()
