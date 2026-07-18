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
