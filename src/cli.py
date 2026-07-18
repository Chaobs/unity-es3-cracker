"""
cli.py
======

Command-line interface for headless / batch cracking.

Example
-------
    python -m src.cli --game-dir "D:/Games/NTR Soccer" --saves save1.es3 save2.es3
    python -m src.cli --saves save3.es3 --json
    python -m src.cli --lang zh --saves save3.es3

The output text is bilingual (English by default). Use ``--lang zh`` for
简体中文. JSON output (``--json``) keeps stable English keys for parsing.
"""

import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cracker  # noqa: E402
from i18n import tr, set_lang  # noqa: E402


def _preparse_lang(argv):
    """Detect --lang before building the parser so help text is translated."""
    lang = "en"
    for i, a in enumerate(argv):
        if a == "--lang" and i + 1 < len(argv):
            lang = argv[i + 1]
        elif a.startswith("--lang="):
            lang = a.split("=", 1)[1]
    set_lang(lang)
    return lang


def main():
    _preparse_lang(sys.argv[1:])

    ap = argparse.ArgumentParser(description=tr("cli_desc"))
    ap.add_argument("--game-dir", help=tr("cli_help_game"))
    ap.add_argument("--saves", nargs="+", required=True, help=tr("cli_help_saves"))
    ap.add_argument("--json", action="store_true", help=tr("cli_help_json"))
    ap.add_argument("--lang", choices=["en", "zh"], default="en",
                    help="Interface language: en | zh")
    args = ap.parse_args()
    set_lang(args.lang)

    res = cracker.crack_batch(args.saves, game_dir=args.game_dir)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
        return

    print(tr("cli_cand_total", res["candidates_count"]))
    for r in res["results"]:
        print(tr("cli_file", r["name"]))
        print(tr("cli_file_info", r["info"]["size"], r["info"]["iv_hex"][:16],
                 r["info"]["looks_encrypted"]))
        if not r["hits"]:
            print(tr("cli_no_pw"))
        for h in r["hits"]:
            print(tr("cli_hit", h["password"], h["score"], h["key_size"] * 8))
            preview = h["text"][:200].replace("\n", " ")
            print(tr("cli_preview", preview))


if __name__ == "__main__":
    main()
