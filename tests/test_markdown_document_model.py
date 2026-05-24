import unittest
import tempfile
import os
from pathlib import Path

from services.markdown_document_model import MarkdownDocument, MarkdownMetadata, MarkdownAsset
from services.markdown_front_matter import split_front_matter, serialize_front_matter, parse_markdown_document
from services.markdown_filename_policy import sanitize_filename, dedupe_filename
from services.markdown_asset_resolver import extract_markdown_assets


class TestMarkdownMetadata(unittest.TestCase):
    def test_default_values(self):
        meta = MarkdownMetadata()
        self.assertIsNone(meta.title)
        self.assertEqual(meta.tags, [])
        self.assertIsNone(meta.folder)
        self.assertEqual(meta.extra, {})

    def test_with_values(self):
        meta = MarkdownMetadata(
            title="Test Title",
            tags=["tag1", "tag2"],
            folder="test/folder",
            created_at="2026-05-24",
            extra={"custom": "value"}
        )
        self.assertEqual(meta.title, "Test Title")
        self.assertEqual(meta.tags, ["tag1", "tag2"])
        self.assertEqual(meta.folder, "test/folder")
        self.assertEqual(meta.extra["custom"], "value")


class TestMarkdownAsset(unittest.TestCase):
    def test_default_values(self):
        asset = MarkdownAsset(asset_id="test123", original_ref="test.png")
        self.assertEqual(asset.asset_id, "test123")
        self.assertEqual(asset.original_ref, "test.png")
        self.assertIsNone(asset.resolved_path)
        self.assertEqual(asset.status, "ok")

    def test_status_values(self):
        for status in ["ok", "missing", "invalid", "external", "embedded"]:
            asset = MarkdownAsset(asset_id="test", original_ref="test.png", status=status)
            self.assertEqual(asset.status, status)


class TestSplitFrontMatter(unittest.TestCase):
    def test_no_front_matter(self):
        text = "# Hello\n\nWorld"
        meta, body, warnings = split_front_matter(text)
        self.assertEqual(meta, {})
        self.assertEqual(body, text)
        self.assertEqual(warnings, [])

    def test_yaml_front_matter(self):
        text = """---
title: Test Title
tags: [tag1, tag2]
folder: test/folder
---
# Content here"""
        meta, body, warnings = split_front_matter(text)
        self.assertEqual(meta["title"], "Test Title")
        self.assertEqual(meta["tags"], ["tag1", "tag2"])
        self.assertEqual(meta["folder"], "test/folder")
        self.assertEqual(body.strip(), "# Content here")

    def test_yaml_front_matter_with_extra(self):
        text = """---
title: Test
custom_key: custom_value
---
Content"""
        meta, body, warnings = split_front_matter(text)
        self.assertEqual(meta["title"], "Test")
        self.assertIn("custom_key", meta.get("extra", {}))

    def test_tags_array_format(self):
        text = "---\ntags: [a, b, c]\n---\n"
        meta, body, _ = split_front_matter(text)
        self.assertEqual(meta["tags"], ["a", "b", "c"])

    def test_tags_comma_format(self):
        text = "---\ntags: a, b, c\n---\n"
        meta, body, _ = split_front_matter(text)
        self.assertEqual(meta["tags"], ["a", "b", "c"])

    def test_tags_list_format(self):
        text = """---
tags:
  - a
  - b
  - c
---
"""
        meta, body, _ = split_front_matter(text)
        self.assertEqual(meta["tags"], ["a", "b", "c"])

    def test_toml_front_matter(self):
        text = """+++
title = "TOML Title"
tags = ["t1", "t2"]
+++
# Content"""
        meta, body, _ = split_front_matter(text)
        self.assertEqual(meta["title"], "TOML Title")
        self.assertEqual(meta["tags"], ["t1", "t2"])


class TestSerializeFrontMatter(unittest.TestCase):
    def test_serialize_basic(self):
        meta = MarkdownMetadata(
            title="Test Title",
            tags=["tag1", "tag2"],
            folder="test/folder"
        )
        result = serialize_front_matter(meta)
        self.assertIn("title: Test Title", result)
        self.assertIn("tags: [tag1, tag2]", result)
        self.assertIn("folder: test/folder", result)
        self.assertTrue(result.startswith("---"))

    def test_serialize_empty(self):
        meta = MarkdownMetadata()
        result = serialize_front_matter(meta)
        self.assertIn("---", result)


