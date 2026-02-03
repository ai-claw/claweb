"""
智能探索模块 - 自主探索网站并学习
"""

import asyncio
import json
import os
import re
import uuid
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from playwright.async_api import Page

from claweb.core.config import Config
from claweb.core.browser import BrowserManager
from claweb.tagger.page_tagger import PageTagger
from claweb.llm.client import VisionLLMClient
from claweb.storage.database import DatabaseInterface
from claweb.storage.models import (
    Site, Page as PageModel, Element, Action, ExplorationLog,
    PageType, ElementType, ActionType
)


class PageAnalyzer:
    """页面分析器 - 使用 LLM 分析页面语义"""
    
    ANALYZE_PAGE_PROMPT = """分析这个网页截图，返回以下 JSON 格式的信息：

{
    "page_type": "页面类型，可选: login/home/list/detail/form/search/settings/error/auth/dashboard/unknown",
    "page_description": "一句话描述这个页面的功能",
    "key_features": ["页面的关键特征"],
    "has_sidebar_nav": true/false,
    "sidebar_nav_items": ["侧边栏导航菜单项名称列表"],
    "important_elements": [
        {
            "semantic_name": "元素的语义名称",
            "element_type": "button/link/input/select/checkbox/nav_item/other",
            "text_content": "元素显示的文本",
            "position": "位置描述",
            "importance": 1-10的重要性评分,
            "is_nav_menu": true/false,
            "action_suggestion": "建议的操作"
        }
    ],
    "suggested_explorations": ["建议探索的操作"]
}

注意：
1. important_elements 只包含值得交互的元素
2. 忽略纯装饰性元素
3. 如果看到登录/验证码页面，page_type 设为 auth
4. 如果有侧边栏导航菜单，has_sidebar_nav 设为 true
5. 导航菜单项的 is_nav_menu 设为 true，importance 设为 9-10"""

    ANALYZE_ELEMENTS_PROMPT = """这是网页截图，页面上的可交互元素已被标记：
- [#ID]：输入框
- [@ID]：链接
- [$ID]：按钮等其他可交互元素

当前页面描述：{page_description}

请分析标记的元素，返回 JSON 格式：
{{
    "elements": [
        {{
            "tag_id": 元素标签ID（纯数字）,
            "semantic_name": "语义名称",
            "element_type": "button/link/input/select/nav_item/other",
            "text_or_hint": "元素文本或提示",
            "importance": 1-10,
            "explore_priority": 1-10,
            "is_nav_menu": true/false,
            "is_crud_action": true/false,
            "crud_type": "create/read/update/delete/none",
            "action_suggestion": "建议操作"
        }}
    ]
}}

重要规则：
1. 侧边栏导航菜单项的 is_nav_menu 设为 true，explore_priority 设为 9-10
2. CRUD 操作按钮必须识别
3. 列表页中的操作列按钮必须标记为高优先级
4. 普通按钮的 explore_priority 设为 3-5
5. 只返回值得探索的元素"""

    def __init__(self, llm_client: VisionLLMClient):
        self.llm = llm_client
    
    async def analyze_page(self, screenshot: bytes) -> Dict:
        """分析页面，返回页面语义信息"""
        try:
            response = await self.llm.analyze_with_vision(
                screenshot,
                self.ANALYZE_PAGE_PROMPT
            )
            
            if response:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"分析页面失败: {e}")
        
        return {
            "page_type": "unknown",
            "page_description": "无法分析的页面",
            "key_features": [],
            "has_sidebar_nav": False,
            "sidebar_nav_items": [],
            "important_elements": [],
            "suggested_explorations": []
        }
    
    async def analyze_elements(
        self, 
        screenshot: bytes, 
        page_description: str
    ) -> List[Dict]:
        """分析标记后的页面元素"""
        try:
            prompt = self.ANALYZE_ELEMENTS_PROMPT.format(page_description=page_description)
            response = await self.llm.analyze_with_vision(screenshot, prompt)
            
            if response:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    data = json.loads(json_match.group())
                    return data.get("elements", [])
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"分析元素失败: {e}")
        
        return []


