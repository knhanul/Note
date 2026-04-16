"""Image service for handling image conversions and data URL operations."""
from pathlib import Path
from typing import Optional
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QBuffer, QIODevice


class ImageService:
    """Handles image operations for DB storage (base64 data URLs)."""
    
    def __init__(self):
        """Initialize image service."""
        # Keep for legacy relative path resolution
        self.images_dir = Path(__file__).parent.parent / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def get_image_data_url(self, image: QImage) -> str:
        """Convert QImage to base64 data URL for inline display."""
        if image.isNull():
            return ""
        
        # Convert to PNG bytes
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        buffer.close()
        
        # Get base64
        base64_data = buffer.data().toBase64().data().decode()
        return f"data:image/png;base64,{base64_data}"

    def load_image_file_as_data_url(self, file_path: str) -> str:
        """Load a local image file and return as data URL."""
        if not file_path:
            return ""

        image = QImage(file_path)
        if image.isNull():
            return ""

        return self.get_image_data_url(image)
    
    def insert_image_markdown(self, content: str, cursor_pos: int,
                              image_src: str, alt_text: str = "image") -> str:
        """Insert markdown image tag at cursor position."""
        markdown = f"\n![{alt_text}]({image_src})\n"
        
        if cursor_pos < 0 or cursor_pos > len(content):
            cursor_pos = len(content)
        
        return content[:cursor_pos] + markdown + content[cursor_pos:]
    
