"""Common startup splash screen shown while the application loads."""
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QGuiApplication, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QSplashScreen


def _render_svg(path: Path, target_width: int) -> QPixmap:
    """Render an SVG into a QPixmap at the target width (keeps it crisp)."""
    try:
        from PyQt6.QtSvg import QSvgRenderer
    except ImportError:
        return QPixmap()

    renderer = QSvgRenderer(str(path))
    if not renderer.isValid():
        return QPixmap()

    size = renderer.defaultSize()
    if size.width() <= 0 or size.height() <= 0:
        size.setWidth(target_width)
        size.setHeight(target_width // 3)

    width = target_width
    height = max(1, round(size.height() * (width / size.width())))
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, width, height))
    painter.end()
    return pixmap


def _close_bootloader_splash() -> None:
    """Close the PyInstaller bootloader splash if we are running frozen."""
    try:
        import pyi_splash
        if pyi_splash.is_alive():
            pyi_splash.close()
    except ImportError:
        pass


def show_splash(image_path, background: str = "#FCFAF7",
                padding: int = 20, max_image_width: int = 420,
                radius: int = 14) -> Optional[QSplashScreen]:
    """Show a splash screen with the given image as early as possible.

    Returns the QSplashScreen so the caller can close it once the main
    window is ready, or None when the image is missing/unreadable.
    """
    # Hand off from the bootloader splash (frozen onefile builds) so it does
    # not linger once the Qt-based splash takes over.
    _close_bootloader_splash()

    path = Path(image_path) if image_path else None
    if path is None or not path.exists():
        return None

    if path.suffix.lower() == ".svg":
        image = _render_svg(path, max_image_width)
    else:
        image = QPixmap(str(path))
    if image.isNull():
        return None

    if image.width() > max_image_width:
        image = image.scaledToWidth(
            max_image_width, Qt.TransformationMode.SmoothTransformation
        )

    canvas = QPixmap(image.width() + padding * 2, image.height() + padding * 2)
    canvas.fill(Qt.GlobalColor.transparent)

    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    clip = QPainterPath()
    clip.addRoundedRect(QRectF(canvas.rect()), radius, radius)
    painter.setClipPath(clip)
    painter.fillRect(canvas.rect(), QColor(background))
    painter.drawPixmap(padding, padding, image)
    painter.end()

    splash = QSplashScreen(
        canvas,
        Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
    )
    splash.show()
    QGuiApplication.processEvents()
    return splash
