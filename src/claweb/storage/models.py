"""
数据模型定义 - 网站记忆系统

核心实体:
- Site: 网站信息
- Page: 页面信息（语义特征）
- Element: 元素信息（语义特征）
- Action: 操作记录（元素操作及结果）
- TaskPath: 任务路径（高层任务到操作序列的映射）
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class PageType(Enum):
    """页面类型"""
    LOGIN = "login"
    HOME = "home"
    LIST = "list"
    DETAIL = "detail"
    FORM = "form"
    SEARCH = "search"
    SETTINGS = "settings"
    ERROR = "error"
    AUTH = "auth"
    DASHBOARD = "dashboard"
    UNKNOWN = "unknown"


class ElementType(Enum):
    """元素类型"""
    BUTTON = "button"
    LINK = "link"
    INPUT = "input"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXTAREA = "textarea"
    IMAGE = "image"
    MENU = "menu"
    TAB = "tab"
    ICON = "icon"
    NAV_ITEM = "nav_item"
    OTHER = "other"


class ActionType(Enum):
    """操作类型"""
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    HOVER = "hover"
    SCROLL = "scroll"
    NAVIGATE = "navigate"


@dataclass
class Site:
    """网站信息"""
    id: Optional[int] = None
    domain: str = ""
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Page:
    """页面信息 - 基于语义特征"""
    id: Optional[int] = None
    site_id: int = 0
    url_pattern: str = ""
    title_pattern: str = ""
    page_type: PageType = PageType.UNKNOWN
    semantic_description: str = ""
    key_features: str = ""
    sample_url: str = ""
    visit_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Element:
    """元素信息 - 基于语义特征"""
    id: Optional[int] = None
    page_id: int = 0
    element_type: ElementType = ElementType.OTHER
    semantic_name: str = ""
    semantic_description: str = ""
    text_content: str = ""
    aria_label: str = ""
    placeholder: str = ""
    css_selector_hint: str = ""
    position_hint: str = ""
    importance: int = 5
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Action:
    """操作记录"""
    id: Optional[int] = None
    site_id: int = 0
    source_page_id: int = 0
    element_id: Optional[int] = None
    action_type: ActionType = ActionType.CLICK
    action_params: str = ""
    target_page_id: Optional[int] = None
    success_rate: float = 1.0
    execution_count: int = 1
    avg_duration_ms: int = 0
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskPath:
    """任务路径 - 高层任务到操作序列的映射"""
    id: Optional[int] = None
    site_id: int = 0
    task_description: str = ""
    task_keywords: str = ""
    action_sequence: str = ""
    start_page_id: Optional[int] = None
    end_page_id: Optional[int] = None
    success_count: int = 0
    fail_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExplorationLog:
    """探索日志"""
    id: Optional[int] = None
    site_id: int = 0
    session_id: str = ""
    page_id: Optional[int] = None
    action_taken: str = ""
    result: str = ""
    screenshot_path: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
