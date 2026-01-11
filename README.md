# PySide6 V8 JS逆向执行框架 - 完美版

基于 Qt WebEngine 的 JS 逆向执行框架，无需补环境，直接执行加密 JS 代码。

## 特性

- ✅ **WebDriver 检测绕过** - 自动注入隐身脚本
- ✅ **Hook 注入** - 拦截任意 JS 函数
- ✅ **异步 JS 支持** - 支持 async/await 和 Promise
- ✅ **开发者工具** - 内置 DevTools 调试
- ✅ **代理支持** - HTTP/SOCKS5 代理
- ✅ **自定义 UA** - 修改 User-Agent
- ✅ **localStorage 操作** - 读写本地存储
- ✅ **Cookie 操作** - 读写 Cookie
- ✅ **截图功能** - 保存页面截图

## 安装

```bash
pip install PySide6
```

## 命令行使用

```bash
# 执行 JS 文件
python main.py encrypt.js

# 指定目标网站
python main.py encrypt.js -url https://target.com

# 直接执行代码
python main.py -c "1+1"

# 显示浏览器窗口
python main.py encrypt.js --show

# 打开开发者工具调试
python main.py -url https://target.com --devtools

# 使用代理
python main.py encrypt.js --proxy http://127.0.0.1:7890

# 自定义 User-Agent
python main.py encrypt.js --ua "Mozilla/5.0 ..."

# 禁用隐身模式
python main.py encrypt.js --no-stealth

# 交互模式
python main.py
>>> document.title
>>> .url https://example.com
>>> .file encrypt.js
>>> .exit
```

## 作为模块使用

### 基础用法

```python
from v8engine import V8Engine

# 创建引擎（自动启用隐身模式）
engine = V8Engine()

# 或加载目标网站
engine = V8Engine("https://target.com")
engine.wait_ready()

# 执行 JS
result = engine.run_js("1 + 1")
print(result)  # 2

# 执行 JS 文件
engine.run_js_file("encrypt.js")
sign = engine.run_js("getSign('data')")
```

### 异步 JS 执行

```python
# 支持 async/await
result = engine.run_js("await fetch('/api').then(r => r.json())")

# 支持 Promise
result = engine.run_js("new Promise(r => setTimeout(() => r('done'), 100))")
```

### Hook 函数

```python
# Hook JSON.stringify
engine.hook("JSON.stringify", '''
    console.log("stringify called:", __args__);
    return __original__.apply(this, __args__);
''')

# Hook 加密函数
engine.hook("window.encrypt", '''
    console.log("encrypt input:", __args__[0]);
    let result = __original__.apply(this, __args__);
    console.log("encrypt output:", result);
    return result;
''')
```

### 代理和 UA

```python
# 使用代理
engine = V8Engine(proxy="http://127.0.0.1:7890")

# SOCKS5 代理
engine = V8Engine(proxy="socks5://127.0.0.1:1080")

# 自定义 User-Agent
engine = V8Engine(user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)")
```

### localStorage 和 Cookie

```python
# 读写 localStorage
engine.set_local_storage("token", "abc123")
token = engine.get_local_storage("token")

# 读写 Cookie（支持 domain, path, url, secure, httponly 参数）
engine.set_cookie("session", "xyz", path="/", domain=".example.com")
engine.set_cookie("token", "abc", secure=True, httponly=True)
cookies = engine.get_cookies()
```

### 开发者工具

```python
# 显示窗口并打开 DevTools
engine = V8Engine("https://target.com", show=True)
engine.open_devtools()
```

### 截图

```python
# 截图保存（即使窗口不可见也能截图）
success = engine.screenshot("page.png")
```

## 实战示例

```python
from v8engine import V8Engine
import requests

# 1. 创建引擎（隐身模式自动绕过检测）
engine = V8Engine("https://example.com")
engine.wait_ready()

# 2. Hook 加密函数观察参数
engine.hook("window.getSign", '''
    console.log("Input:", __args__);
    return __original__.apply(this, __args__);
''')

# 3. 注入扣下来的 JS
engine.run_js_file("sign.js")

# 4. 调用加密函数
data = "username=test&password=123"
sign = engine.run_js(f"getSign('{data}')")

# 5. 查看 console 输出
for log in engine.get_console_logs():
    print(log["message"])

# 6. 发送请求
resp = requests.post(
    "https://example.com/api/login",
    data=data,
    headers={"X-Sign": sign}
)
```

## API 参考

### V8Engine 类

| 方法 | 说明 |
|------|------|
| `V8Engine(url, show, stealth, user_agent, proxy)` | 创建引擎 |
| `wait_ready(timeout)` | 等待页面加载 |
| `load_url(url)` | 加载 URL |
| `load_html(html, base_url)` | 加载 HTML |
| `run_js(code, timeout)` | 执行 JS 并返回结果 |
| `run_js_file(filepath)` | 执行 JS 文件 |
| `inject_js(code, run_at)` | 注入自动执行脚本 |
| `hook(func_path, handler)` | Hook JS 函数 |
| `get_cookies()` | 获取 Cookie 列表 |
| `set_cookie(name, value, domain, path, url, secure, httponly)` | 设置 Cookie |
| `get_local_storage(key)` | 获取 localStorage |
| `set_local_storage(key, value)` | 设置 localStorage |
| `get_console_logs()` | 获取 console.log |
| `get_console_errors()` | 获取 JS 错误 |
| `clear_console()` | 清空控制台 |
| `screenshot(path)` | 截图保存，返回是否成功 |
| `open_devtools()` | 打开开发者工具（重复调用不会创建多个窗口） |

### 构造函数参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | str | "" | 初始 URL |
| `show` | bool | False | 显示窗口 |
| `stealth` | bool | True | 隐身模式（绕过检测） |
| `user_agent` | str | None | 自定义 UA |
| `proxy` | str | None | 代理地址 |

## 注意事项

1. 首次运行会下载 Qt WebEngine（约100MB）
2. 隐身模式可绕过大部分 WebDriver 检测
3. 如需更深度调试，使用 `--devtools` 打开开发者工具
4. `get_cookies()` 会实时收集页面加载过程中的所有 Cookie
5. `screenshot()` 即使窗口不可见也能正常截图
