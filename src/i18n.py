"""
i18n.py
======

Bilingual (English / 简体中文) support for the Unity Easy Save 3 password
cracker. The default language is English.

Usage
-----
    from i18n import tr, set_lang, get_lang

    set_lang("zh")                 # switch language
    label = tr("btn_start")        # -> "开始破解"
    text  = tr("log_files", 3)     # -> "待破解存档: 3 个"  (positional %-args)

Translation keys use ``%``-style formatting. Pass positional args to ``tr``; if
the format string contains ``%s`` / ``%d`` they are applied via ``%``.
"""

# --------------------------------------------------------------------------- #
# Translation tables
# --------------------------------------------------------------------------- #
_EN = {
    # --- Window / chrome ---
    "app_title": "Unity Easy Save 3 Save Password Cracker",
    "frame_input": "Input",
    "label_game_dir": "Game directory:",
    "btn_browse": "Browse...",
    "label_saves": "Save files:",
    "btn_select": "Select...",
    "hint_input": "Hint: the game directory is used to extract candidate passwords; "
                  "leave it empty to use only the built-in common passwords.",
    "btn_start": "Start Cracking",
    "btn_copy": "Copy Selected Password",
    # Label of the toggle button shows the language you will switch TO.
    "btn_lang": "中文",
    "status_ready": "Ready",
    "status_working": "Scanning candidates / cracking...",
    "status_done": "Done",
    "status_copied": "Password copied: %s",
    "status_copy_fail": "Copy failed: %s",
    "frame_result": "Crack Results",
    "tree_file": "Save File",
    "tree_pw": "Password",
    "tree_score": "Score",
    "preview_label": "Decrypted preview (first 2000 chars)",
    "frame_log": "Log",

    # --- File dialogs ---
    "dlg_game_title": "Select game install directory",
    "dlg_saves_title": "Select ES3 save files (multiple)",
    "filetype_es3": "ES3 saves",
    "filetype_all": "All files",

    # --- Messages ---
    "warn_no_input": "Missing input",
    "warn_no_input_msg": "Please select at least one valid save file first.",
    "err_run": "Runtime error",
    "ctx_copy": "Copy Password",

    # --- Tree node placeholders (password column) ---
    "tree_file_node": "(file)",
    "tree_no_pw": "(no password found)",

    # --- Log lines ---
    "log_game_dir": "Game directory: %s",
    "log_no_game_dir": "(not provided, built-in passwords only)",
    "log_files": "Save files to crack: %d",
    "log_cand_total": "Total candidate passwords: %d",
    "log_file_info": "  %s | size=%d | IV=%s | encrypted=%s",
    "log_no_pw": "    -> No password found (try providing more game directories "
                 "or a custom password)",
    "log_hit": "    -> Password found: %s (score %d)",
    "log_copied": "Copied password: %s",
    "log_copy_fail": "Copy failed: %s",
    "log_done": "Done.",
    "log_progress": "[%s] %d/%d  %s",
    "log_phase_scan": "scan",
    "log_phase_crack": "crack",

    # --- CLI ---
    "cli_desc": "Unity Easy Save 3 save password cracker (command line)",
    "cli_help_game": "Game install directory (used to extract candidate passwords)",
    "cli_help_saves": "One or more .es3 save files",
    "cli_help_json": "Output results as JSON",
    "cli_cand_total": "Total candidate passwords: %d",
    "cli_file": "\nFile: %s",
    "cli_file_info": "  size=%d  IV=%s...  encrypted=%s",
    "cli_no_pw": "  No password found (try providing more game directories or a "
                "custom password)",
    "cli_hit": "  Password found: %s  (score %d, AES-%d)",
    "cli_preview": "  Preview: %s",
}

_ZH = {
    # --- Window / chrome ---
    "app_title": "Unity Easy Save 3 存档密码破解器",
    "frame_input": "输入",
    "label_game_dir": "游戏目录:",
    "btn_browse": "浏览...",
    "label_saves": "存档文件:",
    "btn_select": "选择...",
    "hint_input": "提示: 游戏目录用于提取候选密码；留空则仅用内置常见密码。",
    "btn_start": "开始破解",
    "btn_copy": "复制选中密码",
    "btn_lang": "English",
    "status_ready": "就绪",
    "status_working": "正在扫描候选密码 / 破解中...",
    "status_done": "完成",
    "status_copied": "密码已复制: %s",
    "status_copy_fail": "复制失败: %s",
    "frame_result": "破解结果",
    "tree_file": "存档文件",
    "tree_pw": "密码",
    "tree_score": "置信度",
    "preview_label": "解密预览 (前 2000 字符)",
    "frame_log": "日志",

    # --- File dialogs ---
    "dlg_game_title": "选择游戏安装目录",
    "dlg_saves_title": "选择 ES3 存档文件 (可多选)",
    "filetype_es3": "ES3 存档",
    "filetype_all": "所有文件",

    # --- Messages ---
    "warn_no_input": "缺少输入",
    "warn_no_input_msg": "请先选择至少一个有效的存档文件。",
    "err_run": "运行错误",
    "ctx_copy": "复制密码",

    # --- Tree node placeholders (password column) ---
    "tree_file_node": "(文件)",
    "tree_no_pw": "(未找到密码)",

    # --- Log lines ---
    "log_game_dir": "游戏目录: %s",
    "log_no_game_dir": "(未提供，仅用内置密码)",
    "log_files": "待破解存档: %d 个",
    "log_cand_total": "候选密码总数: %d",
    "log_file_info": "  %s | 大小=%d | IV=%s | 加密=%s",
    "log_no_pw": "    -> 未找到密码 (可尝试提供更多游戏目录或自定义密码)",
    "log_hit": "    -> 命中密码: %s (置信度 %d)",
    "log_copied": "已复制密码: %s",
    "log_copy_fail": "复制失败: %s",
    "log_done": "完成。",
    "log_progress": "[%s] %d/%d  %s",
    "log_phase_scan": "扫描候选",
    "log_phase_crack": "破解密码",

    # --- CLI ---
    "cli_desc": "Unity Easy Save 3 存档密码破解器 (命令行)",
    "cli_help_game": "游戏安装目录 (用于提取候选密码)",
    "cli_help_saves": "一个或多个 .es3 存档文件",
    "cli_help_json": "以 JSON 输出结果",
    "cli_cand_total": "候选密码总数: %d",
    "cli_file": "\n文件: %s",
    "cli_file_info": "  大小=%d  IV=%s...  加密=%s",
    "cli_no_pw": "  未找到密码 (可尝试提供更多游戏目录或自定义密码)",
    "cli_hit": "  命中密码: %s  (置信度 %d, AES-%d)",
    "cli_preview": "  预览: %s",
}

_TABLES = {"en": _EN, "zh": _ZH}
DEFAULT_LANG = "en"

_state = {"lang": DEFAULT_LANG}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def get_lang() -> str:
    return _state["lang"]


def set_lang(lang: str) -> None:
    if lang in _TABLES:
        _state["lang"] = lang


def tr(key: str, *args):
    """Return the translated string for ``key`` in the active language.

    If positional ``args`` are supplied they are applied to the format string
    with ``%`` (the string uses ``%s`` / ``%d`` placeholders).
    """
    table = _TABLES.get(_state["lang"], _EN)
    s = table.get(key, key)
    if args:
        try:
            s = s % args
        except (TypeError, ValueError):
            pass
    return s
