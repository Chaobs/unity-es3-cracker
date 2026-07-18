"""
Unity Easy Save 3 存档密码破解器 — 入口
"""

import os
import sys

# Ensure the src/ package is importable regardless of CWD.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from gui import main
from cracker import crack_batch
from es3_crypto import encrypt


def _self_test():
    """Headless smoke test for the frozen .exe (no Tk / no display needed).

    Builds a synthetic ES3 save with a known password that lives in the
    built-in candidate list, then runs the real crack pipeline against it.
    Proves the bundled crypto + candidate logic work inside the single-file
    executable. Triggered only by ``ES3_SELFTEST=1``.
    """
    import tempfile
    plaintext = b'{"__type":"float","value":1}{"key_playerMoney":{"__type":"float","value":9999}}'
    blob = encrypt(plaintext, "mypassword")
    fd, path = tempfile.mkstemp(suffix=".es3")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(blob)
    try:
        res = crack_batch([path], None)
        found = any(h["password"] == "mypassword"
                      for r in res["results"] for h in r["hits"])
        line = "SELFTEST candidates=%d found_password=%s" % (res["candidates_count"], found)
        # The frozen .exe is windowed (no console), so also persist the
        # result to a file that a caller (or the build script) can read.
        try:
            with open(os.path.join(os.environ.get("TEMP", "."),
                                 "UnityES3Cracker_selftest.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception:
            pass
        print(line)
        return 0 if found else 1
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


if __name__ == "__main__":
    if os.environ.get("ES3_SELFTEST") == "1":
        sys.exit(_self_test())
    main()
