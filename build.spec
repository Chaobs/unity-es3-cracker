# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for unity-es3-cracker
# Produces a single self-contained Windows executable (onefile) that needs
# no Python install. Run with:
#   python -m PyInstaller build.spec
#
# The GUI is Tkinter (console=False). The bundled ``libs/extract_strings.ps1``
# and ``libs/dnlib.dll`` are placed under ``libs/`` inside the frozen package
# so the PowerShell bridge can locate dnlib.dll at runtime (via sys._MEIPASS).

import os

# PyInstaller injects SPECPATH into the spec namespace.
SRC_DIR = os.path.join(SPECPATH, "src")
LIBS_DIR = os.path.join(SPECPATH, "libs")

block_cipher = None

a = Analysis(
    [os.path.join(SPECPATH, "main.py")],
    pathex=[SRC_DIR, SPECPATH],
    binaries=[],
    datas=[
        (os.path.join(LIBS_DIR, "extract_strings.ps1"), "libs"),
        (os.path.join(LIBS_DIR, "dnlib.dll"), "libs"),
    ],
    hiddenimports=["gui", "cracker", "candidates", "es3_crypto", "i18n", "cli"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter.test",
        "tkinter.test.support",
        "unittest",
        "pydoc",
        "doctest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="UnityES3Cracker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
