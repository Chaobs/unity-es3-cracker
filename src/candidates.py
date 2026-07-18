"""
candidates.py
=============

Builds the list of *candidate passwords* to brute-force against ES3 saves.

Three sources are combined:

1. **Common defaults** — ES3 / Unity save-password guesses (always included).
2. **Game DLLs** — C# string literals extracted via dnlib (PowerShell bridge to
   ``libs/dnlib.dll``). Falls back to a UTF-16 byte scan if PowerShell/dnlib is
   unavailable (e.g. non-Windows).
3. **Unity .assets files** — plaintext string literals embedded in the game's
   asset bundles, scanned with a fast regex. This is where ES3's
   ``ES3Defaults`` encryption password frequently lives (it is a
   ScriptableObject serialized into an asset, *not* a code constant).

The candidate list is de-duplicated and returned as a list.
"""

import os
import re
import sys
import subprocess
import tempfile

DEFAULT_PASSWORDS = [
    # ES3 / Unity common defaults
    "password", "Password", "PASSWORD",
    "My Password", "my password", "mypassword", "MyPassword",
    "easy save", "EasySave", "easysave", "ES3", "es3", "ES3Save",
    "default", "Default", "defaultPassword", "123456", "12345678",
    "admin", "player", "save", "Save", "game", "Game",
    "unity", "Unity", "key", "secret", "encrypt",
]

# Files we definitely do NOT want to scan (huge / irrelevant)
_SKIP_DIR_HINTS = ("streamingassets", "plugin", "mono", "managed", "il2cpp")


# --------------------------------------------------------------------------- #
# Source 2: game DLLs via dnlib
# --------------------------------------------------------------------------- #
def _dnlib_ps1_path():
    # When frozen by PyInstaller, bundled data lives under sys._MEIPASS.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        p = os.path.join(meipass, "libs", "extract_strings.ps1")
        if os.path.exists(p):
            return p
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "libs", "extract_strings.ps1")


def extract_from_dll(dll_path: str):
    """Extract C# string literals from a .NET DLL using dnlib (PowerShell bridge)."""
    ps1 = _dnlib_ps1_path()
    if not os.path.exists(ps1):
        return set()
    out = tempfile.mktemp(suffix=".txt")
    try:
        proc = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps1,
             "-DllPath", dll_path, "-OutFile", out],
            capture_output=True, text=True, timeout=300,
        )
        if proc.returncode != 0 or not os.path.exists(out):
            return set()
        with open(out, "r", encoding="utf-8-sig", errors="ignore") as f:
            return {line.strip() for line in f if line.strip()}
    except Exception:
        return set()
    finally:
        try:
            os.remove(out)
        except Exception:
            pass


def extract_from_dll_fallback(dll_path: str):
    """Fallback: scan DLL bytes for UTF-16LE printable runs (no dnlib needed)."""
    try:
        data = open(dll_path, "rb").read()
    except Exception:
        return set()
    cands = set()
    n = len(data)
    i = 0
    while i < n - 1:
        lo, hi = data[i], data[i + 1]
        if 0x20 <= lo <= 0x7E and hi <= 0x20:
            j = i
            buf = bytearray()
            while j < n - 1 and 0x20 <= data[j] <= 0x7E and data[j + 1] <= 0x20:
                buf.append(data[j])
                j += 2
            s = buf.decode("utf-16-le", "ignore")
            if 1 <= len(s) <= 200 and not s.isdigit():
                cands.add(s)
            i = j
        else:
            i += 1
    return cands


# --------------------------------------------------------------------------- #
# Source 3: .assets files (regex)
# --------------------------------------------------------------------------- #
def extract_from_assets(assets_path: str):
    """Extract ASCII printable runs (3-80 chars, not pure digits) from an asset file."""
    try:
        with open(assets_path, "rb") as f:
            data = f.read()
    except Exception:
        return set()
    cands = set()
    for m in re.finditer(rb"[\x20-\x7e]{3,80}", data):
        s = m.group(0).decode("ascii", "ignore")
        if s.isdigit():
            continue
        cands.add(s)
    return cands


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _should_skip(path: str) -> bool:
    low = path.lower().replace("\\", "/")
    return any(h in low for h in _SKIP_DIR_HINTS)


def scan_game_dir(game_dir: str, progress_cb=None):
    """Walk ``game_dir`` and collect candidate passwords from DLLs + .assets.

    ``progress_cb(cur, total, label)`` is invoked as files are scanned.
    """
    dlls, assets = [], []
    for root, _dirs, files in os.walk(game_dir):
        if _should_skip(root):
            continue
        for fn in files:
            low = fn.lower()
            full = os.path.join(root, fn)
            if low.endswith(".dll"):
                dlls.append(full)
            elif low.endswith(".assets"):
                assets.append(full)

    # Prioritize Assembly-CSharp* DLLs and smaller assets (faster / more likely).
    dlls.sort(key=lambda p: (0 if "assembly-csharp" in os.path.basename(p).lower() else 1,
                             os.path.getsize(p)))
    assets.sort(key=lambda p: os.path.getsize(p))

    cands = set()
    total = min(len(dlls), 6) + min(len(assets), 12)
    done = 0

    for d in dlls[:6]:
        cands |= extract_from_dll(d)
        if not cands:  # dnlib bridge unavailable -> fallback
            cands |= extract_from_dll_fallback(d)
        done += 1
        if progress_cb:
            progress_cb(done, total, os.path.basename(d))

    for a in assets[:12]:
        cands |= extract_from_assets(a)
        done += 1
        if progress_cb:
            progress_cb(done, total, os.path.basename(a))

    return cands


def build_candidates(game_dir=None, progress_cb=None):
    """Build the full de-duplicated candidate password list."""
    cands = set(DEFAULT_PASSWORDS)
    if game_dir and os.path.isdir(game_dir):
        cands |= scan_game_dir(game_dir, progress_cb)
    return list(cands)
