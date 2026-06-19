# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building PosidNote (posid branding)
"""

import sys
from pathlib import Path

block_cipher = None

# Use absolute path for base directory
base_dir = Path(r'E:\Pjt\Note')
spec_dir = base_dir / 'apps' / 'work_ai_editor'

a = Analysis(
    [str(spec_dir / 'main_posid.py')],
    pathex=[str(base_dir)],
    binaries=[],
    datas=[
        (str(base_dir / 'qml'), 'qml'),
        (str(base_dir / 'assets'), 'assets'),
        (str(base_dir / 'packages'), 'packages'),
        (str(base_dir / 'services'), 'services'),
        (str(base_dir / 'controllers'), 'controllers'),
        (str(base_dir / 'app_bootstrap.py'), '.'),
        (str(base_dir / 'app_config.py'), '.'),
        (str(base_dir / 'tools'), 'tools'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtQml',
        'PyQt6.QtWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineQuick',
        'PyQt6.QtWebEngineWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(base_dir / 'assets' / 'images' / 'posid' / 'posid_logo.ico')
)
