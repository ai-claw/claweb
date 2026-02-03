"""
Claweb - 基于 Tarsier 的智能 Web 自动化 Agent

一个基于视觉 LLM 和 Tarsier 的 Web 自动化框架，支持：
- 智能页面元素识别和标记
- 自然语言任务执行
- 网站自动探索和记忆学习
"""

__version__ = "0.1.0"
__author__ = "AI-Claw Team"

from claweb.core.agent import WebAgent
from claweb.core.config import Config, load_config

__all__ = [
    "WebAgent",
    "Config",
    "load_config",
    "__version__",
]
