# PySide6 V8 JS逆向执行框架

基于 Qt WebEngine 的 JS 逆向执行框架，无需补环境，直接执行加密 JS 代码。

## 安装依赖

```bash
pip install PySide6
```

## 快速开始

```python
from v8engine import V8Engine

engine = V8Engine()

result = engine.run_js("1 + 1")
engine.run_js_file("encrypt.js")
sign = engine.run_js("getSign('data')")
```

## 使用示例

### 1. 基础用法

```python
engine = V8Engine()

engine.run_js(code)  # 执行 JS
engine.run_js_file(filepath)  # 执行 JS 文件
```

### 2. 加载目标网站

```python
engine = V8Engine("https://target.com")
engine.wait_ready()

result = engine.run_js("document.title")
```

### 3. Hook 函数

```python
engine.hook("JSON.stringify", '''
    console.log("args:", __args__);
    return __original__.apply(this, __args__);
''')

engine.hook("window.encrypt", '''
    console.log("input:", __args__[0]);
    return __original__.apply(this, __args__);
''')
```

### 4. 存储和 Cookie

```python
engine.set_local_storage("token", "abc123")
token = engine.get_local_storage("token")

engine.set_cookie("session", "xyz", domain=".example.com")
cookies = engine.get_cookies()
```

### 5. 控制台日志

```python
logs = engine.get_console_logs()  # 获取 console.log
errors = engine.get_console_errors()  # 获取 JS 错误
engine.clear_console()  # 清空
```

### 6. 代理和 UA

```python
engine = V8Engine(proxy="http://127.0.0.1:7890")
engine = V8Engine(proxy="socks5://127.0.0.1:1080")
engine = V8Engine(user_agent="Mozilla/5.0 (iPhone...)")
```

### 7. 调试工具

```python
engine = V8Engine("https://target.com", show=True)
engine.open_devtools()
engine.screenshot("page.png")
```

## API

| 方法 | 说明 |
|------|------|
| `V8Engine(url, show, stealth, user_agent, proxy)` | 创建引擎 |
| `wait_ready(timeout)` | 等待页面加载 |
| `load_url(url)` | 加载 URL |
| `load_html(html, base_url)` | 加载 HTML |
| `run_js(code, timeout)` | 执行 JS |
| `run_js_file(filepath)` | 执行 JS 文件 |
| `hook(func_path, handler)` | Hook 函数 |
| `get_local_storage(key)` | 获取 localStorage |
| `set_local_storage(key, value)` | 设置 localStorage |
| `get_cookies()` | 获取 Cookie |
| `set_cookie(name, value, ...)` | 设置 Cookie |
| `get_console_logs()` | 获取控制台日志 |
| `get_console_errors()` | 获取 JS 错误 |
| `clear_console()` | 清空控制台 |
| `screenshot(path)` | 截图 |
| `open_devtools()` | 打开开发者工具 |

## 原理

通过 Qt WebEngine 内置的 Chromium 引擎执行 JS，自动注入隐身脚本绕过 WebDriver 检测。
