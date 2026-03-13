# clonr.spec — PyInstaller build spec
#
# Produces a single-file Windows exe with:
#   - No console window (windowed mode)
#   - UAC manifest requesting Administrator (requireAdministrator)
#   - All PyQt6 dependencies bundled

import os
from PyInstaller.building.build_main import Analysis, PYZ, EXE

block_cipher = None

a = Analysis(
    ['clonr_gui.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
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
    name='Clonr',
    icon='assets/icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,         # triggers proper UAC prompt — no more PowerShell window
    onefile=True,
)
