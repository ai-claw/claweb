"""
Web Agent 核心模块 - 带记忆系统
"""
import asyncio
import json
from typing import Optional, Callable, Dict, List
from urllib.parse import urlparse

from config import Config, load_config
from browser import BrowserManager
from llm_client import VisionLLMClient
from page_tagger import PageTagger
from action_executor import ActionExecutor
from database import DatabaseInterface, create_database
from explorer import SiteExplorer, PageAnalyzer, MemoryBasedPlanner
from models import Site, Page, TaskPath, ActionType


class WebAgent:
    """Web 自动化 Agent - 带记忆系统"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or load_config()
        self.browser_manager = BrowserManager(self.config.browser)
        self.llm_client = VisionLLMClient(self.config.llm)
        self.page_tagger = PageTagger()
        self.action_executor: Optional[ActionExecutor] = None
        
        # 记忆系统
        self.db: Optional[DatabaseInterface] = None
        self.current_site: Optional[Site] = None
        self.planner: Optional[MemoryBasedPlanner] = None
        self.page_analyzer: Optional[PageAnalyzer] = None
        
        self._running = False
        self._max_steps = 20
        self._use_memory = True  # 是否使用记忆系统

    async def start(self, use_memory: bool = True) -> None:
        """启动 Agent"""
        self._use_memory = use_memory
        
        page = await self.browser_manager.start()
        self.action_executor = ActionExecutor(page)
        
        if use_memory:
            # 初始化记忆系统
            db_config = {
                'type': self.config.database.type,
                'path': self.config.database.path,
                'host': self.config.database.host,
                'port': self.config.database.port,
                'user': self.config.database.user,
                'password': self.config.database.password,
                'database': self.config.database.database,
            }
            self.db = create_database(db_config)
            self.db.connect()
            self.planner = MemoryBasedPlanner(self.llm_client, self.db)
            self.page_analyzer = PageAnalyzer(self.llm_client)
            print("浏览器已启动（记忆系统已启用）")
        else:
            print("浏览器已启动（无记忆模式）")

    async def stop(self) -> None:
        """停止 Agent"""
        self._running = False
        await self.browser_manager.close()
        if self.db:
            self.db.close()
        print("浏览器已关闭")

    async def goto(self, url: str) -> None:
        """导航到指定 URL"""
        await self.browser_manager.goto(url)
        
        if self._use_memory and self.db:
            # 更新当前网站
            domain = urlparse(url).netloc
            self.current_site = self.db.get_or_create_site(domain)
        
        print(f"已导航到: {url}")

    async def explore(self, url: str, site_name: str = "") -> None:
        """
        探索网站并学习
        
        Args:
            url: 起始 URL
            site_name: 网站名称（可选）
        """
        if not self._use_memory:
            print("错误: 探索功能需要启用记忆系统")
            return
        
        explorer = SiteExplorer(self.config, self.db)
        explorer.browser_manager = self.browser_manager
        
        print(f"\n🔍 开始探索网站: {url}")
        self.current_site = await explorer.explore_site(url, site_name)
        print(f"✅ 探索完成，已记录网站信息")

    async def execute_task(
        self,
        instruction: str,
        on_step: Optional[Callable[[int, str, str], None]] = None,
    ) -> str:
        """
        执行用户指令 - 优先使用记忆
        
        Args:
            instruction: 用户指令
            on_step: 步骤回调函数 (step_number, action, result)
            
        Returns:
            执行结果描述
        """
        self._running = True
        self.llm_client.reset_conversation()
        
        page = self.browser_manager.page
        if not page:
            return "浏览器未启动"
        
        # 尝试使用记忆规划
        plan = None
        if self._use_memory and self.current_site and self.planner:
            print("\n📚 查询记忆中...")
            
            # 获取当前页面信息
            screenshot = await self.browser_manager.screenshot()
            page_info = await self.page_analyzer.analyze_page(screenshot)
            
            plan = await self.planner.plan_task(
                self.current_site,
                instruction,
                page.url,
                page_info.get("page_description", "")
            )
            
            if plan.get("can_plan") and plan.get("confidence", 0) > 0.6:
                print(f"✅ 找到相关记忆，置信度: {plan.get('confidence', 0):.0%}")
                print("📋 规划的步骤:")
                for step in plan.get("plan", []):
                    print(f"   {step['step']}. {step['action_detail']}")
                
                # 按规划执行
                return await self._execute_with_plan(plan, instruction, on_step)
            else:
                print("❌ 记忆不足，使用实时分析模式")
                if plan.get("unknown_steps"):
                    print(f"   需要探索: {plan.get('unknown_steps')}")
        
        # 无记忆或记忆不足，使用原有的实时分析模式
        return await self._execute_without_memory(instruction, on_step)

    async def _execute_with_plan(
        self,
        plan: Dict,
        instruction: str,
        on_step: Optional[Callable[[int, str, str], None]] = None
    ) -> str:
        """按照记忆规划执行任务"""
        steps = plan.get("plan", [])
        
        for step_info in steps:
            step_num = step_info.get("step", 0)
            action_type = step_info.get("action_type", "click")
            target_desc = step_info.get("target_description", "")
            action_detail = step_info.get("action_detail", "")
            
            print(f"\n[步骤 {step_num}] {action_detail}")
            
            page = self.browser_manager.page
            screenshot = await self.browser_manager.screenshot()
            page_text, tag_to_xpath = await self.page_tagger.tag_page(page)
            
            # 让 LLM 根据目标描述找到具体元素
            find_element_prompt = f"""当前页面元素:
{page_text}

