"""Image service for handling clipboard images and file storage."""
import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from PyQt6.QtGui import QImage, QClipboard
from PyQt6.QtCore import QBuffer, QByteArray, QIODevice


class ImageService:
    """Handles image operations including clipboard paste and file storage."""
    
    def __init__(self, base_path: Optional[str] = None):
        """Initialize image service with storage path."""
        if base_path is None:
            base_path = Path(__file__).parent.parent / "app_data" / "images"
        
        self.images_dir = Path(base_path)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
    def save_clipboard_image(self, image: QImage, note_id: str) -> Optional[str]:
        """Save clipboard image to storage and return relative path."""
        if image.isNull():
            return None
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{note_id}_{timestamp}_{str(uuid.uuid4())[:8]}.png"
        filepath = self.images_dir / filename
        
        # Save image as PNG
        if image.save(str(filepath), "PNG"):
            return f"images/{filename}"
        
        return None
    
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
    
    def insert_image_markdown(self, content: str, cursor_pos: int, 
                              image_path: str, alt_text: str = "image") -> str:
        """Insert markdown image tag at cursor position."""
        markdown = f"\n![{alt_text}]({image_path})\n"
        
        if cursor_pos < 0 or cursor_pos > len(content):
            cursor_pos = len(content)
        
        return content[:cursor_pos] + markdown + content[cursor_pos:]
    
    def delete_image(self, relative_path: str) -> bool:
        """Delete image file."""
        filepath = self.images_dir.parent / relative_path
        try:
            if filepath.exists():
                filepath.unlink()
                return True
        except Exception as e:
            print(f"[ImageService] Delete error: {e}")
        
        return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get image storage statistics."""
        try:
            files = list(self.images_dir.glob("*.png"))
            total_size = sum(f.stat().st_size for f in files)
            
            return {
                'count': len(files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'directory': str(self.images_dir)
            }
        except Exception as e:
            print(f"[ImageService] Stats error: {e}")
            return {'count': 0, 'total_size_mb': 0, 'directory': str(self.images_dir)}
