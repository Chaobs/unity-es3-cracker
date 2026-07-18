"""
gui.py
=======

Tkinter GUI for the Unity Easy Save 3 password cracker.

Features:
  * Select a game install directory (scanned for candidate passwords).
  * Select one or more .es3 save files (batch supported).
  * Live progress bar + log.
  * Results table: per-file found password(s) with a decrypted preview.
  * One-click Chinese / English language toggle (default: English). All UI
    text, button labels, hints, the log and the results re-render instantly.

Internationalization is provided by :mod:`i18n` (``tr`` / ``set_lang``).
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
from i18n import tr, get_lang, set_lang  # noqa: E402


class CrackerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(tr("app_title"))
        self.root.geometry("900x660")
        try:
            self.root.tk.call("tk", "scaling", 1.3)
        except tk.TclError:
            pass

        self.queue = queue.Queue()
        self.cracking = False
        self.last_result = None
        # Structured log buffer so it can be re-rendered on language switch.
        self._log_entries = []

        self._build_widgets()
        self._apply_language()
        self._poll()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_widgets(self):
        pad = {"padx": 8, "pady": 5}

        # --- Top bar: language toggle (top-right, always visible) ---
        frm_top = ttk.Frame(self.root)
        frm_top.pack(fill="x", **pad)
        self.btn_lang = ttk.Button(frm_top, command=self.toggle_lang)
        self.btn_lang.pack(side="right")

        # --- Inputs ---
        self.frm_input = ttk.LabelFrame(self.root, padding=10)
        self.frm_input.pack(fill="x", **pad)

        self.lbl_game_dir = ttk.Label(self.frm_input)
        self.lbl_game_dir.grid(row=0, column=0, sticky="w")
        self.var_game = tk.StringVar()
        ttk.Entry(self.frm_input, textvariable=self.var_game, width=60).grid(row=0, column=1, sticky="ew")
        self.btn_browse = ttk.Button(self.frm_input, command=self.browse_game)
        self.btn_browse.grid(row=0, column=2, padx=4)

        self.lbl_saves = ttk.Label(self.frm_input)
        self.lbl_saves.grid(row=1, column=0, sticky="w")
        self.var_saves = tk.StringVar()
        ttk.Entry(self.frm_input, textvariable=self.var_saves, width=60).grid(row=1, column=1, sticky="ew")
        self.btn_select = ttk.Button(self.frm_input, command=self.browse_saves)
        self.btn_select.grid(row=1, column=2, padx=4)
        self.frm_input.columnconfigure(1, weight=1)

        # --- Action ---
        frm_act = ttk.Frame(self.root)
        frm_act.pack(fill="x", **pad)
        self.btn_start = ttk.Button(frm_act, command=self.start)
        self.btn_start.pack(side="left")
        self.btn_copy = ttk.Button(frm_act, command=self.copy_pw, state="disabled")
        self.btn_copy.pack(side="left", padx=6)

        # Hint on its own row so it can wrap in either language.
        frm_hint = ttk.Frame(self.root)
        frm_hint.pack(fill="x", **pad)
        self.hint_label = ttk.Label(frm_hint, wraplength=820, anchor="w")
        self.hint_label.pack(side="left", fill="x", expand=True)

        # --- Progress ---
        frm_prog = ttk.Frame(self.root)
        frm_prog.pack(fill="x", **pad)
        self.var_status = tk.StringVar()
        ttk.Label(frm_prog, textvariable=self.var_status, width=70).pack(side="left")
        self.pb = ttk.Progressbar(frm_prog, mode="indeterminate")
        self.pb.pack(side="right", fill="x", expand=True, padx=6)

        # --- Results (left: files/hits, right: preview) ---
        self.frm_res = ttk.LabelFrame(self.root, padding=8)
        self.frm_res.pack(fill="both", expand=True, **pad)

        paned = ttk.PanedWindow(self.frm_res, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # left: tree of files -> hits
        left = ttk.Frame(paned)
        self.tree = ttk.Treeview(left, columns=("pw", "score"), show="tree headings",
                                 height=12)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        # Click-to-copy (left click on a password row) + right-click menu.
        self.ctx_menu = tk.Menu(self.tree, tearoff=0)
        self.ctx_menu.add_command(label=tr("ctx_copy"), command=self._copy_from_menu)
        self.tree.bind("<Button-1>", self._on_left_click)
        self.tree.bind("<Button-3>", self._on_right_click)
        paned.add(left, weight=1)

        # right: decrypted preview + log
        right = ttk.Frame(paned)
        self.lbl_preview = ttk.Label(right)
        self.lbl_preview.pack(anchor="w")
        self.preview = scrolledtext.ScrolledText(right, wrap="word", height=10)
        self.preview.pack(fill="both", expand=True)
        paned.add(right, weight=2)

        # --- Log ---
        self.frm_log = ttk.LabelFrame(self.root, padding=6)
        self.frm_log.pack(fill="both", expand=True, **pad)
        self.log = scrolledtext.ScrolledText(self.frm_log, wrap="word", height=8)
        self.log.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    # Language switching
    # ------------------------------------------------------------------ #
    def toggle_lang(self):
        set_lang("zh" if get_lang() == "en" else "en")
        self._apply_language()

    def _apply_language(self):
        """Re-render every piece of translatable UI in the active language."""
        self.root.title(tr("app_title"))

        # Top bar
        self.btn_lang.config(text=tr("btn_lang"))

        # Input frame
        self.frm_input.config(text=tr("frame_input"))
        self.lbl_game_dir.config(text=tr("label_game_dir"))
        self.btn_browse.config(text=tr("btn_browse"))
        self.lbl_saves.config(text=tr("label_saves"))
        self.btn_select.config(text=tr("btn_select"))

        # Action bar
        self.btn_start.config(text=tr("btn_start"))
        self.btn_copy.config(text=tr("btn_copy"))
        self.hint_label.config(text=tr("hint_input"))

        # Results frame + tree headings
        self.frm_res.config(text=tr("frame_result"))
        self.tree.heading("#0", text=tr("tree_file"))
        self.tree.heading("pw", text=tr("tree_pw"))
        self.tree.heading("score", text=tr("tree_score"))
        self.tree.column("#0", width=200)
        self.tree.column("pw", width=180)
        self.tree.column("score", width=60)
        self.ctx_menu.entryconfig(0, label=tr("ctx_copy"))
        self.lbl_preview.config(text=tr("preview_label"))

        # Log frame
        self.frm_log.config(text=tr("frame_log"))

        # Status text (only when idle; live progress keeps its own language)
        if not self.cracking:
            self.var_status.set(tr("status_ready"))

        # Re-render results + log so "output results" follow the new language.
        self._render_results()
        self._render_log()

    # ------------------------------------------------------------------ #
    # File dialogs
    # ------------------------------------------------------------------ #
    def browse_game(self):
        d = filedialog.askdirectory(title=tr("dlg_game_title"))
        if d:
            self.var_game.set(d)

    def browse_saves(self):
        files = filedialog.askopenfilenames(
            title=tr("dlg_saves_title"),
            filetypes=[(tr("filetype_es3"), "*.es3"), (tr("filetype_all"), "*.*")],
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
            messagebox.showwarning(tr("warn_no_input"), tr("warn_no_input_msg"))
            return
        game_dir = self.var_game.get().strip()
        if game_dir and not os.path.isdir(game_dir):
            game_dir = None

        self.tree.delete(*self.tree.get_children())
        self.preview.delete("1.0", tk.END)
        self.log.delete("1.0", tk.END)
        self._log_entries = []
        self.btn_copy.config(state="disabled")
        self.cracking = True
        self.btn_start.config(state="disabled")
        self.pb.start(20)
        self.var_status.set(tr("status_working"))

        dir_disp = game_dir if game_dir else tr("log_no_game_dir")
        self._log("log_game_dir", dir_disp)
        self._log("log_files", len(saves))

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
            self.var_status.set(tr("log_progress", tr("log_phase_" + phase), cur, total, label))
            self._log("log_progress", phase, cur, total, label)
        elif kind == "done":
            self._show_result(msg[1])
        elif kind == "error":
            self._log("err_run", msg[1])
            messagebox.showerror(tr("err_run"), msg[1])
            self._finish()

    def _show_result(self, res):
        self.last_result = res
        self._log("log_cand_total", res["candidates_count"])
        for r in res["results"]:
            info = r["info"]
            self._log("log_file_info", r["name"], info["size"],
                      info["iv_hex"][:16] + "...", info["looks_encrypted"])
            if not r["hits"]:
                self._log("log_no_pw")
            for h in r["hits"]:
                self._log("log_hit", h["password"], h["score"])
        self._render_results()
        if res["results"] and any(r["hits"] for r in res["results"]):
            self.btn_copy.config(state="normal")
        self._finish()

    def _render_results(self):
        """Rebuild the results tree from ``last_result`` in the active language."""
        self.tree.delete(*self.tree.get_children())
        res = self.last_result
        if not res:
            return
        for r in res["results"]:
            node = self.tree.insert("", "end", text=r["name"],
                                    values=(tr("tree_file_node"), ""))
            if not r["hits"]:
                self.tree.insert(node, "end", text=tr("tree_no_pw"), values=("-", "-"))
            for h in r["hits"]:
                self.tree.insert(node, "end", text="", values=(h["password"], h["score"]))

    def on_select(self, _evt):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = self.tree.item(item, "values")
        # A real password row is a child whose score column holds a number.
        if not (len(vals) >= 2 and vals[1] not in ("", "-")):
            return
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
            if len(vals) >= 2 and vals[1] not in ("", "-"):
                self._copy_password(vals[0])
                return

    # ------------------------------------------------------------------ #
    # Copy helpers (click / right-click / button) with feedback
    # ------------------------------------------------------------------ #
    @staticmethod
    def _is_pw_row(vals):
        return len(vals) >= 2 and vals[1] not in ("", "-")

    def _copy_password(self, text):
        """Copy ``text`` to the clipboard and report success / failure.

        Feedback is shown both in the status bar and the log so the user gets
        an immediate, durable confirmation in either language.
        """
        if not text:
            return False
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        except Exception as ex:
            self.var_status.set(tr("status_copy_fail", str(ex)))
            self._log("log_copy_fail", str(ex))
            return False
        self.var_status.set(tr("status_copied", text))
        self._log("log_copied", text)
        return True

    def _on_left_click(self, event):
        """Left-click a password row -> copy it to the clipboard."""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        vals = self.tree.item(item, "values")
        if self._is_pw_row(vals):
            self._copy_password(vals[0])

    def _on_right_click(self, event):
        """Right-click a password row -> select it and pop the copy menu."""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        vals = self.tree.item(item, "values")
        if self._is_pw_row(vals):
            self.tree.selection_set(item)
            try:
                self.ctx_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.ctx_menu.grab_release()

    def _copy_from_menu(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        if self._is_pw_row(vals):
            self._copy_password(vals[0])

    def _finish(self):
        self.cracking = False
        self.btn_start.config(state="normal")
        self.pb.stop()
        self.var_status.set(tr("status_done"))

    # ------------------------------------------------------------------ #
    # Logging (buffered so it can be re-rendered on language switch)
    # ------------------------------------------------------------------ #
    def _log(self, key, *args):
        self._log_entries.append((key, args))
        self.log.insert(tk.END, self._fmt(key, args) + "\n")
        self.log.see(tk.END)

    def _fmt(self, key, args):
        if key == "log_progress":
            # Translate the phase token stored as args[0] at render time.
            phase = tr("log_phase_" + args[0])
            return "[%s] %d/%d  %s" % (phase, args[1], args[2], args[3])
        return tr(key, *args)

    def _render_log(self):
        self.log.delete("1.0", tk.END)
        for key, args in self._log_entries:
            self.log.insert(tk.END, self._fmt(key, args) + "\n")
        self.log.see(tk.END)


def main():
    root = tk.Tk()
    CrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
