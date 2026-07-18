"""
gui.py
=======

Tkinter GUI for the Unity Easy Save 3 password cracker.

Features:
  * Select a game install directory (scanned for candidate passwords).
  * Select one or more .es3 save files (batch supported).
  * Live progress bar + log.
  * Results table: per-file found password(s) with a decrypted preview.
"""

import os
import sys
import queue
import threading

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cracker  # noqa: E402


class CrackerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Unity Easy Save 3 存档密码破解器")
        self.root.geometry("880x640")
        try:
            self.root.tk.call("tk", "scaling", 1.3)
        except tk.TclError:
            pass

        self.queue = queue.Queue()
        self.cracking = False
        self.last_result = None

        self._build_widgets()
        self._poll()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_widgets(self):
        pad = {"padx": 8, "pady": 5}

        # --- Inputs ---
        frm_input = ttk.LabelFrame(self.root, text="输入", padding=10)
        frm_input.pack(fill="x", **pad)

        ttk.Label(frm_input, text="游戏目录:").grid(row=0, column=0, sticky="w")
        self.var_game = tk.StringVar()
        ttk.Entry(frm_input, textvariable=self.var_game, width=60).grid(row=0, column=1, sticky="ew")
        ttk.Button(frm_input, text="浏览...", command=self.browse_game).grid(row=0, column=2, padx=4)

        ttk.Label(frm_input, text="存档文件:").grid(row=1, column=0, sticky="w")
        self.var_saves = tk.StringVar()
        ttk.Entry(frm_input, textvariable=self.var_saves, width=60).grid(row=1, column=1, sticky="ew")
        ttk.Button(frm_input, text="选择...", command=self.browse_saves).grid(row=1, column=2, padx=4)
        frm_input.columnconfigure(1, weight=1)

        # --- Action ---
        frm_act = ttk.Frame(self.root)
        frm_act.pack(fill="x", **pad)
        self.btn_start = ttk.Button(frm_act, text="开始破解", command=self.start)
        self.btn_start.pack(side="left")
        self.btn_copy = ttk.Button(frm_act, text="复制选中密码", command=self.copy_pw, state="disabled")
        self.btn_copy.pack(side="left", padx=6)
        ttk.Label(frm_act, text="提示: 游戏目录用于提取候选密码；留空则仅用内置常见密码。").pack(side="left", padx=6)

        # --- Progress ---
        frm_prog = ttk.Frame(self.root)
        frm_prog.pack(fill="x", **pad)
        self.var_status = tk.StringVar(value="就绪")
        ttk.Label(frm_prog, textvariable=self.var_status, width=70).pack(side="left")
        self.pb = ttk.Progressbar(frm_prog, mode="indeterminate")
        self.pb.pack(side="right", fill="x", expand=True, padx=6)

        # --- Results (left: files/hits, right: preview) ---
        frm_res = ttk.LabelFrame(self.root, text="破解结果", padding=8)
        frm_res.pack(fill="both", expand=True, **pad)

        paned = ttk.PanedWindow(frm_res, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # left: tree of files -> hits
        left = ttk.Frame(paned)
        self.tree = ttk.Treeview(left, columns=("pw", "score"), show="tree headings",
                                 height=12)
        self.tree.heading("#0", text="存档文件")
        self.tree.heading("pw", text="密码")
        self.tree.heading("score", text="置信度")
        self.tree.column("#0", width=200)
        self.tree.column("pw", width=180)
        self.tree.column("score", width=60)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        paned.add(left, weight=1)

        # right: decrypted preview + log
        right = ttk.Frame(paned)
        ttk.Label(right, text="解密预览 (前 2000 字符)").pack(anchor="w")
        self.preview = scrolledtext.ScrolledText(right, wrap="word", height=10)
        self.preview.pack(fill="both", expand=True)
        paned.add(right, weight=2)

        # --- Log ---
        frm_log = ttk.LabelFrame(self.root, text="日志", padding=6)
        frm_log.pack(fill="both", expand=True, **pad)
        self.log = scrolledtext.ScrolledText(frm_log, wrap="word", height=8)
        self.log.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    # File dialogs
    # ------------------------------------------------------------------ #
    def browse_game(self):
        d = filedialog.askdirectory(title="选择游戏安装目录")
        if d:
            self.var_game.set(d)

    def browse_saves(self):
        files = filedialog.askopenfilenames(
            title="选择 ES3 存档文件 (可多选)",
            filetypes=[("ES3 存档", "*.es3"), ("所有文件", "*.*")],
        )
        if files:
            self.var_saves.set("; ".join(files))

    # ------------------------------------------------------------------ #
    # Cracking
    # ------------------------------------------------------------------ #
    def start(self):
        if self.cracking:
            return
        saves = [s.strip() for s in self.var_saves.get().split(";") if s.strip()]
        saves = [s for s in saves if os.path.isfile(s)]
        if not saves:
            messagebox.showwarning("缺少输入", "请先选择至少一个有效的存档文件。")
            return
        game_dir = self.var_game.get().strip()
        if game_dir and not os.path.isdir(game_dir):
            game_dir = None

        self.tree.delete(*self.tree.get_children())
        self.preview.delete("1.0", tk.END)
        self.log.delete("1.0", tk.END)
        self.btn_copy.config(state="disabled")
        self.cracking = True
        self.btn_start.config(state="disabled")
        self.pb.start(20)
        self.var_status.set("正在扫描候选密码 / 破解中...")

        self._log("游戏目录: %s" % (game_dir or "(未提供，仅用内置密码)"))
        self._log("待破解存档: %d 个" % len(saves))

        t = threading.Thread(target=self._worker, args=(game_dir, saves), daemon=True)
        t.start()

    def _worker(self, game_dir, paths):
        def progress(phase, cur, total, label):
            self.queue.put(("progress", phase, cur, total, label))

        try:
            res = cracker.crack_batch(paths, game_dir, progress_cb=progress)
            self.queue.put(("done", res))
        except Exception as ex:
            self.queue.put(("error", str(ex)))

    def _poll(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                self._handle(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _handle(self, msg):
        kind = msg[0]
        if kind == "progress":
            _, phase, cur, total, label = msg
            zh = "扫描候选" if phase == "scan" else "破解密码"
            self.var_status.set("%s: %d/%d  %s" % (zh, cur, total, label))
            self._log("[%s] %d/%d  %s" % (zh, cur, total, label))
        elif kind == "done":
            self._show_result(msg[1])
        elif kind == "error":
            self._log("错误: " + msg[1])
            messagebox.showerror("运行错误", msg[1])
            self._finish()

    def _show_result(self, res):
        self.last_result = res
        self._log("候选密码总数: %d" % res["candidates_count"])
        for r in res["results"]:
            node = self.tree.insert("", "end", text=r["name"],
                                    values=("(文件)", ""))
            info = r["info"]
            self._log("  %s | 大小=%d | IV=%s | 加密=%s" % (
                r["name"], info["size"], info["iv_hex"][:16] + "...",
                info["looks_encrypted"]))
            if not r["hits"]:
                self.tree.insert(node, "end", text="(未找到密码)", values=("-", "-"))
                self._log("    -> 未找到密码 (可尝试提供更多游戏目录或自定义密码)")
            for h in r["hits"]:
                self.tree.insert(node, "end", text="",
                                values=(h["password"], h["score"]))
                self._log("    -> 命中密码: %s (置信度 %d)" % (h["password"], h["score"]))
        if res["results"] and any(r["hits"] for r in res["results"]):
            self.btn_copy.config(state="normal")
        self._finish()

    def on_select(self, _evt):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = self.tree.item(item, "values")
        if len(vals) >= 1 and vals[0] not in ("(文件)", "-", ""):
            # find the file this hit belongs to
            parent = self.tree.parent(item)
            fname = self.tree.item(parent, "text") if parent else self.tree.item(item, "text")
            for r in (self.last_result or {}).get("results", []):
                if r["name"] == fname:
                    for h in r["hits"]:
                        if h["password"] == vals[0]:
                            self.preview.delete("1.0", tk.END)
                            self.preview.insert("1.0", h["text"])
                            return

    def copy_pw(self):
        sel = self.tree.selection()
        for item in sel:
            vals = self.tree.item(item, "values")
            if len(vals) >= 1 and vals[0] not in ("(文件)", "-", ""):
                self.root.clipboard_clear()
                self.root.clipboard_append(vals[0])
                self._log("已复制密码: %s" % vals[0])
                return

    def _finish(self):
        self.cracking = False
        self.btn_start.config(state="normal")
        self.pb.stop()
        self.var_status.set("完成")
        # stash result for preview lookups
        # (last_result is set in _show_result via closure)
        self._log("完成。")

    def _log(self, text):
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)


def main():
    root = tk.Tk()
    CrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
