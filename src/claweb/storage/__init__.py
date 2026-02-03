"""
存储模块 - 数据库和模型
"""

from claweb.storage.models import (
    Site, Page, Element, Action, TaskPath, ExplorationLog,
    PageType, ElementType, ActionType
)
from claweb.storage.database import (
    DatabaseInterface, SQLiteDatabase, MySQLDatabase, create_database
)

__all__ = [
    # Models
    "Site",
    "Page", 
    "Element",
    "Action",
    "TaskPath",
    "ExplorationLog",
    "PageType",
    "ElementType",
    "ActionType",
    # Database
    "DatabaseInterface",
    "SQLiteDatabase",
    "MySQLDatabase",
    "create_database",
]
