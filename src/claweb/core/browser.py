"""
浏览器管理模块
"""

from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from claweb.core.config import BrowserConfig


class BrowserManager:
    """浏览器管理器"""

    def __init__(self, config: BrowserConfig):
        self.config = config
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def start(self) -> Page:
        """启动浏览器并返回页面"""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.config.headless
        )
        self._context = await self._browser.new_context(
            viewport={"width": self.config.width, "height": self.config.height}
        )
        self._page = await self._context.new_page()
        return self._page

    @property
    def page(self) -> Optional[Page]:
        """获取当前页面"""
        return self._page

    async def goto(self, url: str) -> None:
        """导航到指定 URL"""
        if self._page:
            await self._page.goto(url, wait_until="networkidle")

    async def screenshot(self) -> bytes:
        """截取页面截图"""
        if self._page:
            return await self._page.screenshot(type="png")
        return b""

    async def close(self) -> None:
        """关闭浏览器"""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def stop(self) -> None:
        """关闭浏览器（close 的别名）"""
        await self.close()