class TestParseMarkdownDocument(unittest.TestCase):
    def test_parse_with_front_matter(self):
        text = """---
title: My Document
tags: [a, b]
---
# Hello World

This is content."""
        doc = parse_markdown_document(text)
        self.assertEqual(doc.metadata.title, "My Document")
        self.assertEqual(doc.metadata.tags, ["a", "b"])
        self.assertIn("Hello World", doc.body_markdown)

    def test_parse_without_front_matter(self):
        text = "# Just Content\n\nNo front matter here."
        doc = parse_markdown_document(text)
        self.assertIsNone(doc.metadata.title)
        self.assertEqual(doc.body_markdown, text)

    def test_parse_invalid_front_matter_preserves_body(self):
        text = "---\ntitle: test\nno closing\n# Content"
        doc = parse_markdown_document(text)
        self.assertEqual(doc.body_markdown, text)
        self.assertTrue(any("not closed" in w.lower() for w in doc.warnings))


class TestSanitizeFilename(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(sanitize_filename("test.txt"), "test.txt")

    def test_windows_invalid_chars(self):
        self.assertEqual(sanitize_filename('test<>:".txt'), "test____.txt")

    def test_empty_name(self):
        self.assertEqual(sanitize_filename(""), "untitled")
        self.assertEqual(sanitize_filename("   "), "untitled")

    def test_dot_only(self):
        self.assertEqual(sanitize_filename("..."), "untitled")

    def test_korean_preserved(self):
        self.assertEqual(sanitize_filename("문서.txt"), "문서.txt")

    def test_trim_spaces(self):
        self.assertEqual(sanitize_filename("  test  "), "test")

    def test_length_limit(self):
        long_name = "a" * 200
        result = sanitize_filename(long_name)
        self.assertEqual(len(result), 120)


class TestDedupeFilename(unittest.TestCase):
    def test_no_collision(self):
        result = dedupe_filename("new.txt", {"old.txt"})
        self.assertEqual(result, "new.txt")

    def test_collision(self):
        result = dedupe_filename("test.txt", {"test.txt"})
        self.assertEqual(result, "test_2.txt")

    def test_multiple_collisions(self):
        existing = {"test.txt", "test_2.txt", "test_3.txt"}
        result = dedupe_filename("test.txt", existing)
        self.assertEqual(result, "test_4.txt")

    def test_case_insensitive(self):
        result = dedupe_filename("Test.txt", {"test.txt"})
        self.assertEqual(result, "Test_2.txt")

    def test_no_extension(self):
        result = dedupe_filename("mydoc", {"mydoc"})
        self.assertEqual(result, "mydoc_2")


class TestExtractMarkdownAssets(unittest.TestCase):
    def test_no_images(self):
        assets, warnings = extract_markdown_assets("# Just text")
        self.assertEqual(assets, [])
        self.assertEqual(warnings, [])

    def test_relative_path_image(self):
        body = "![alt](image.png)"
        assets, warnings = extract_markdown_assets(body)
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0].original_ref, "image.png")
        self.assertEqual(assets[0].status, "missing")

    def test_note_image_token(self):
        body = "![alt](note-image://abc123)"
        assets, warnings = extract_markdown_assets(body)
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0].status, "embedded")
        self.assertEqual(assets[0].db_image_id, "abc123")

    def test_data_url(self):
        body = "![alt](data:image/png;base64,iVBORw0KGgo=)"
        assets, warnings = extract_markdown_assets(body)
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0].status, "embedded")
        self.assertEqual(assets[0].mime_type, "png")

    def test_external_url(self):
        body = "![alt](https://example.com/image.png)"
        assets, warnings = extract_markdown_assets(body)
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0].status, "external")

    def test_multiple_images(self):
        body = "![a](a.png)\n![b](b.png)\n![c](note-image://xyz)"
        assets, warnings = extract_markdown_assets(body)
        self.assertEqual(len(assets), 3)

    def test_relative_path_with_base(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = Path(tmpdir) / "test.png"
            img_path.write_bytes(b"fake image")

            body = "![alt](test.png)"
            assets, warnings = extract_markdown_assets(body, base_path=str(img_path))

            self.assertEqual(len(assets), 1)
            self.assertEqual(assets[0].status, "ok")
            self.assertIsNotNone(assets[0].resolved_path)


if __name__ == "__main__":
    unittest.main()
