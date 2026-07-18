"""
es3_crypto.py
=============

Decryption / re-encryption and validation for **Unity Easy Save 3 (ES3)**
encrypted save files.

Algorithm (reverse-engineered from the game's ES3 assembly, instruction-level):

    IV   = first 16 bytes of the save file
    Key  = PBKDF2-HMAC-SHA1(password, salt=IV, iterations=100, dklen=16)   # AES-128
         = PBKDF2-HMAC-SHA1(password, salt=IV, iterations=100, dklen=32)   # AES-256 (fallback)
    file = IV || AES-CBC(Key, IV).Encrypt(PKCS7(plaintext))

The salt is the IV *itself* (not a fixed string), so the key differs per file.
This is the single most common pitfall when re-implementing ES3 crypto.
"""

import os
import sys
import re
import hashlib
import zlib
import base64

DEFAULT_ITERATIONS = 100
KEY_SIZES = (16, 32)  # try AES-128 first, then AES-256


def _ensure_crypto():
    """Import PyCryptodome's AES, falling back to the vendored copy in libs/."""
    try:
        from Crypto.Cipher import AES  # noqa: F401
        return sys.modules["Crypto"].Cipher.AES
    except Exception:
        here = os.path.dirname(os.path.abspath(__file__))
        libs = os.path.join(here, "..", "libs")
        for cand in (os.path.join(libs, "pycryptodome"), libs):
            if os.path.isdir(cand) and cand not in sys.path:
                sys.path.insert(0, cand)
        from Crypto.Cipher import AES
        return AES


AES = _ensure_crypto()


# --------------------------------------------------------------------------- #
# Low-level primitives
# --------------------------------------------------------------------------- #
def derive_key(password: str, iv: bytes, key_size: int, iterations: int = DEFAULT_ITERATIONS) -> bytes:
    return hashlib.pbkdf2_hmac("sha1", password.encode("utf-8"), iv, iterations, dklen=key_size)


def _pkcs7_valid(data: bytes) -> bool:
    if not data or len(data) == 0:
        return False
    pad = data[-1]
    if pad < 1 or pad > 16:
        return False
    return data[-pad:] == bytes([pad]) * pad


def _pkcs7_unpad(data: bytes) -> bytes:
    return data[:-data[-1]]


def _try_decompress(data: bytes):
    """ES3 may compress plaintext before encryption. Try the common formats."""
    strategies = (
        lambda d: zlib.decompress(d, -15),   # raw deflate
        lambda d: zlib.decompress(d, 15 + 16),  # gzip
        lambda d: zlib.decompress(d),        # zlib
    )
    for fn in strategies:
        try:
            return fn(data)
        except Exception:
            continue
    return None


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def decrypt_raw(data: bytes, password: str):
    """Decrypt ``data`` with ``password``.

    Returns ``(plaintext: bytes, key_size: int)`` on success, else ``(None, None)``.
    """
    if len(data) < 32:
        return None, None
    iv = data[:16]
    ct = data[16:]
    for ks in KEY_SIZES:
        key = derive_key(password, iv, ks)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        try:
            pt = cipher.decrypt(ct)
        except Exception:
            continue
        if not _pkcs7_valid(pt):
            continue
        return _pkcs7_unpad(pt), ks
    return None, None


def score_plaintext(pt: bytes):
    """Score how likely ``pt`` is the real (correctly decrypted) plaintext.

    Returns ``(score: int, display_text: str)``. Higher score = more likely.
    """
    decompressed = _try_decompress(pt)
    data = decompressed if decompressed is not None else pt

    sample = data[:4096]
    if not sample:
        return 0, ""
    printable = sum(1 for b in sample if 32 <= b < 127 or b in (9, 10, 13))
    ratio = printable / len(sample)

    score = 0
    if ratio >= 0.6:
        score += 1
    if ratio >= 0.85:
        score += 1
    # ES3-specific markers (its custom serialization format)
    head = data[:8192].lower()
    if b"__type" in head or b'"key_' in head or b"{" in data[:50]:
        score += 2

    text = data[:2000].decode("utf-8", "replace")
    return score, text


def try_password(data: bytes, password: str):
    """Attempt to decrypt ``data`` with ``password``.

    Returns a dict ``{password, score, text, key_size}`` if the result passes
    validation, otherwise ``None``.
    """
    pt, ks = decrypt_raw(data, password)
    if pt is None:
        return None
    score, text = score_plaintext(pt)
    if score == 0:
        return None
    return {"password": password, "score": score, "text": text, "key_size": ks}


def encrypt(plaintext: bytes, password: str, iv: bytes = None, key_size: int = 16,
           iterations: int = DEFAULT_ITERATIONS) -> bytes:
    """Re-encrypt ``plaintext`` with ``password`` (round-trip for editing)."""
    if iv is None:
        iv = os.urandom(16)
    key = derive_key(password, iv, key_size, iterations)
    pad = 16 - (len(plaintext) % 16)
    pt = plaintext + bytes([pad]) * pad
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(pt)


def parse_header(data: bytes) -> dict:
    """Extract displayable encryption info from a save file."""
    looks_text = False
    if data:
        sample = data[:512]
        printable = sum(1 for b in sample if 32 <= b < 127 or b in (9, 10, 13))
        looks_text = printable / len(sample) > 0.85
    return {
        "size": len(data),
        "looks_encrypted": (len(data) >= 32) and not looks_text,
        "iv_hex": data[:16].hex() if len(data) >= 16 else "",
        "algorithm": "AES-CBC (Easy Save 3)",
    }


def load_save(path: str) -> bytes:
    """Read a save file, transparently base64-decoding if wrapped."""
    with open(path, "rb") as f:
        raw = f.read()
    stripped = raw.strip()
    if len(stripped) % 4 == 0 and re.match(rb"^[A-Za-z0-9+/=\s]+$", stripped):
        try:
            return base64.b64decode(stripped)
        except Exception:
            pass
    return raw