我需要执行: {action_detail}
目标元素描述: {target_desc}

请输出要执行的操作命令（只输出一个命令）:
- CLICK [ID] - 点击
- TYPE [ID] "文本" - 输入
- 如果找不到目标元素，输出 FAIL"""

            action = await self.llm_client.chat(find_element_prompt)
            print(f"   LLM: {action}")
            
            if "FAIL" in action.upper():
                print(f"   ⚠️ 找不到目标元素，切换到实时分析模式")
                return await self._execute_without_memory(instruction, on_step)
            
            done, result = await self.action_executor.execute(action, tag_to_xpath)
            print(f"   结果: {result}")
            
            if on_step:
                on_step(step_num, action, result)
            
            if done:
                # 记录成功的任务路径
                if self.db and self.current_site:
                    self._record_successful_task(instruction, plan)
                return f"任务完成，共执行 {step_num} 步（使用记忆）"
            
            await asyncio.sleep(0.5)
        
        return f"按计划执行完成 {len(steps)} 步"

    async def _execute_without_memory(
        self,
        instruction: str,
        on_step: Optional[Callable[[int, str, str], None]] = None
    ) -> str:
        """无记忆模式执行任务（原有逻辑）"""
        step = 0
        action_history = []  # 记录操作历史

        while self._running and step < self._max_steps:
            step += 1

            page = self.browser_manager.page
            if not page:
                return "浏览器未启动"

            current_url = page.url
            screenshot = await self.browser_manager.screenshot()
            page_text, tag_to_xpath = await self.page_tagger.tag_page(page)

            action = self.llm_client.analyze_page(
                screenshot=screenshot,
                page_text=page_text,
                user_instruction=instruction,
                current_url=current_url,
            )

            print(f"\n[步骤 {step}] LLM 返回: {action}")

            done, result = await self.action_executor.execute(action, tag_to_xpath)

            print(f"[步骤 {step}] 执行结果: {result}")
            
            # 记录操作
            action_history.append({
                "step": step,
                "url": current_url,
                "action": action,
                "result": result
            })

            if on_step:
                on_step(step, action, result)

            if done:
                # 记录成功的任务路径
                if self._use_memory and self.db and self.current_site:
                    self._record_task_from_history(instruction, action_history)
                return f"任务完成，共执行 {step} 步"

            await asyncio.sleep(0.5)

        return f"达到最大步数 {self._max_steps}，任务未完成"

    def _record_successful_task(self, instruction: str, plan: Dict) -> None:
        """记录成功的任务（从规划执行）"""
        try:
            task_path = TaskPath(
                site_id=self.current_site.id,
                task_description=instruction,
                task_keywords=" ".join(instruction.split()),
                action_sequence=json.dumps(plan.get("plan", []), ensure_ascii=False),
                success_count=1
            )
            self.db.save_task_path(task_path)
        except Exception as e:
            print(f"记录任务路径失败: {e}")

    def _record_task_from_history(self, instruction: str, history: List[Dict]) -> None:
        """从操作历史记录任务路径"""
        try:
            task_path = TaskPath(
                site_id=self.current_site.id,
                task_description=instruction,
                task_keywords=" ".join(instruction.split()),
                action_sequence=json.dumps(history, ensure_ascii=False),
                success_count=1
            )
            self.db.save_task_path(task_path)
            print("📝 已记录新的任务路径")
        except Exception as e:
            print(f"记录任务路径失败: {e}")

    def show_memory_stats(self) -> None:
        """显示记忆统计"""
        if not self.db or not self.current_site:
            print("无记忆数据")
            return
        
        pages = self.db.get_pages_by_site(self.current_site.id)
        task_paths = self.db.get_task_paths_by_site(self.current_site.id)
        
        print(f"\n📊 网站记忆统计: {self.current_site.domain}")
        print(f"   已知页面: {len(pages)} 个")
        print(f"   任务路径: {len(task_paths)} 条")
        
        if pages:
            print("\n   页面列表:")
            for p in pages[:10]:
                print(f"   - [{p.page_type.value}] {p.semantic_description[:40]}")
        
        if task_paths:
            print("\n   已学会的任务:")
            for t in task_paths[:5]:
                print(f"   - {t.task_description}")

    async def run_interactive(self) -> None:
        """交互式运行"""
        print("\n=== Web Agent 交互模式（带记忆）===")
        print("命令:")
        print("  goto <url>  - 导航到指定网址")
        print("  explore     - 探索当前网站并学习")
        print("  do <指令>   - 执行自然语言指令（自动使用记忆）")
        print("  memory      - 显示当前网站的记忆统计")
        print("  screenshot  - 保存当前截图")
        print("  wait        - 等待你手动操作浏览器（如登录验证）")
        print("  quit        - 退出")
        print("=" * 50)

        while True:
            try:
                user_input = input("\n> ").strip()
                if not user_input:
                    continue

                if user_input.lower() == "quit":
                    break

                if user_input.lower().startswith("goto "):
                    url = user_input[5:].strip()
                    await self.goto(url)

                elif user_input.lower() == "explore":
                    page = self.browser_manager.page
                    if page:
                        site_name = input("网站名称（可选，直接回车跳过）: ").strip()
                        await self.explore(page.url, site_name)
                    else:
                        print("请先使用 goto 命令打开一个网站")

                elif user_input.lower().startswith("do "):
                    instruction = user_input[3:].strip()
                    result = await self.execute_task(instruction)
                    print(f"\n结果: {result}")

                elif user_input.lower() == "memory":
                    self.show_memory_stats()

                elif user_input.lower() == "screenshot":
                    screenshot = await self.browser_manager.screenshot()
                    with open("screenshot.png", "wb") as f:
                        f.write(screenshot)
                    print("截图已保存到 screenshot.png")

                elif user_input.lower() == "wait":
                    print("请在浏览器中完成操作（如登录验证）...")
                    input("完成后按 Enter 继续...")
                    print("继续")

                else:
                    print("未知命令，请使用 goto/explore/do/memory/screenshot/wait/quit")

            except KeyboardInterrupt:
                print("\n中断")
                break
            except Exception as e:
                print(f"错误: {e}")
                import traceback
                traceback.print_exc()
