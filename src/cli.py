"""
cli.py
======

Command-line interface for headless / batch cracking.

Example
-------
    python -m src.cli --game-dir "D:/Games/NTR Soccer" --saves save1.es3 save2.es3
    python -m src.cli --saves save3.es3 --json
"""

import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cracker  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Unity Easy Save 3 存档密码破解器 (命令行)")
    ap.add_argument("--game-dir", help="游戏安装目录 (用于提取候选密码)")
    ap.add_argument("--saves", nargs="+", required=True, help="一个或多个 .es3 存档文件")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args()

    res = cracker.crack_batch(args.saves, game_dir=args.game_dir)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
        return

    print("候选密码总数:", res["candidates_count"])
    for r in res["results"]:
        print("\n文件: %s" % r["name"])
        print("  大小=%d  IV=%s...  加密=%s" % (
            r["info"]["size"], r["info"]["iv_hex"][:16], r["info"]["looks_encrypted"]))
        if not r["hits"]:
            print("  未找到密码 (可尝试提供更多游戏目录或自定义密码)")
        for h in r["hits"]:
            print("  命中密码: %s  (置信度 %d, AES-%d)" % (
                h["password"], h["score"], h["key_size"] * 8))
            preview = h["text"][:200].replace("\n", " ")
            print("  预览: %s" % preview)


if __name__ == "__main__":
    main()
