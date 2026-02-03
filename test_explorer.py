"""
测试探索器 - 测试 CRUD 操作探索功能
"""

import asyncio
from config import load_config
from browser import BrowserManager
from page_tagger import PageTagger
from llm_client import VisionLLMClient
from explorer import PageAnalyzer, SiteExplorer
from database import create_database


async def test():
    config = load_config()
    
    print("=" * 60)
    print("测试探索器 - CRUD 操作探索")
    print("=" * 60)
    
    # 创建数据库
    db = create_database(config.database)
    
    # 创建探索器
    explorer = SiteExplorer(config, db)
    
    try:
        await explorer.start()
        print("✓ 探索器启动成功")
        
        # 探索测试用例库页面
        url = "https://test.ting.woa.com/15/testing-assets/usecase-lib/#/usecase-lib"
        print(f"\n开始探索: {url}")
        
        site = await explorer.explore_site(url, "Ting测试用例库")
        
        print(f"\n✅ 探索完成!")
        print(f"   网站 ID: {site.id}")
        print(f"   访问页面数: {len(explorer.visited_urls)}")
        print(f"   探索项目数: {len(explorer.visited_items)}")
        
    except Exception as e:
        import traceback
        print(f"\n❌ 错误: {e}")
        traceback.print_exc()
    finally:
        await explorer.stop()
        print("\n✓ 探索器已关闭")


if __name__ == '__main__':
    asyncio.run(test())
