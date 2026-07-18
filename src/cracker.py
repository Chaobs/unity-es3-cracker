"""
cracker.py
==========

High-level orchestration: build candidate passwords and brute-force them
against one or more ES3 save files.

Public functions
-----------------
* ``crack_file(path, candidates, progress_cb)`` -> result dict for one file
* ``crack_batch(paths, game_dir, progress_cb)`` -> aggregate result dict
"""

import os
import re

import es3_crypto
from candidates import build_candidates

# A correct ES3 decryption is printable AND contains ES3 serialization markers
# (e.g. "__type" / "key_"), which our scorer rewards with >= 3 points. Random
# decrypts that merely look printable score <= 2 and are filtered out here to
# avoid flooding the results with false positives.
MIN_SCORE = 3


def crack_file(path: str, candidates: list, progress_cb=None) -> dict:
    """Attempt to crack a single save file with the given candidate list."""
    data = es3_crypto.load_save(path)
    info = es3_crypto.parse_header(data)

    hits = []
    total = len(candidates)
    for i, pw in enumerate(candidates):
        res = es3_crypto.try_password(data, pw)
        if res and res["score"] >= MIN_SCORE:
            hits.append(res)
        if progress_cb and (i % 50 == 0 or i == total - 1):
            progress_cb(i + 1, total, os.path.basename(path))

    # Highest score first; on ties keep shorter (more likely) passwords first.
    hits.sort(key=lambda h: (-h["score"], len(h["password"])))
    return {"path": path, "name": os.path.basename(path), "info": info, "hits": hits}


def crack_batch(paths: list, game_dir: str = None, progress_cb=None) -> dict:
    """Crack multiple save files. Candidates are built once.

    ``progress_cb(phase, cur, total, label)`` where phase is
    ``"scan"`` (building candidates) or ``"crack"`` (testing passwords).
    """
    def _scan(cur, total, label):
        if progress_cb:
            progress_cb("scan", cur, total, label)

    def _crack(cur, total, label):
        if progress_cb:
            progress_cb("crack", cur, total, label)

    candidates = build_candidates(game_dir, progress_cb=_scan)
    results = []
    for p in paths:
        results.append(crack_file(p, candidates, progress_cb=_crack))
    return {"candidates_count": len(candidates), "results": results}
