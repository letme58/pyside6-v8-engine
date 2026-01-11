"""PySide6 V8 JS逆向执行框架"""
import sys
import os
import json
from typing import Any, List, Optional
from PySide6.QtCore import QTimer, QEventLoop, QUrl
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineSettings, QWebEngineProfile,
    QWebEngineScript
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtNetwork import QNetworkProxy, QNetworkCookie

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--ignore-gpu-blocklist --enable-webgl --enable-accelerated-2d-canvas "
    "--disable-blink-features=AutomationControlled"
)

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
window.chrome = {runtime: {}};
"""


class V8Page(QWebEnginePage):
    def __init__(self, profile=None, parent=None):
        if profile:
            super().__init__(profile, parent)
        else:
            super().__init__(parent)
        self.console_logs = []
        self.console_errors = []
    
    def javaScriptConsoleMessage(self, level, message, line, source):
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            self.console_errors.append({"message": message, "line": line})
        else:
            self.console_logs.append({"message": message, "line": line})


class V8Engine(QWebEngineView):
    def __init__(self, url="", show=False, stealth=True, user_agent=None, proxy=None):
        _ensure_app()
        super().__init__()
        self._profile = QWebEngineProfile()
        if user_agent:
            self._profile.setHttpUserAgent(user_agent)
        if proxy:
            self._set_proxy(proxy)
        
        self._page = V8Page(self._profile, self)
        self.setPage(self._page)
        self._result = None
        self._done = False
        self._loaded = False
        self._cookies = {}
        
        self._setup_settings()
        if stealth:
            self._inject_stealth()
        self._setup_cookie_tracking()
        
        self.page().loadFinished.connect(self._on_load)
        if show:
            self.resize(1280, 800)
            self.show()
        
        if url:
            self.load_url(url)
        else:
            self.setHtml("<!DOCTYPE html><html><body></body></html>", QUrl("http://localhost/"))
            self._wait(300)
            self._loaded = True
    
    def _setup_settings(self):
        s = self.page().settings()
        s.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        s.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
    
    def _set_proxy(self, proxy_url):
        from urllib.parse import urlparse
        p = urlparse(proxy_url)
        proxy = QNetworkProxy()
        proxy.setType(QNetworkProxy.HttpProxy if p.scheme in ('http', 'https') else QNetworkProxy.Socks5Proxy)
        proxy.setHostName(p.hostname)
        proxy.setPort(p.port or 1080)
        QNetworkProxy.setApplicationProxy(proxy)
    
    def _inject_stealth(self):
        script = QWebEngineScript()
        script.setSourceCode(STEALTH_JS)
        script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        script.setWorldId(QWebEngineScript.MainWorld)
        self._profile.scripts().insert(script)
    
    def _setup_cookie_tracking(self):
        store = self._profile.cookieStore()
        store.cookieAdded.connect(self._on_cookie_added)
        store.cookieRemoved.connect(self._on_cookie_removed)
    
    def _on_cookie_added(self, cookie):
        key = (cookie.name().data().decode(), cookie.domain(), cookie.path())
        self._cookies[key] = {
            "name": cookie.name().data().decode(),
            "value": cookie.value().data().decode(),
            "domain": cookie.domain(),
            "path": cookie.path()
        }
    
    def _on_cookie_removed(self, cookie):
        key = (cookie.name().data().decode(), cookie.domain(), cookie.path())
        self._cookies.pop(key, None)
    
    def _on_load(self, ok):
        self._loaded = ok
    
    def _wait(self, ms=50):
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()
    
    def _wait_done(self, timeout=10000):
        waited = 0
        while not self._done and waited < timeout:
            self._wait(10)
            waited += 10
        return self._done
    
    def wait_ready(self, timeout=30000):
        waited = 0
        while not self._loaded and waited < timeout:
            self._wait(50)
            waited += 50
        self._wait(100)
        # 页面加载完成后自动清空网页自带的日志
        self.clear_console()
        return self._loaded
    
    def load_url(self, url, wait=True):
        self._loaded = False
        self.page().load(QUrl(url))
        return self.wait_ready() if wait else True
    
    def run_js(self, code, timeout=10000):
        self._result = None
        self._done = False
        def cb(r):
            self._result = r
            self._done = True
        self.page().runJavaScript(code, cb)
        self._wait_done(timeout)
        return self._result
    
    def run_js_file(self, filepath, timeout=10000):
        with open(filepath, 'r', encoding='utf-8') as f:
            result = self.run_js(f.read(), timeout)
        self._wait(200)
        return result
    
    def hook(self, func_path, handler):
        parts = func_path.rsplit('.', 1)
        obj, func = (parts[0], parts[1]) if len(parts) == 2 else ("window", parts[0])
        return self.run_js(f"""
        (function() {{
            if (typeof {func_path} !== 'function') return false;
            const __original__ = {func_path};
            {obj}["{func}"] = function(...__args__) {{ {handler} }};
            return true;
        }})();
        """)
    
    def get_local_storage(self, key: Optional[str] = None):
        if key:
            safe_key = json.dumps(key)
            return self.run_js(f"localStorage.getItem({safe_key})")
        return self.run_js("JSON.stringify(localStorage)")
    
    def set_local_storage(self, key: str, value: str):
        safe_key = json.dumps(key)
        safe_value = json.dumps(value)
        self.run_js(f"localStorage.setItem({safe_key}, {safe_value})")
    
    def get_console_logs(self):
        return self._page.console_logs
    
    def get_console_errors(self):
        return self._page.console_errors
    
    def clear_console(self):
        self._page.console_logs = []
        self._page.console_errors = []
    
    def load_html(self, html, base_url="http://localhost/"):
        self._loaded = False
        self.setHtml(html, QUrl(base_url))
        return self.wait_ready()
    
    def inject_js(self, code, run_at="document_end"):
        script = QWebEngineScript()
        script.setSourceCode(code)
        script.setWorldId(QWebEngineScript.MainWorld)
        point = QWebEngineScript.DocumentReady
        if run_at == "document_start":
            point = QWebEngineScript.DocumentCreation
        elif run_at == "document_idle":
            point = QWebEngineScript.Deferred
        script.setInjectionPoint(point)
        self._profile.scripts().insert(script)
    
    def get_cookies(self):
        # 触发加载所有 cookies，会为每个 cookie 触发 cookieAdded 信号
        self._profile.cookieStore().loadAllCookies()
        self._wait(200)  # 等待信号处理完成
        return list(self._cookies.values())
    
    def set_cookie(self, name: str, value: str, domain: str = "", path: str = "/", url: str = "", **kwargs):
        cookie = QNetworkCookie(name.encode(), value.encode())
        if domain:
            cookie.setDomain(domain)
        cookie.setPath(path)
        if "secure" in kwargs:
            cookie.setSecure(kwargs["secure"])
        if "httponly" in kwargs:
            cookie.setHttpOnly(kwargs["httponly"])
        cookie_url = QUrl(url) if url else self.page().url()
        self._profile.cookieStore().setCookie(cookie, cookie_url)
    
    def screenshot(self, path: str) -> bool:
        if not self.isVisible():
            self.show()
            self._wait(100)
            pixmap = self.grab()
            self.hide()
        else:
            pixmap = self.grab()
        return pixmap.save(path)
    
    def open_devtools(self):
        if hasattr(self, '_devtools') and self._devtools:
            self._devtools.show()
            self._devtools.raise_()
            return
        self._page.setDevToolsPage(V8Page(self._profile))
        dev_view = QWebEngineView()
        dev_view.setPage(self._page.devToolsPage())
        dev_view.resize(1200, 800)
        dev_view.show()
        self._devtools = dev_view


# 全局 QApplication 实例
_app = None

def _ensure_app():
    global _app
    if _app is None:
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app
