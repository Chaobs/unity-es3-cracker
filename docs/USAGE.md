# 使用指南（详细）

本文档面向首次使用者，逐步演示如何用本工具破解 Unity Easy Save 3 加密存档。

---

## 前置说明

- 本工具针对 **Easy Save 3（ES3）** 的 AES 加密存档（通常扩展名为 `.es3`）。
- 加密密码由**游戏开发者设定**，常见位置：
  - 写在游戏 C# 代码里的字符串常量（用 dnlib 提取 DLL 字面量找到）；
  - 序列化在 Unity `.assets` 资源中的 `ES3Defaults` ScriptableObject（多数情况）；
  - 或仅仅是 ES3 默认值 `"password"`。
- 工具会自动从你提供的「游戏目录」里把上述位置的字符串都收集成候选密码，再逐个尝试。

---

## 图形界面操作步骤

### 1. 启动

```bash
cd unity-es3-cracker
python main.py
```

若提示找不到 `tkinter`，请用完整 Python 安装（标准库自带 tkinter，通常无需额外安装）。

### 2. 选择游戏目录（推荐）

点击「游戏目录」右侧的 **浏览...**，选择游戏的安装根目录，例如：
```
D:\GamesPirated\NTR Soccer ver.1.0.1
```
工具会递归扫描其中的 `*.dll` 与 `*.assets` 来构建候选密码。
> 若不确定目录，可留空——此时仅使用内置常见密码字典（命中率较低）。

### 3. 选择存档文件

点击「存档文件」右侧的 **选择...**，在文件对话框中**多选** `.es3` 文件，例如：
```
C:\Users\<你>\AppData\LocalLow\<厂商>\<游戏>\save3.es3
```
选中后路径会显示在主界面输入框中（多个文件以 `;` 分隔）。

### 4. 开始破解

点击 **开始破解**。此时：
- 进度条进入不确定动画，状态栏显示「扫描候选 / 破解密码」进度；
- 日志区实时打印正在扫描的文件与命中结果；
- 耗时取决于候选密码数量（数万到十余万不等，通常数十秒到几分钟）。

### 5. 查看结果

破解完成后：
- 左侧结果树按存档文件分组，列出**命中的密码**与置信度；
- 选中某条密码，右侧 **解密预览** 显示该存档明文（ES3 自定义格式）的前 2000 字符；
- 点击 **复制选中密码** 可将密码复制到剪贴板，便于后续手动修改存档。

> 若某文件显示「未找到密码」：尝试提供正确的游戏目录（候选更全面），或手动把疑似密码加入
> `src/candidates.py` 的 `DEFAULT_PASSWORDS` 列表后重试。

---

## 命令行操作步骤

适合批量、自动化或无图形环境：

```bash
# 指定游戏目录，破解多个存档
python -m src.cli --game-dir "D:/Games/NTR Soccer" --saves save1.es3 save2.es3

# 仅用内置字典破解单个存档
python -m src.cli --saves save3.es3

# 以 JSON 输出（便于脚本解析）
python -m src.cli --saves save3.es3 --json
```

输出示例：
```
候选密码总数: 109069

文件: save3.es3
  大小=15536  IV=8c861a80083d0866...  加密=True
  命中密码: mypassword  (置信度 4, AES-128)
  预览: { "key_dialogueData" : { "__type" : "string", "value" : ...
```

---

## 破解成功后如何修改存档

拿到密码后，你可以用如下方式修改存档内容（以金币为例，字段名因游戏而异）：

1. 用本项目的 `es3_crypto` 模块解密：

   ```python
   import sys; sys.path.insert(0, 'src')
   import es3_crypto
   data = es3_crypto.load_save('save3.es3')
   pt, ks = es3_crypto.decrypt_raw(data, 'mypassword')
   text = pt.decode('utf-8')          # ES3 自定义 JSON 文本
   ```

2. 用文本方式将目标字段（如 `key_playerMoney` 的 `"value" : 7750`）改为目标值；
   **保留 `__type` 与数值类型**（float 写 `9999999.0`，int 写 `999999`）。

3. 重新加密（必须用**原 IV** 以保证密钥不变）：

   ```python
   iv = data[:16]
   new_data = es3_crypto.encrypt(text.encode('utf-8'), 'mypassword', iv=iv)
   open('save3.es3', 'wb').write(new_data)
   ```

> 修改前务必备份原存档。不同游戏的字段结构差异很大，盲改嵌套结构（物品/对话）有损坏风险。

---

## 常见问题

**Q：扫描很慢？**
A：`.assets` 文件可能很大（过百 MB），正则扫描本身较慢，属正常。可耐心等待，或只对关键目录提供游戏目录。

**Q：非 Windows 系统能用吗？**
A：可以，但 DLL 字面量提取依赖 PowerShell + dnlib（Windows 专用），会自动回退为字节扫描，
仅损失从 DLL 提取字符串这一来源；`.assets` 扫描与内置字典仍可用。

**Q：置信度是什么意思？**
A：破解器对每个候选密码解密后打分——明文可读且含 ES3 标记（`__type`/`key_`）得分高（≥3 为可靠命中），
随机误解密得分低（被过滤）。置信度最高的密码即为答案。
