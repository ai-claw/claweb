"""
数据模型单元测试
"""

import pytest
from datetime import datetime

from claweb.storage.models import (
    Site, Page, Element, Action, TaskPath,
    PageType, ElementType, ActionType
)


class TestModels:
    """数据模型测试类"""
    
    def test_site_creation(self):
        """测试 Site 模型创建"""
        site = Site(
            domain="example.com",
            name="Example Site",
            description="Test site"
        )
        assert site.domain == "example.com"
        assert site.name == "Example Site"
        assert site.id is None
    
    def test_page_type_enum(self):
        """测试 PageType 枚举"""
        assert PageType.LOGIN.value == "login"
        assert PageType.HOME.value == "home"
        assert PageType.UNKNOWN.value == "unknown"
    
    def test_element_type_enum(self):
        """测试 ElementType 枚举"""
        assert ElementType.BUTTON.value == "button"
        assert ElementType.INPUT.value == "input"
        assert ElementType.LINK.value == "link"
    
    def test_action_type_enum(self):
        """测试 ActionType 枚举"""
        assert ActionType.CLICK.value == "click"
        assert ActionType.TYPE.value == "type"
        assert ActionType.SCROLL.value == "scroll"
    
    def test_page_creation(self):
        """测试 Page 模型创建"""
        page = Page(
            site_id=1,
            url_pattern="/login",
            page_type=PageType.LOGIN,
            semantic_description="登录页面"
        )
        assert page.site_id == 1
        assert page.page_type == PageType.LOGIN
        assert page.visit_count == 0
    
    def test_element_creation(self):
        """测试 Element 模型创建"""
        element = Element(
            page_id=1,
            element_type=ElementType.BUTTON,
            semantic_name="登录按钮",
            importance=9
        )
        assert element.page_id == 1
        assert element.element_type == ElementType.BUTTON
        assert element.importance == 9
    
    def test_task_path_creation(self):
        """测试 TaskPath 模型创建"""
        task = TaskPath(
            site_id=1,
            task_description="搜索产品",
            task_keywords="搜索 产品",
            success_count=5
        )
        assert task.task_description == "搜索产品"
        assert task.success_count == 5
        assert task.fail_count == 0
