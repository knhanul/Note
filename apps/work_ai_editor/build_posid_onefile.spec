# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PosidNote one-file build (posid branding)

Usage:
    pyinstaller apps/work_ai_editor/build_posid_onefile.spec

빌드 시 버전과 빌드일자를 입력받아 build_info.json에 기록하고,
실행 파일의 Windows 버전 리소스에도 반영합니다.
비대화형 실행 시 POSID_VERSION / POSID_BUILD_DATE 환경변수로 지정할 수 있습니다.
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

block_cipher = None

# Use absolute path for base directory
base_dir = Path(r'E:\Pjt\Note')
spec_dir = base_dir / 'apps' / 'work_ai_editor'


def _ask(prompt: str, env_key: str, default: str) -> str:
    """Read a build input from env var first, then prompt interactively."""
    value = os.environ.get(env_key, "").strip()
    if value:
        return value
    if sys.stdin is not None and sys.stdin.isatty():
        entered = input(f"{prompt} [{default}]: ").strip()
        return entered or default
    return default


app_version = _ask("버전", "POSID_VERSION", "1.0.0")
build_date = _ask("빌드일자(yyyy-MM-dd)", "POSID_BUILD_DATE", date.today().isoformat())

# Runtime build metadata consumed by app_config.py (_load_build_info)
build_info_path = base_dir / 'build_info.json'
build_info_path.write_text(
    json.dumps({"version": app_version, "build_date": build_date},
               ensure_ascii=False, indent=2),
    encoding='utf-8',
)
print(f"[build_posid_onefile] version={app_version} build_date={build_date}")

# Windows version resource embedded into PosidNote.exe
from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable,
    StringStruct, VarFileInfo, VarStruct,
)

_vparts = (app_version.split("-")[0].split(".") + ["0", "0", "0"])[:4]
_vtuple = tuple(int(p) if p.isdigit() else 0 for p in _vparts)

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=_vtuple,
        prodvers=_vtuple,
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo([
            StringTable('041204B0', [
                StringStruct('CompanyName', '우체국금융개발원 나주 AI킥오프 모임'),
                StringStruct('FileDescription', 'PosidNote'),
                StringStruct('FileVersion', app_version),
                StringStruct('InternalName', 'PosidNote'),
                StringStruct('OriginalFilename', 'PosidNote.exe'),
                StringStruct('ProductName', 'PosidNote'),
                StringStruct('ProductVersion', app_version),
            ])
        ]),
        VarFileInfo([VarStruct('Translation', [1042, 1200])]),
    ],
)

app_datas = [
    (str(base_dir / 'qml'), 'qml'),
    (str(base_dir / 'assets'), 'assets'),
    (str(base_dir / 'packages'), 'packages'),
    (str(base_dir / 'services'), 'services'),
    (str(base_dir / 'controllers'), 'controllers'),
    (str(base_dir / 'app_bootstrap.py'), '.'),
    (str(base_dir / 'app_config.py'), '.'),
    (str(base_dir / 'app_splash.py'), '.'),
    (str(build_info_path), '.'),
]
if (base_dir / 'tools').exists():
    app_datas.append((str(base_dir / 'tools'), 'tools'))

a = Analysis(
    [str(spec_dir / 'main_posid.py')],
    pathex=[str(base_dir)],
    binaries=[],
    datas=app_datas,
    hiddenimports=[
        # Required so PyInstaller bundles the Tcl/Tk script libraries
        # (ttk/cursors.tcl etc.) needed by the bootloader splash screen
        '_tkinter',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtQml',
        'PyQt6.QtWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineQuick',
        'PyQt6.QtWebEngineWidgets',
        'chromadb',
        'chromadb.telemetry.product.posthog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Unused heavy packages pulled in by hooks - exclude to shrink the exe
    # and cut onefile extraction time on startup
    excludes=[
        'torch',
        'transformers',
        'sentence_transformers',
        'sklearn',
        'scipy',
        'tensorflow',
        'matplotlib',
        'sympy',
        'IPython',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Bootloader-level splash: shown by the bootloader while the onefile payload
# is being extracted - much earlier than the Qt splash in app_splash.py.
# Only raster formats are supported (PNG/JPG), not SVG.
splash = Splash(
    str(base_dir / 'assets' / 'images' / 'posid_signature.png'),
    binaries=a.binaries,
    datas=a.datas,
    always_on_top=True,
)

# One-file build: binaries/zipfiles/datas are all embedded in the EXE (no COLLECT)
exe = EXE(
    pyz,
    a.scripts,
    splash,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PosidNote',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=version_info,
    icon=str(base_dir / 'assets' / 'images' / 'posid' / 'posid_logo.ico')
)
