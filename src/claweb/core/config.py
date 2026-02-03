"""
Web Agent 配置模块
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    """LLM 配置"""
    api_base: str
    api_key: str
    model: str


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool
    width: int
    height: int


@dataclass
class DatabaseConfig:
    """数据库配置"""
    type: str           # sqlite 或 mysql
    path: str           # SQLite 文件路径
    host: str           # MySQL 主机
    port: int           # MySQL 端口
    user: str           # MySQL 用户名
    password: str       # MySQL 密码
    database: str       # MySQL 数据库名


@dataclass
class ExplorationConfig:
    """探索配置"""
    max_pages: int              # 最大探索页面数
    max_depth: int              # 最大探索深度
    max_actions_per_page: int   # 每页最大探索操作数
    screenshot_dir: str         # 截图保存目录


@dataclass
class Config:
    """应用配置"""
    llm: LLMConfig
    browser: BrowserConfig
    database: DatabaseConfig
    exploration: ExplorationConfig


def load_config() -> Config:
    """加载配置"""
    return Config(
        llm=LLMConfig(
            api_base=os.getenv("LLM_API_BASE", "https://api.openai.com/v1"),
            api_key=os.getenv("LLM_API_KEY", ""),
            model=os.getenv("LLM_MODEL", "gpt-4o"),
        ),
        browser=BrowserConfig(
            headless=os.getenv("HEADLESS", "false").lower() == "true",
            width=int(os.getenv("BROWSER_WIDTH", "1280")),
            height=int(os.getenv("BROWSER_HEIGHT", "800")),
        ),
        database=DatabaseConfig(
            type=os.getenv("DB_TYPE", "sqlite"),
            path=os.getenv("DB_PATH", "web_agent_memory.db"),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "web_agent"),
        ),
        exploration=ExplorationConfig(
            max_pages=int(os.getenv("EXPLORE_MAX_PAGES", "50")),
            max_depth=int(os.getenv("EXPLORE_MAX_DEPTH", "5")),
            max_actions_per_page=int(os.getenv("EXPLORE_MAX_ACTIONS", "10")),
            screenshot_dir=os.getenv("SCREENSHOT_DIR", "screenshots"),
        ),
    )
