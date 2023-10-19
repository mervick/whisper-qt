# -*- mode: python ; coding: utf-8 -*-
import sys

a = Analysis(
    ['app.py'],
    pathex=['app', 'app/ui', 'venv/lib/python3.10/site-packages', 'venv/Lib/site-packages'],
    binaries=[('lib/ffmpeg.exe', '.')] if sys.platform in ('win32', 'cygwin', 'msys') else [],
    # binaries=[],
    datas=[('lib/whisper', 'whisper'), ('LICENSE.txt', '.'), ('COPYING.txt', '.')],
    # datas=[],
    hiddenimports=['appdirs'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

_name = 'whisper-qt'
_icon = 'logo.ico'

# Build on OS X
if sys.platform == 'darwin':
    _name = 'whisper-qt.app',
    _icon = None

# Build on Linux
if sys.platform in ('linux', 'linux2'):
    _icon = 'logo.svg'

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # console=False,
    console=True,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory='lib',
    hide_console='minimize-early',
    icon=_icon
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='whisper-qt',
)
