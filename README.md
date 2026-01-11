# PySide6 V8 Engine - JS逆向执行框架

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

基于 Qt WebEngine 的 JS 逆向执行框架，无需补环境，直接执行加密 JS 代码。

## 特性

- 自动注入隐身脚本，绕过 WebDriver 检测
- 支持 Hook 任意 JS 函数
- 完整的 IDE 类型提示支持

## 安装

```bash
pip install PySide6
```

## 快速开始

```python
from v8engine import V8Engine

engine = V8Engine()

# 执行 JS
result = engine.run_js("1 + 1")
print(result)  # 2

# 执行 JS 文件
engine.run_js_file("encrypt.js")
sign = engine.run_js("getSign('data')")
```

## API 文档

### V8Engine 类

```python
from v8engine import V8Engine

engine = V8Engine(url="", show=False, stealth=True, user_agent=None, proxy=None)
```

#### 构造函数参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | str | "" | 初始 URL |
| `show` | bool | False | 显示窗口 |
| `stealth` | bool | True | 隐身模式（绕过检测） |
| `user_agent` | str | None | 自定义 UA |
| `proxy` | str | None | 代理地址 |

#### 方法

| 方法 | 说明 |
|------|------|
| `wait_ready(timeout)` | 等待页面加载 |
| `load_url(url)` | 加载 URL |
| `load_html(html, base_url)` | 加载 HTML |
| `run_js(code, timeout)` | 执行 JS 并返回结果 |
| `run_js_file(filepath)` | 执行 JS 文件 |
| `hook(func_path, handler)` | Hook JS 函数 |
| `get_local_storage(key)` | 获取 localStorage |
| `set_local_storage(key, value)` | 设置 localStorage |
| `get_cookies()` | 获取 Cookie 列表 |
| `set_cookie(name, value, ...)` | 设置 Cookie |
| `get_console_logs()` | 获取 console.log |
| `get_console_errors()` | 获取 JS 错误 |
| `clear_console()` | 清空控制台 |
| `screenshot(path)` | 截图保存 |
| `open_devtools()` | 打开开发者工具 |

#### 执行 JavaScript

```python
# 同步执行
result = engine.run_js("document.title")

# 执行 JS 文件
engine.run_js_file("encrypt.js")
sign = engine.run_js("getSign('data')")
```

#### Hook 函数

```python
# Hook JSON.stringify
engine.hook("JSON.stringify", '''
    console.log("args:", __args__);
    return __original__.apply(this, __args__);
''')

# Hook 加密函数
engine.hook("window.encrypt", '''
    console.log("input:", __args__[0]);
    return __original__.apply(this, __args__);
''')
```

#### 操作 Storage

```python
# 获取 localStorage
token = engine.get_local_storage("token")

# 设置 localStorage
engine.set_local_storage("token", "new_value")
```

#### 获取 Cookies

```python
# 获取所有 cookies
cookies = engine.get_cookies()

# 设置 cookie
engine.set_cookie("session", "xyz", domain=".example.com")
```

## 完整示例

```python
from v8engine import V8Engine
import requests

# 创建引擎（隐身模式自动绕过检测）
engine = V8Engine("https://example.com")
engine.wait_ready()

# Hook 加密函数观察参数
engine.hook("window.getSign", '''
    console.log("Input:", __args__);
    return __original__.apply(this, __args__);
''')

# 注入扣下来的 JS
engine.run_js_file("sign.js")

# 调用加密函数
data = "username=test&password=123"
sign = engine.run_js(f"getSign('{data}')")

# 查看 console 输出
for log in engine.get_console_logs():
    print(log["message"])

# 发送请求
resp = requests.post(
    "https://example.com/api/login",
    data=data,
    headers={"X-Sign": sign}
)
```

## 代理和 UA

```python
# HTTP 代理
engine = V8Engine(proxy="http://127.0.0.1:7890")

# SOCKS5 代理
engine = V8Engine(proxy="socks5://127.0.0.1:1080")

# 自定义 User-Agent
engine = V8Engine(user_agent="Mozilla/5.0 (iPhone...)")
```

## 调试工具

```python
# 显示窗口并打开 DevTools
engine = V8Engine("https://target.com", show=True)
engine.open_devtools()

# 截图
engine.screenshot("page.png")
```

## 注意事项

1. 首次运行会下载 Qt WebEngine（约100MB）
2. 隐身模式可绕过大部分 WebDriver 检测
3. `get_cookies()` 会实时收集页面加载过程中的所有 Cookie
4. `screenshot()` 即使窗口不可见也能正常截图

## License

MIT License
