# src/cliany_site/browser/cdp.py
import asyncio
import aiohttp
import subprocess
from browser_use.browser.session import BrowserSession
from browser_use.browser.profile import BrowserProfile
from cliany_site.browser.launcher import (
    ensure_chrome,
    find_chrome_binary,
    ChromeNotFoundError,
)


class CDPConnection:
    """通过 CDP 连接用户已运行的 Chrome 实例"""

    def __init__(self):
        self._session: BrowserSession | None = None
        self._chrome_proc: subprocess.Popen | None = None
        self._chrome_auto_launched: bool = False

    async def check_available(self, port: int = 9222) -> bool:
        """检查 CDP 端口是否可连接，必要时自动启动 Chrome"""
        try:
            ws_url, proc = ensure_chrome(port)
            if proc is not None:
                self._chrome_proc = proc
                self._chrome_auto_launched = True
            return True
        except ChromeNotFoundError:
            return False
        except Exception:
            return False

    async def connect(self, port: int = 9222) -> BrowserSession:
        """通过 CDP 连接到用户已运行的 Chrome"""
        profile = BrowserProfile(
            cdp_url=f"http://localhost:{port}",
            is_local=True,
        )
        self._session = BrowserSession(browser_profile=profile)
        await self._session.start()
        return self._session

    async def get_pages(self, port: int = 9222) -> list[dict]:
        """获取当前打开的标签页列表"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{port}/json/list",
                    timeout=aiohttp.ClientTimeout(total=2),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return []
        except Exception:
            return []

    async def disconnect(self):
        """断开连接，如果是自动启动的 Chrome 则一并关闭"""
        if self._session:
            try:
                await self._session.stop()
            except Exception:
                pass
            self._session = None
        if self._chrome_proc:
            try:
                self._chrome_proc.terminate()
                self._chrome_proc.wait(timeout=5)
            except Exception:
                pass
            self._chrome_proc = None
