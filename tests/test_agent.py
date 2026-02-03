"""
Agent 单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from claweb.core.config import Config, LLMConfig, BrowserConfig, DatabaseConfig, ExplorationConfig


@pytest.fixture
def mock_config():
    """创建测试配置"""
    return Config(
        llm=LLMConfig(
            api_base="https://api.test.com",
            api_key="test-key",
            model="gpt-4o"
        ),
        browser=BrowserConfig(
            headless=True,
            width=1280,
            height=800
        ),
        database=DatabaseConfig(
            type="sqlite",
            path=":memory:",
            host="localhost",
            port=3306,
            user="root",
            password="",
            database="test"
        ),
        exploration=ExplorationConfig(
            max_pages=10,
            max_depth=3,
            max_actions_per_page=5,
            screenshot_dir="/tmp/screenshots"
        )
    )


class TestWebAgent:
    """WebAgent 测试类"""
    
    def test_config_creation(self, mock_config):
        """测试配置创建"""
        assert mock_config.llm.api_key == "test-key"
        assert mock_config.browser.headless is True
        assert mock_config.database.type == "sqlite"
