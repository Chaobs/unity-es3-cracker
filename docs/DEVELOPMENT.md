# 开发与算法说明

本文档面向开发者，说明项目结构、核心算法与扩展方式。

---

## 核心算法（ES3 AES 加密）

逆向自游戏 `Assembly-CSharp.dll` 的 `ES3Internal.AESEncryptionAlgorithm`，指令级确认：

| 参数 | 值 |
|------|----|
| 算法 | AES（CBC 模式） |
| 密钥长度 | 优先 128 位（16 字节）；失败回退 256 位（32 字节） |
| 填充 | PKCS7 |
| IV | 存档文件**前 16 字节**（每文件随机生成） |
| 盐（salt） | **= IV 本身**（非固定字符串，这是关键差异） |
| 密钥派生 | `PBKDF2-HMAC-SHA1(password, salt=IV, iterations=100, dklen=key_size)` |
| 文件布局 | `[16 字节 IV][密文]` |

对应实现见 `src/es3_crypto.py`：

```python
def derive_key(password, iv, key_size, iterations=100):
    return hashlib.pbkdf2_hmac("sha1", password.encode("utf-8"), iv, iterations, dklen=key_size)

def decrypt_raw(data, password):
    iv, ct = data[:16], data[16:]
    for ks in (16, 32):
        key = derive_key(password, iv, ks)
        pt = AES.new(key, AES.MODE_CBC, iv).decrypt(ct)
        if _pkcs7_valid(pt):
            return _pkcs7_unpad(pt), ks
    return None, None
```

> 某些 ES3 版本会在加密前先压缩明文。校验阶段会对解密结果尝试
> raw-deflate / gzip / zlib 解压，并以解压后内容做可读性判断（`_try_decompress`）。

---

## 模块职责

| 文件 | 职责 |
|------|------|
| `src/es3_crypto.py` | 加解密原语、PKCS7 校验、明文打分、头部解析、base64 透明解码 |
| `src/candidates.py` | 候选密码来源：内置字典 + DLL 字面量（dnlib）+ `.assets` 正则 + 回退字节扫描 |
| `src/cracker.py` | 编排：构建候选 → 逐文件暴力解密 → 按置信度排序返回 |
| `src/gui.py` | tkinter 界面，线程化破解避免界面卡死 |
| `src/cli.py` | 命令行入口，支持 `--game-dir` / `--saves` / `--json` |
| `libs/extract_strings.ps1` | 通过 PowerShell 加载 `dnlib.dll`，提取 DLL 的 C# 字符串字面量 |

---

## dnlib 桥接机制

`dnlib` 是 .NET 程序集解析库（开源）。本工具在 Windows 上用 PowerShell 加载它：

```powershell
[void][System.Reflection.Assembly]::LoadFrom("libs/dnlib.dll")
$mod = [dnlib.DotNet.ModuleDefMD]::Load($dllPath)
foreach ($type in $mod.GetTypes()) {
    # 1) 字段常量字符串
    # 2) 方法体中的 ldstr 操作数（最常见的密码赋值位置）
}
```

提取结果写入临时文本文件，由 Python 读取。若 PowerShell/dnlib 不可用（非 Windows），
`candidates.extract_from_dll_fallback` 退化为对 DLL 字节做 UTF‑16LE 可打印串扫描。

---

## 扩展指南

### 增加内置密码字典
编辑 `src/candidates.py` 的 `DEFAULT_PASSWORDS`。

### 支持新的存档格式
在 `src/es3_crypto.py` 的 `try_password` 中调整 `score_plaintext` 的判定，
或新增解密函数并在 `decrypt_raw` 的候选算法列表中追加。

### 自定义候选来源
在 `src/candidates.py` 的 `scan_game_dir` 中增加新的扫描目标（例如特定配置文件、JSON 资源）。

---

## 测试建议

可用以下方式做自验证：用 `es3_crypto.encrypt` 加密一段已知明文（已知密码），
再交给 `cracker.crack_file` 破解，确认能找回该密码。

```python
import sys; sys.path.insert(0, 'src')
import es3_crypto, cracker
blob = es3_crypto.encrypt(b'{"key_x":{"__type":"int","value":1}}', "test123")
open("sample.es3", "wb").write(blob)
res = cracker.crack_file("sample.es3", ["wrong", "test123"])
assert res["hits"][0]["password"] == "test123"
```

> 注意：`encrypt` 会随机生成 IV，因此每次密文不同，但用相同密码均可解密。
