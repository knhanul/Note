from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import sys


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    brand: str
    app_name: str
    icon_path: Path
    logo_path: str
    qml_dir: Path
    main_qml_path: Path
    qml_import_path: Path
    app_data_dir: Path
    organization_name: str = "nuninote"
    app_version: str = "1.0.0"


def create_app_config(base_dir: Path, argv: Sequence[str]) -> AppConfig:
    # Determine base_dir for read-only data (qml, assets, packages)
    if getattr(sys, 'frozen', False):
        # Running as executable - use _MEIPASS for read-only data
        if hasattr(sys, '_MEIPASS'):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(sys.executable).parent
    else:
        # Running as script - use provided base_dir
        base_dir = base_dir.resolve()
    
    # Determine app_data_dir for writable data
    if getattr(sys, 'frozen', False):
        # Running as executable - use executable directory for writable data
        app_data_dir = Path(sys.executable).parent / "app_data"
    else:
        # Running as script - use base_dir
        app_data_dir = base_dir / "app_data"
    
    qml_dir = base_dir / "qml"
    brand_config = _resolve_brand(base_dir, argv)

    return AppConfig(
        base_dir=base_dir,
        brand=brand_config["brand"],
        app_name=brand_config["app_name"],
        icon_path=brand_config["icon_path"],
        logo_path=brand_config["logo_path"],
        qml_dir=qml_dir,
        main_qml_path=qml_dir / "Main.qml",
        qml_import_path=qml_dir,
        app_data_dir=app_data_dir,
    )


def _resolve_brand(base_dir: Path, argv: Sequence[str]) -> dict:
    args = list(argv)[1:]
    if "posid" in args:
        return {
            "brand": "posid",
            "app_name": "포시드노트",
            "icon_path": base_dir / "assets" / "images" / "posid" / "posid_logo.ico",
            "logo_path": str(base_dir / "assets" / "images" / "posid" / "posid_ename.png"),
        }

    return {
        "brand": "nuni",
        "app_name": "누니노트",
        "icon_path": base_dir / "assets" / "images" / "nuni" / "nuni_ico.ico",
        "logo_path": str(base_dir / "assets" / "images" / "nuni" / "nuni_logo.png"),
    }
