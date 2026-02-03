"""
Tarsier 页面标记模块
使用 Tarsier 的标签功能获取元素映射，不依赖 OCR
"""
from typing import Dict, Tuple, Optional, Any
from playwright.async_api import Page


class DummyOCRService:
    """虚拟 OCR 服务（同步方法）"""
    
    def annotate(self, image: bytes) -> list:
        """返回空标注列表"""
        return []


class PageTagger:
    """页面标记器，使用 Tarsier 为页面元素添加可视标签"""

    def __init__(self):
        self._tarsier = None

    def _get_tarsier(self):
        """获取 Tarsier 实例"""
        if self._tarsier is None:
            from tarsier import Tarsier
            self._tarsier = Tarsier(DummyOCRService())
        return self._tarsier

    async def tag_page(self, page: Page) -> Tuple[Optional[bytes], Dict[int, str]]:
        """
        为页面添加标签并返回标记后的截图和标签映射
        
        Returns:
            Tuple[Optional[bytes], Dict[int, str]]: (标记后的截图字节, 标签ID到XPath的映射)
        """
        try:
            tarsier = self._get_tarsier()
            
            # 使用 page_to_image 获取截图和标签映射，保持标签显示
            screenshot_base64, tag_metadata = await tarsier.page_to_image(
                page,
                tag_text_elements=True,
                keep_tags_showing=True,  # 保持标签在页面上显示
            )
            
            # 从 TagMetadata 中提取 xpath 映射
            tag_to_xpath: Dict[int, str] = {}
            
            for tag_id, meta in tag_metadata.items():
                tag_to_xpath[tag_id] = meta["xpath"]
            
            # 将 base64 转换为字节，或者直接获取新截图
            import base64
            if isinstance(screenshot_base64, str):
                # 如果是 base64 字符串，解码为字节
                try:
                    screenshot_bytes = base64.b64decode(screenshot_base64)
                except Exception:
                    # 如果解码失败，直接截图
                    screenshot_bytes = await page.screenshot(type="png")
            elif isinstance(screenshot_base64, bytes):
                screenshot_bytes = screenshot_base64
            else:
                # 其他情况，直接截图（带标签的页面）
                screenshot_bytes = await page.screenshot(type="png")
            
            return screenshot_bytes, tag_to_xpath
            
        except Exception as e:
            print(f"Tarsier 标记失败: {e}，使用备用方案")
            return await self._fallback_tag_page(page)

    async def _fallback_tag_page(self, page: Page) -> Tuple[Optional[bytes], Dict[int, str]]:
        """备用方案：直接通过 JavaScript 提取页面元素并生成映射"""
        try:
            result = await page.evaluate("""
                () => {
                    function getXPath(element) {
                        if (element.id) {
                            return `//*[@id="${element.id}"]`;
                        }
                        if (element === document.body) {
                            return '/html/body';
                        }
                        let ix = 0;
                        const siblings = element.parentNode ? element.parentNode.childNodes : [];
                        for (let i = 0; i < siblings.length; i++) {
                            const sibling = siblings[i];
                            if (sibling === element) {
                                const parentPath = element.parentNode ? getXPath(element.parentNode) : '';
                                return `${parentPath}/${element.tagName.toLowerCase()}[${ix + 1}]`;
                            }
                            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                                ix++;
                            }
                        }
                        return '';
                    }
                    
                    const selectors = 'a, button, input, textarea, select, [onclick], [role="button"], [type="submit"]';
                    const elements = document.querySelectorAll(selectors);
                    const results = [];
                    const xpaths = {};
                    let id = 1;
                    
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        if (style.display === 'none' || style.visibility === 'hidden') {
                            return;
                        }
                        
                        const tag = el.tagName.toLowerCase();
                        let text = el.textContent?.trim() || el.value || el.placeholder || el.title || el.getAttribute('aria-label') || '';
                        text = text.replace(/\\s+/g, ' ').substring(0, 60);
                        
                        if (text || tag === 'input' || tag === 'textarea') {
                            let prefix = '$';
                            if (tag === 'a') prefix = '@';
                            else if (tag === 'input' || tag === 'textarea') prefix = '#';
                            
                            const displayText = text || `[${tag}]`;
                            results.push(`[${prefix}${id}] ${displayText}`);
                            xpaths[id] = getXPath(el);
                            id++;
                        }
                    });
                    
                    return {
                        elements: results.join('\\n'),
                        xpaths: xpaths
                    };
                }
            """)
            
            tag_to_xpath = {int(k): v for k, v in result['xpaths'].items()}
            
            # 获取截图（备用方案没有标记，但也返回截图）
            screenshot_bytes = await page.screenshot(type="png")
            
            return screenshot_bytes, tag_to_xpath
            
        except Exception as e:
            print(f"备用方案也失败: {e}")
            return None, {}

    async def remove_tags(self, page: Page) -> None:
        """移除页面上的标签"""
        try:
            tarsier = self._get_tarsier()
            await tarsier.remove_tags(page)
        except Exception:
            pass

    async def cleanup(self, page: Page) -> None:
        """清理标签（remove_tags 的别名）"""
        await self.remove_tags(page)
