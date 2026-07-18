"""
Unity Easy Save 3 存档密码破解器 — 入口
"""

import os
import sys

# Ensure the src/ package is importable regardless of CWD.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from gui import main

if __name__ == "__main__":
    main()
