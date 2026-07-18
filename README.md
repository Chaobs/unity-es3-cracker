# Unity Easy Save 3 Save Password Cracker

A graphical / command-line tool to **reverse-engineer and recover the encryption password** of Unity game save files created with the **Easy Save 3 (ES3)** plugin. It automatically harvests candidate passwords from the game directory, brute-forces the AES key that protects `.es3` saves, and shows a decrypted preview of the contents.

> ⚠️ **For single-player games and saves you own only.** Do not use this on online / multiplayer titles, or in any way that violates a game's Terms of Service or infringes on others' rights. This tool is intended for legitimate personal use: save editing, local backup / restore, and offline analysis.

---

## Features

- **GUI (Tkinter):** select a game directory and save files, one-click crack, with live progress and log.
- **Batch processing:** select multiple `.es3` files at once.
- **Automatic candidate harvesting:**
  1. A built-in dictionary of common ES3 / Unity passwords;
  2. **dnlib** parses the game's `.dll` and extracts C# string literals (the most likely place a password lives);
  3. Scans Unity `.assets` bundles for plaintext strings (ES3's default encryption password is often serialized as a `ScriptableObject` inside the assets).
- **Accurate algorithm:** faithfully reproduces ES3 encryption (AES-128/256-CBC, PBKDF2-HMAC-SHA1, salt = file IV). See "How it works" below.
- **Decrypted preview:** on success, shows the first 2000 characters of the decrypted save (ES3's custom serialization format).
- **CLI mode:** for batch / automation / headless environments.
- **Bilingual (English / 中文):** defaults to English. The GUI has a one-click toggle (top-right); the CLI switches via `--lang en|zh`.

## Bilingual

| Entry | Default | Switch |
| --- | --- | --- |
| GUI | English | One-click toggle button (top-right) — all UI text, labels, hints, logs and results refresh instantly |
| CLI | English | `--lang zh` outputs Simplified Chinese; `--lang en` (default) outputs English |

> The GUI language state lives only in memory for the current run; it resets to English on every launch.

## How it works

ES3's AES encryption format (reverse-engineered from the game assembly, confirmed at the instruction level):

```
IV   = first 16 bytes of the save file (random per file)
Key  = PBKDF2-HMAC-SHA1(password, salt = IV, iterations = 100, dklen = 16)   # AES-128
file = IV || AES-CBC(Key, IV).Encrypt(PKCS7(plaintext))
```

The key trap: **the salt is not a fixed string — it is the file's own IV.** Every save file therefore derives a different key, and deriving with a "fixed salt" never opens the file. This is the biggest gap between many online ES3 examples and real game implementations.

Cracking flow:

1. Read the save → parse the header (size, IV, whether it looks encrypted);
2. Build the candidate set from the game directory (DLL literals + `.assets` strings + built-in dictionary);
3. For each candidate: `decrypt → PKCS7 check → plaintext readability / ES3 marker detection`;
4. The candidate that passes validation with the highest confidence score wins.

## Requirements

| Component | Notes |
|-----------|-------|
| Python | 3.8+ (3.11+ recommended) |
| OS | Windows (dnlib is invoked through a PowerShell bridge; on non-Windows it auto-falls back to byte scanning, losing only the DLL literal extraction) |
| `pycryptodome` | bundled in `libs/pycryptodome/`, no manual install needed |
| `dnlib.dll` | bundled in `libs/dnlib.dll` (open-source .NET assembly parser) |

## Installation

No installation required — dependencies are bundled:

```bash
git clone https://github.com/Chaobs/unity-es3-cracker.git
cd unity-es3-cracker
python main.py
```

If your Python version is incompatible with the bundled `pycryptodome` (rare), reinstall manually:

```bash
pip install -r requirements.txt
```

## Usage

### GUI

```bash
python main.py
```

1. **Game directory:** click "Browse" to select the game's install root (used to harvest candidate passwords). Leave it empty to use only the built-in common passwords.
2. **Save files:** click "Select" to choose one or more `.es3` files (batch supported).
3. Click **Start Crack** and wait for the progress bar and log to finish.
4. The results panel lists each save's **recovered password** (sorted by confidence); click an entry to see the **decrypted preview** on the right.
5. Select a password and click **Copy selected password** to use it (e.g. with an ES3 editor or your own script to modify the save). You can also click or right-click a password row to copy it directly.

### CLI

```bash
# Game directory + multiple saves
python -m src.cli --game-dir "D:/Games/NTR Soccer" --saves save1.es3 save2.es3

# Built-in dictionary only, single save, JSON output
python -m src.cli --saves save3.es3 --json
```

## Project structure

```
unity-es3-cracker/
├── main.py                  # Entry point (launches the GUI)
├── requirements.txt         # Python dependencies
├── README.md
├── LICENSE
├── src/
│   ├── es3_crypto.py        # ES3 AES encrypt/decrypt / validation / header parsing
│   ├── candidates.py        # Candidate password harvesting (dnlib + .assets + built-in dict)
│   ├── cracker.py           # Crack orchestration (single file / batch)
│   ├── gui.py               # Tkinter GUI
│   └── cli.py               # Command-line interface
├── libs/
│   ├── dnlib.dll            # Open-source .NET assembly parser (extracts DLL strings)
│   ├── extract_strings.ps1  # PowerShell bridge that invokes dnlib
│   └── pycryptodome/        # Bundled pycryptodome (Crypto package)
└── docs/
    ├── USAGE.md             # Detailed usage guide (EN/中文)
    └── DEVELOPMENT.md       # Development & algorithm notes
```

## Dependencies

- **dnlib** (MIT, <https://github.com/0xd4d/dnlib>): loaded via `libs/extract_strings.ps1` in PowerShell to extract C# string literals from game DLLs. Windows only; auto-fallback elsewhere.
- **pycryptodome** (BSD, <https://github.com/Legrandin/pycryptodome>): provides AES / PBKDF2, bundled in `libs/pycryptodome/`, auto-added to `sys.path` at startup.

## License

MIT — see [LICENSE](LICENSE).

---

# Unity Easy Save 3 存档密码破解器

一个用于**逆向破解 Unity 游戏（使用 Easy Save 3 插件）加密存档**的图形化 / 命令行工具。
它能自动从游戏目录中提取候选密码，暴力破解 `.es3` 存档的加密密钥，并展示解密后的内容预览。

> ⚠️ **仅限单机游戏 / 你自己拥有的存档**。请勿用于联网对战游戏或任何违反游戏服务条款、侵犯他人权益的场景。本工具面向**存档修改、本地备份还原、离线分析**等合法个人用途。

---

## 功能特性

- **图形界面（GUI）**：选择游戏目录与存档文件，一键破解，实时进度与日志。
- **批量处理**：可同时选择多个 `.es3` 文件。
- **自动候选提取**：
  1. 内置常见 ES3 / Unity 密码字典；
  2. 通过 **dnlib** 解析游戏 `.dll`，提取 C# 字符串字面量（密码最可能的来源）；
  3. 扫描 Unity `.assets` 资源包中的明文字符串（ES3 默认加密密码常以 `ScriptableObject` 形式序列化在资源里）。
- **算法实现**：精确还原 ES3 加密（AES‑128/256‑CBC，PBKDF2‑HMAC‑SHA1，salt = 文件 IV），详见下文「工作原理」。
- **解密预览**：破解成功后直接展示存档明文（ES3 自定义序列化格式）前 2000 字符。
- **命令行模式**：适合批量 / 自动化 / 无界面环境。
- **双语支持（中 / 英）**：默认英文。图形界面右上角有一键切换按钮，点击后界面文本、按钮标签、提示、日志与破解结果立即更新为对应语言；命令行通过 `--lang en|zh` 切换输出语言。

---

## 双语支持 / Bilingual

| 入口 | 默认语言 | 切换方式 |
| --- | --- | --- |
| 图形界面 (GUI) | 英文 | 点击右上角语言切换按钮，一键在中英文间切换，所有界面与结果即时刷新 |
| 命令行 (CLI) | 英文 | `--lang zh` 输出简体中文，`--lang en`（默认）输出英文 |

> GUI 的切换状态仅保存在本次运行内存中，每次启动默认回到英文。

---

## 工作原理

Easy Save 3 的 AES 加密格式（逆向自游戏程序集，指令级确认）：

```
IV   = 存档文件的前 16 字节（每个文件随机生成）
Key  = PBKDF2-HMAC-SHA1(password, salt = IV, iterations = 100, dklen = 16)   # AES-128
文件 = IV || AES-CBC(Key, IV).Encrypt(PKCS7(明文))
```

关键陷阱：**salt 不是固定字符串，而是文件自身的 IV**。因此每个存档文件的密钥都不同，
用「固定 salt」去派生永远解不开——这是网上许多 ES3 示例与真实游戏实现之间最大的差异。

破解流程：

1. 读取存档 → 解析头部（大小、IV、是否像加密数据）；
2. 从游戏目录构建候选密码集合（DLL 字面量 + .assets 字符串 + 内置字典）；
3. 对每个候选密码执行 `解密 → PKCS7 校验 → 明文可读性 / ES3 标记检测`；
4. 通过校验且置信度最高的密码即为结果。

---

## 环境要求

| 组件 | 说明 |
|------|------|
| Python | 3.8+（推荐 3.11+） |
| 操作系统 | Windows（dnlib 通过 PowerShell 桥接调用；非 Windows 时自动回退为字节扫描，仅损失 DLL 字面量提取） |
| `pycryptodome` | 已随项目打包在 `libs/pycryptodome/`，无需手动安装 |
| `dnlib.dll` | 已随项目打包在 `libs/dnlib.dll`（开源 .NET 程序集解析库） |

---

## 安装

本项目为**免安装**结构，依赖已内置：

```bash
git clone <本仓库地址>
cd unity-es3-cracker
# 直接运行（依赖已在 libs/ 内）
python main.py
```

如果你的 Python 版本与内置 `pycryptodome` 不兼容（极少见），可手动重装：

```bash
pip install -r requirements.txt
```

---

## 使用方法

### 图形界面

```bash
python main.py
```

1. **游戏目录**：点击「浏览」选择游戏安装根目录（用于提取候选密码）。留空则仅使用内置常见密码。
2. **存档文件**：点击「选择」多选 `.es3` 文件（支持批量）。
3. 点击 **开始破解**，等待进度条与日志完成。
4. 结果区会列出每个存档**命中的密码**（按置信度排序），点击某条可在右侧查看**解密预览**。
5. 选中密码后点 **复制选中密码** 即可使用（例如配合 ES3 编辑器或自定义脚本修改存档）。

### 命令行

```bash
# 指定游戏目录 + 多个存档
python -m src.cli --game-dir "D:/Games/NTR Soccer" --saves save1.es3 save2.es3

# 仅用内置字典破解单个存档，并以 JSON 输出
python -m src.cli --saves save3.es3 --json
```

---

## 项目结构

```
unity-es3-cracker/
├── main.py                  # 程序入口（启动 GUI）
├── requirements.txt         # Python 依赖
├── README.md
├── LICENSE
├── src/
│   ├── es3_crypto.py        # ES3 AES 加解密 / 校验 / 头部解析
│   ├── candidates.py        # 候选密码提取（dnlib + .assets + 内置字典）
│   ├── cracker.py           # 破解编排（单文件 / 批量）
│   ├── gui.py               # tkinter 图形界面
│   └── cli.py               # 命令行界面
├── libs/
│   ├── dnlib.dll            # 开源 .NET 程序集解析库（用于提取 DLL 字符串）
│   ├── extract_strings.ps1  # 调用 dnlib 的 PowerShell 桥接脚本
│   └── pycryptodome/        # 随附的 pycryptodome（Crypto 包）
└── docs/
    ├── USAGE.md             # 详细使用指南
    └── DEVELOPMENT.md       # 开发与算法说明
```

---

## 依赖说明

- **dnlib**（MIT 许可证，<https://github.com/0xd4d/dnlib>）：通过 `libs/extract_strings.ps1`
  在 PowerShell 中加载，提取游戏 DLL 的 C# 字符串字面量。Windows 专用；非 Windows 自动回退。
- **pycryptodome**（BSD 许可证，<https://github.com/Legrandin/pycryptodome>）：提供 AES / PBKDF2，
  已打包在 `libs/pycryptodome/`，程序启动时自动加入 `sys.path`。

---

## 许可证

MIT —— 详见 [LICENSE](LICENSE)。
