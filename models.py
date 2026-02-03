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
    LOGIN = "login"           # 登录页
    HOME = "home"             # 首页
    LIST = "list"             # 列表页
    DETAIL = "detail"         # 详情页
    FORM = "form"             # 表单页
    SEARCH = "search"         # 搜索页
    SETTINGS = "settings"     # 设置页
    ERROR = "error"           # 错误页
    AUTH = "auth"             # 认证页（验证码、二维码等）
    UNKNOWN = "unknown"       # 未知


class ElementType(Enum):
    """元素类型"""
    BUTTON = "button"         # 按钮
    LINK = "link"             # 链接
    INPUT = "input"           # 输入框
    SELECT = "select"         # 下拉选择
    CHECKBOX = "checkbox"     # 复选框
    RADIO = "radio"           # 单选框
    TEXTAREA = "textarea"     # 文本域
    IMAGE = "image"           # 图片
    MENU = "menu"             # 菜单项
    TAB = "tab"               # 标签页
    ICON = "icon"             # 图标按钮
    OTHER = "other"           # 其他


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
    domain: str = ""                    # 域名
    name: str = ""                      # 网站名称
    description: str = ""               # 网站描述
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Page:
    """页面信息 - 基于语义特征"""
    id: Optional[int] = None
    site_id: int = 0
    url_pattern: str = ""               # URL 模式（正则或通配符）
    title_pattern: str = ""             # 标题模式
    page_type: PageType = PageType.UNKNOWN
    semantic_description: str = ""      # 页面语义描述（LLM 生成）
    key_features: str = ""              # 关键特征（JSON: 导航栏、表单、列表等）
    sample_url: str = ""                # 示例 URL
    visit_count: int = 0                # 访问次数
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Element:
    """元素信息 - 基于语义特征"""
    id: Optional[int] = None
    page_id: int = 0
    element_type: ElementType = ElementType.OTHER
    semantic_name: str = ""             # 语义名称（如"登录按钮"、"用户名输入框"）
    semantic_description: str = ""      # 语义描述
    text_content: str = ""              # 元素文本内容
    aria_label: str = ""                # aria-label 属性
    placeholder: str = ""               # placeholder 属性
    css_selector_hint: str = ""         # CSS 选择器提示（非精确，用于辅助定位）
    position_hint: str = ""             # 位置提示（如"页面顶部导航栏"）
    importance: int = 5                 # 重要性 1-10
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Action:
    """操作记录"""
    id: Optional[int] = None
    site_id: int = 0
    source_page_id: int = 0             # 源页面
    element_id: Optional[int] = None    # 操作的元素
    action_type: ActionType = ActionType.CLICK
    action_params: str = ""             # 操作参数（JSON，如输入的文本）
    target_page_id: Optional[int] = None  # 目标页面（操作后跳转到的页面）
    success_rate: float = 1.0           # 成功率
    execution_count: int = 1            # 执行次数
    avg_duration_ms: int = 0            # 平均执行时间
    notes: str = ""                     # 备注
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskPath:
    """任务路径 - 高层任务到操作序列的映射"""
    id: Optional[int] = None
    site_id: int = 0
    task_description: str = ""          # 任务描述（自然语言）
    task_keywords: str = ""             # 任务关键词（用于匹配）
    action_sequence: str = ""           # 操作序列（JSON: [action_id, action_id, ...]）
    start_page_id: Optional[int] = None # 起始页面
    end_page_id: Optional[int] = None   # 结束页面
    success_count: int = 0              # 成功次数
    fail_count: int = 0                 # 失败次数
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExplorationLog:
    """探索日志"""
    id: Optional[int] = None
    site_id: int = 0
    session_id: str = ""                # 探索会话 ID
    page_id: Optional[int] = None
    action_taken: str = ""              # 执行的操作
    result: str = ""                    # 操作结果
    screenshot_path: str = ""           # 截图路径
    timestamp: datetime = field(default_factory=datetime.now)