class SiteExplorer:
    """网站探索器 - 智能探索网站并记录操作"""
    
    def __init__(self, config: Config, db: DatabaseInterface):
        self.config = config
        self.db = db
        self.browser_manager: Optional[BrowserManager] = None
        self.page_tagger = PageTagger()
        self.llm_client = VisionLLMClient(config.llm)
        self.page_analyzer = PageAnalyzer(self.llm_client)
        
        self.session_id = str(uuid.uuid4())[:8]
        self.current_site: Optional[Site] = None
        self.visited_urls: Set[str] = set()
        self.visited_items: Set[str] = set()
        self.pending_items: List[Dict] = []
        self.exploration_depth = 0
        
        os.makedirs(config.exploration.screenshot_dir, exist_ok=True)
    
    async def start(self) -> None:
        """启动探索器"""
        self.browser_manager = BrowserManager(self.config.browser)
        await self.browser_manager.start()
        self.db.connect()
    
    async def stop(self) -> None:
        """停止探索器"""
        if self.browser_manager:
            await self.browser_manager.stop()
        self.db.close()
    
    async def explore_site(self, start_url: str, site_name: str = "") -> Site:
        """探索整个网站"""
        parsed = urlparse(start_url)
        domain = parsed.netloc
        
        self.current_site = self.db.get_or_create_site(domain, site_name)
        
        print(f"\n{'='*60}")
        print(f"🌐 开始探索网站: {domain}")
        print(f"📝 会话 ID: {self.session_id}")
        print(f"{'='*60}\n")
        
        await self.browser_manager.goto(start_url)
        await asyncio.sleep(2)
        
        print("📍 第一阶段：分析页面结构...")
        await self._analyze_and_collect_items()
        
        print(f"\n📍 第二阶段：探索所有项目 (共 {len(self.pending_items)} 个待探索)...")
        await self._explore_all_items()
        
        print(f"\n{'='*60}")
        print(f"✅ 探索完成!")
        print(f"📊 访问页面数: {len(self.visited_urls)}")
        print(f"📊 探索项目数: {len(self.visited_items)}")
        print(f"{'='*60}\n")
        
        return self.current_site
    
    async def _analyze_and_collect_items(self) -> None:
        """分析当前页面并收集导航菜单项和 CRUD 操作"""
        page = self.browser_manager.page
        current_url = page.url
        
        url_key = self._normalize_url(current_url)
        self.visited_urls.add(url_key)
        
        print(f"\n📄 分析页面: {current_url[:80]}...")
        
        screenshot = await self.browser_manager.screenshot()
        page_info = await self.page_analyzer.analyze_page(screenshot)
        
        page_type_str = page_info.get("page_type", "unknown")
        print(f"   类型: {page_type_str}")
        print(f"   描述: {page_info.get('page_description', '未知')}")
        
        if page_info.get("has_sidebar_nav"):
            nav_items = page_info.get("sidebar_nav_items", [])
            print(f"   🧭 发现侧边栏导航: {nav_items}")
        
        title = await page.title()
        page_model = PageModel(
            site_id=self.current_site.id,
            url_pattern=url_key,
            title_pattern=title,
            page_type=PageType(page_type_str) if page_type_str in [e.value for e in PageType] else PageType.UNKNOWN,
            semantic_description=page_info.get("page_description", ""),
            key_features=json.dumps(page_info.get("key_features", []), ensure_ascii=False),
            sample_url=current_url,
            visit_count=1
        )
        page_model = self.db.save_page(page_model)
        
        screenshot_path = os.path.join(
            self.config.exploration.screenshot_dir,
            f"{self.session_id}_{page_model.id}.png"
        )
        with open(screenshot_path, "wb") as f:
            f.write(screenshot)
        
        print("   🏷️ 标记并分析页面元素...")
        tagged_screenshot, tag_to_xpath = await self.page_tagger.tag_page(page)
        
        if tagged_screenshot and tag_to_xpath:
            elements_info = await self.page_analyzer.analyze_elements(
                tagged_screenshot,
                page_info.get("page_description", "")
            )
            
            nav_count = 0
            crud_count = 0
            for elem_info in elements_info:
                tag_id = elem_info.get("tag_id")
                if tag_id is None:
                    continue
                
                semantic_name = elem_info.get("semantic_name", "")
                is_nav = elem_info.get("is_nav_menu", False)
                is_crud = elem_info.get("is_crud_action", False)
                crud_type = elem_info.get("crud_type", "none")
                priority = elem_info.get("explore_priority", 5)
                
                xpath = tag_to_xpath.get(tag_id) or tag_to_xpath.get(str(tag_id)) or tag_to_xpath.get(int(tag_id) if isinstance(tag_id, str) else tag_id)
                
                elem_type_str = elem_info.get("element_type", "other")
                element = Element(
                    page_id=page_model.id,
                    element_type=ElementType(elem_type_str) if elem_type_str in [e.value for e in ElementType] else ElementType.OTHER,
                    semantic_name=semantic_name,
                    semantic_description=elem_info.get("action_suggestion", ""),
                    text_content=elem_info.get("text_or_hint", ""),
                    importance=elem_info.get("importance", 5),
                    css_selector_hint=str(xpath) if xpath else ""
                )
                element = self.db.save_element(element)
                
                item_key = f"{page_model.id}:{semantic_name}"
                should_explore = (is_nav or is_crud or priority >= 7) and xpath and item_key not in self.visited_items
                
                if should_explore:
                    item_type = "crud" if is_crud else ("nav" if is_nav else "action")
                    self.pending_items.append({
                        "name": semantic_name,
                        "xpath": xpath,
                        "priority": priority,
                        "element_id": element.id,
                        "source_page_id": page_model.id,
                        "source_url": current_url,
                        "item_type": item_type,
                        "crud_type": crud_type,
                        "text": elem_info.get("text_or_hint", "")
                    })
                    
                    if is_nav:
                        nav_count += 1
                    elif is_crud:
                        crud_count += 1
            
            if nav_count > 0 or crud_count > 0:
                print(f"   📊 收集: {nav_count} 个导航项, {crud_count} 个 CRUD 操作")
            
            self.pending_items.sort(key=lambda x: (
                10 if x["item_type"] == "nav" else 
                9 if x["crud_type"] == "create" else
                8 if x["crud_type"] in ("read", "update") else
                7 if x["crud_type"] == "delete" else
                x["priority"]
            ), reverse=True)
        
        await self.page_tagger.cleanup(page)
    
    async def _explore_all_items(self) -> None:
        """探索所有收集到的项目"""
        explored_count = 0
        max_items = self.config.exploration.max_pages * 3
        
        while self.pending_items and explored_count < max_items:
            item = self.pending_items.pop(0)
            item_name = item["name"]
            item_key = f"{item['source_page_id']}:{item_name}"
            
            if item_key in self.visited_items:
                continue
            
            self.visited_items.add(item_key)
            explored_count += 1
            
            item_type_icon = {
                "nav": "🧭",
                "crud": "🔧",
                "action": "📌"
            }.get(item["item_type"], "📌")
            
            print(f"\n{'─'*50}")
            print(f"{item_type_icon} [{explored_count}/{max_items}] 探索: {item_name}")
            if item["crud_type"] != "none":
                print(f"   类型: {item['crud_type'].upper()}")
            print(f"{'─'*50}")
            
            await self._ensure_on_source_page(item)
            success = await self._click_item(item)
            
            if success:
                await asyncio.sleep(2)
                await self._analyze_after_click(item)
    
    async def _ensure_on_source_page(self, item: Dict) -> None:
        """确保当前在源页面上"""
        page = self.browser_manager.page
        source_url = item.get("source_url", "")
        current_url = page.url
        
        if source_url and self._normalize_url(current_url) != self._normalize_url(source_url):
            print(f"   📍 返回源页面: {source_url[:50]}...")
            await self.browser_manager.goto(source_url)
            await asyncio.sleep(2)
    
    async def _click_item(self, item: Dict) -> bool:
        """点击项目"""
        page = self.browser_manager.page
        xpath = item["xpath"]
        
        try:
            await self.page_tagger.cleanup(page)
            
            elem = page.locator(f"xpath={xpath}").first
            
            try:
                visible = await elem.is_visible(timeout=3000)
            except Exception:
                visible = False
            
            if not visible:
                print(f"   ⚠️ 元素不可见，尝试重新定位...")
                text = item.get("text") or item["name"]
                elem = page.get_by_text(text, exact=False).first
            
            await elem.click(timeout=5000)
            print(f"   ✓ 点击成功")
            return True
            
        except Exception as e:
            print(f"   ❌ 点击失败: {str(e)[:60]}")
            return False
    
    async def _analyze_after_click(self, source_item: Dict) -> None:
        """分析点击后的页面/弹窗"""
        page = self.browser_manager.page
        current_url = page.url
        url_key = self._normalize_url(current_url)
        
        has_modal = await self._check_for_modal()
        
        is_new_page = url_key not in self.visited_urls
        if is_new_page:
            self.visited_urls.add(url_key)
        
        print(f"   📄 当前状态: {'弹窗' if has_modal else '页面'} - {current_url[:60]}...")
        
        screenshot = await self.browser_manager.screenshot()
        page_info = await self.page_analyzer.analyze_page(screenshot)
        
        page_type_str = page_info.get("page_type", "unknown")
        page_desc = page_info.get("page_description", "未知")
        print(f"   类型: {page_type_str}")
        print(f"   描述: {page_desc}")
        
        title = await page.title()
        page_model = PageModel(
            site_id=self.current_site.id,
            url_pattern=url_key + ("#modal" if has_modal else ""),
            title_pattern=title,
            page_type=PageType(page_type_str) if page_type_str in [e.value for e in PageType] else PageType.UNKNOWN,
            semantic_description=page_desc,
            key_features=json.dumps(page_info.get("key_features", []), ensure_ascii=False),
            sample_url=current_url,
            visit_count=1
        )
        page_model = self.db.save_page(page_model)
        
        screenshot_path = os.path.join(
            self.config.exploration.screenshot_dir,
            f"{self.session_id}_{page_model.id}.png"
        )
        with open(screenshot_path, "wb") as f:
            f.write(screenshot)
        
        action_type = ActionType.CLICK
        action = Action(
            site_id=self.current_site.id,
            source_page_id=source_item["source_page_id"],
            element_id=source_item["element_id"],
            action_type=action_type,
            target_page_id=page_model.id,
            notes=f"{source_item['item_type'].upper()}: {source_item['name']} ({source_item['crud_type']})"
        )
        self.db.save_action(action)
        
        self.db.save_exploration_log(ExplorationLog(
            site_id=self.current_site.id,
            session_id=self.session_id,
            page_id=page_model.id,
            action_taken=f"{source_item['item_type'].upper()}: {source_item['name']}",
            result=f"{'弹窗' if has_modal else '页面'}: {title}",
            screenshot_path=screenshot_path
        ))
        
        if is_new_page or has_modal:
            print("   🏷️ 分析页面元素...")
            tagged_screenshot, tag_to_xpath = await self.page_tagger.tag_page(page)
            
            if tagged_screenshot and tag_to_xpath:
                elements_info = await self.page_analyzer.analyze_elements(
                    tagged_screenshot,
                    page_desc
                )
                
                new_items = 0
                for elem_info in elements_info:
                    tag_id = elem_info.get("tag_id")
                    if tag_id is None:
                        continue
                    
                    semantic_name = elem_info.get("semantic_name", "")
                    is_nav = elem_info.get("is_nav_menu", False)
                    is_crud = elem_info.get("is_crud_action", False)
                    crud_type = elem_info.get("crud_type", "none")
                    priority = elem_info.get("explore_priority", 5)
                    xpath = tag_to_xpath.get(tag_id)
                    
                    elem_type_str = elem_info.get("element_type", "other")
                    element = Element(
                        page_id=page_model.id,
                        element_type=ElementType(elem_type_str) if elem_type_str in [e.value for e in ElementType] else ElementType.OTHER,
                        semantic_name=semantic_name,
                        semantic_description=elem_info.get("action_suggestion", ""),
                        text_content=elem_info.get("text_or_hint", ""),
                        importance=elem_info.get("importance", 5),
                        css_selector_hint=str(xpath) if xpath else ""
                    )
                    element = self.db.save_element(element)
                    
                    item_key = f"{page_model.id}:{semantic_name}"
                    should_explore = (is_nav or is_crud or priority >= 7) and xpath and item_key not in self.visited_items
                    
                    if should_explore:
                        existing = any(n["name"] == semantic_name and n["source_page_id"] == page_model.id 
                                       for n in self.pending_items)
                        if not existing:
                            item_type = "crud" if is_crud else ("nav" if is_nav else "action")
                            self.pending_items.append({
                                "name": semantic_name,
                                "xpath": xpath,
                                "priority": priority,
                                "element_id": element.id,
                                "source_page_id": page_model.id,
                                "source_url": current_url,
                                "item_type": item_type,
                                "crud_type": crud_type,
                                "text": elem_info.get("text_or_hint", "")
                            })
                            new_items += 1
                
                if new_items > 0:
                    print(f"   📌 发现 {new_items} 个新项目")
                    self.pending_items.sort(key=lambda x: x["priority"], reverse=True)
            
            await self.page_tagger.cleanup(page)
        
        if has_modal:
            await self._close_modal()
    
    async def _check_for_modal(self) -> bool:
        """检查页面上是否有弹窗"""
        page = self.browser_manager.page
        
        modal_selectors = [
            ".ant-modal",
            ".el-dialog",
            ".modal",
            "[role='dialog']",
            ".t-dialog",
            ".arco-modal"
        ]
        
        for selector in modal_selectors:
            try:
                elem = page.locator(selector).first
                if await elem.is_visible(timeout=1000):
                    return True
            except Exception:
                continue
        
        return False
    
    async def _close_modal(self) -> None:
        """关闭弹窗"""
        page = self.browser_manager.page
        
        close_selectors = [
            ".ant-modal-close",
            ".el-dialog__close",
            ".modal-close",
            "[aria-label='Close']",
            ".t-dialog__close",
            "button:has-text('取消')",
            "button:has-text('关闭')"
        ]
        
        for selector in close_selectors:
            try:
                elem = page.locator(selector).first
                if await elem.is_visible(timeout=1000):
                    await elem.click()
                    print("   ✓ 关闭弹窗")
                    await asyncio.sleep(0.5)
                    return
            except Exception:
                continue
        
        try:
            await page.keyboard.press("Escape")
            print("   ✓ ESC 关闭弹窗")
        except Exception:
            pass
    
    def _normalize_url(self, url: str) -> str:
        """标准化 URL"""
        parsed = urlparse(url)
        if parsed.fragment:
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}#{parsed.fragment.split('?')[0]}"
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


