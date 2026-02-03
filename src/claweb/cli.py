#!/usr/bin/env python3
"""
Claweb CLI - 命令行入口
"""

import asyncio
import argparse
import sys

from claweb.core.agent import WebAgent
from claweb.core.config import load_config


def main():
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        description="Claweb - 基于 Tarsier 的智能 Web 自动化 Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  claweb --url https://example.com              # 交互模式
  claweb --url https://example.com --explore    # 探索模式
  claweb --url https://example.com --task "搜索产品"  # 任务模式
        """
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="启动时导航到的 URL",
    )
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="要执行的任务指令（非交互模式）",
    )
    parser.add_argument(
        "--explore",
        action="store_true",
        help="探索模式：自动探索网站并学习",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="禁用记忆系统",
    )
    parser.add_argument(
        "--site-name",
        type=str,
        default="",
        help="网站名称（用于探索模式）",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    args = parser.parse_args()

    config = load_config()
    if not config.llm.api_key:
        print("错误: 请在 .env 文件中配置 LLM_API_KEY")
        print("可参考 .env.example 创建 .env 文件")
        sys.exit(1)

    asyncio.run(run_agent(args, config))


async def run_agent(args, config):
    """运行 Agent"""
    agent = WebAgent(config)
    use_memory = not args.no_memory

    try:
        await agent.start(use_memory=use_memory)

        if args.url:
            await agent.goto(args.url)
        
        if args.explore:
            if not args.url:
                print("错误: 探索模式需要指定 --url")
                sys.exit(1)
            await agent.explore(args.url, args.site_name)
            agent.show_memory_stats()
        elif args.task:
            result = await agent.execute_task(args.task)
            print(f"\n执行结果: {result}")
        else:
            await agent.run_interactive()

    finally:
        await agent.stop()


if __name__ == "__main__":
    main()
