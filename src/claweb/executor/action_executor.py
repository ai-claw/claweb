"""
动作执行器模块
"""

import re
import asyncio
from typing import Dict, Tuple
from playwright.async_api import Page


class ActionExecutor:
    """动作执行器，解析并执行 LLM 返回的操作指令"""

    CLICK_PATTERN = re.compile(r"CLICK\s*\[[@#$%]?(\d+)\]", re.IGNORECASE)
    TYPE_PATTERN = re.compile(r'TYPE\s*\[[@#$%]?(\d+)\]\s*["\'](.+?)["\']', re.IGNORECASE)
    SCROLL_PATTERN = re.compile(r"SCROLL\s+(UP|DOWN)", re.IGNORECASE)
    GOTO_PATTERN = re.compile(r'GOTO\s*["\'](.+?)["\']', re.IGNORECASE)
    DONE_PATTERN = re.compile(r"DONE", re.IGNORECASE)
    WAIT_PATTERN = re.compile(r"WAIT\s*(\d+)?", re.IGNORECASE)
    PAUSE_PATTERN = re.compile(r"PAUSE", re.IGNORECASE)

    def __init__(self, page: Page):
        self.page = page

    async def execute(
        self, action: str, tag_to_xpath: Dict[int, str]
    ) -> Tuple[bool, str]:
        """执行动作"""
        action = action.strip()

        if self.DONE_PATTERN.search(action):
            return True, "任务完成"

        if self.PAUSE_PATTERN.search(action):
            print("\n⏸️  需要人工操作，请在浏览器中完成验证...")
            input("完成后按 Enter 继续...")
            await asyncio.sleep(1)
            return False, "人工操作完成，继续执行"

        if match := self.WAIT_PATTERN.search(action):
            seconds = int(match.group(1)) if match.group(1) else 2
            seconds = min(seconds, 30)
            await asyncio.sleep(seconds)
            return False, f"等待 {seconds} 秒"

        if match := self.CLICK_PATTERN.search(action):
            tag_id = int(match.group(1))
            return await self._click(tag_id, tag_to_xpath)

        if match := self.TYPE_PATTERN.search(action):
            tag_id = int(match.group(1))
            text = match.group(2)
            return await self._type(tag_id, text, tag_to_xpath)

        if match := self.SCROLL_PATTERN.search(action):
            direction = match.group(1).upper()
            return await self._scroll(direction)

        if match := self.GOTO_PATTERN.search(action):
            url = match.group(1)
            return await self._goto(url)

        return False, f"无法解析动作: {action}"

    async def _click(
        self, tag_id: int, tag_to_xpath: Dict[int, str]
    ) -> Tuple[bool, str]:
        """点击元素"""
        xpath = tag_to_xpath.get(tag_id)
        if not xpath:
            return False, f"找不到标签 [{tag_id}] 对应的元素"

        try:
            element = self.page.locator(f"xpath={xpath}")
            await element.click(timeout=5000)
            await asyncio.sleep(1)
            return False, f"点击了元素 [{tag_id}]"
        except Exception as e:
            return False, f"点击元素 [{tag_id}] 失败: {e}"

    async def _type(
        self, tag_id: int, text: str, tag_to_xpath: Dict[int, str]
    ) -> Tuple[bool, str]:
        """输入文本"""
        xpath = tag_to_xpath.get(tag_id)
        if not xpath:
            return False, f"找不到标签 [{tag_id}] 对应的元素"

        try:
            element = self.page.locator(f"xpath={xpath}")
            await element.clear()
            await element.fill(text)
            await asyncio.sleep(0.5)
            return False, f"在元素 [{tag_id}] 中输入了文本"
        except Exception as e:
            return False, f"输入文本到元素 [{tag_id}] 失败: {e}"

    async def _scroll(self, direction: str) -> Tuple[bool, str]:
        """滚动页面"""
        try:
            delta = -500 if direction == "UP" else 500
            await self.page.mouse.wheel(0, delta)
            await asyncio.sleep(0.5)
            return False, f"向{'上' if direction == 'UP' else '下'}滚动了页面"
        except Exception as e:
            return False, f"滚动失败: {e}"

    async def _goto(self, url: str) -> Tuple[bool, str]:
        """导航到 URL"""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(1)
            return False, f"导航到了 {url}"
        except Exception as e:
            return False, f"导航到 {url} 失败: {e}"