class MemoryBasedPlanner:
    """基于记忆的任务规划器"""
    
    PLAN_PROMPT = """你是一个网站操作专家。根据用户的任务和网站记忆，规划操作步骤。

## 网站信息
域名: {domain}
已知页面:
{pages}

已知操作路径:
{actions}

已有任务路径:
{task_paths}

## 用户任务
{task}

## 当前页面
URL: {current_url}
描述: {current_page_desc}

请分析任务，返回 JSON 格式的操作计划：
{{
    "can_plan": true/false,
    "confidence": 0.0-1.0,
    "plan": [
        {{
            "step": 1,
            "action_type": "click/type/navigate",
            "target_description": "目标元素描述",
            "action_detail": "具体操作说明",
            "expected_result": "预期结果"
        }}
    ],
    "unknown_steps": ["需要探索才能确定的步骤"]
}}

如果记忆不足以完成任务，设置 can_plan=false 并说明需要探索什么。"""

    def __init__(self, llm_client: VisionLLMClient, db: DatabaseInterface):
        self.llm = llm_client
        self.db = db
    
    async def plan_task(
        self,
        site: Site,
        task: str,
        current_url: str,
        current_page_desc: str
    ) -> Dict:
        """根据记忆规划任务"""
        pages = self.db.get_pages_by_site(site.id)
        pages_desc = "\n".join([
            f"- [{p.page_type.value}] {p.semantic_description} ({p.url_pattern})"
            for p in pages[:20]
        ]) or "暂无记录"
        
        actions_desc_list = []
        for page in pages[:10]:
            actions = self.db.get_actions_from_page(page.id)
            for action in actions[:5]:
                actions_desc_list.append(
                    f"- {page.semantic_description} -> {action.notes}"
                )
        actions_desc = "\n".join(actions_desc_list) or "暂无记录"
        
        task_paths = self.db.get_task_paths_by_site(site.id)
        paths_desc = "\n".join([
            f"- {tp.task_description}"
            for tp in task_paths[:10]
        ]) or "暂无记录"
        
        prompt = self.PLAN_PROMPT.format(
            domain=site.domain,
            pages=pages_desc,
            actions=actions_desc,
            task_paths=paths_desc,
            task=task,
            current_url=current_url,
            current_page_desc=current_page_desc
        )
        
        try:
            response = await self.llm.chat(prompt)
            
            if response:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"规划任务失败: {e}")
        
        return {
            "can_plan": False,
            "confidence": 0.0,
            "plan": [],
            "unknown_steps": ["无法解析规划结果"]
        }
