import os
import sys
from PyInstaller.utils.hooks import collect_data_files

# Collect Tcl/Tk data files for tkinter
tkinter_datas = collect_data_files('tkinter')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=tkinter_datas,          # <-- include Tcl/Tk files here
    hiddenimports=['tkinter'],    # <-- make sure tkinter module is included
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='IOSoccer Mod Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\path\ios.ico'],
)
