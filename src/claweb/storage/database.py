"""
数据库抽象层 - 支持 SQLite 和 MySQL
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
from urllib.parse import urlparse

from claweb.storage.models import (
    Site, Page, Element, Action, TaskPath, ExplorationLog,
    PageType, ElementType, ActionType
)


class DatabaseInterface(ABC):
    """数据库接口抽象类"""
    
    @abstractmethod
    def connect(self) -> None:
        pass
    
    @abstractmethod
    def close(self) -> None:
        pass
    
    @abstractmethod
    def init_schema(self) -> None:
        pass
    
    @abstractmethod
    def get_or_create_site(self, domain: str, name: str = "", description: str = "") -> Site:
        pass
    
    @abstractmethod
    def get_site_by_domain(self, domain: str) -> Optional[Site]:
        pass
    
    @abstractmethod
    def save_page(self, page: Page) -> Page:
        pass
    
    @abstractmethod
    def get_page_by_url(self, site_id: int, url: str) -> Optional[Page]:
        pass
    
    @abstractmethod
    def get_pages_by_site(self, site_id: int) -> List[Page]:
        pass
    
    @abstractmethod
    def find_similar_page(self, site_id: int, url: str, title: str) -> Optional[Page]:
        pass
    
    @abstractmethod
    def save_element(self, element: Element) -> Element:
        pass
    
    @abstractmethod
    def get_elements_by_page(self, page_id: int) -> List[Element]:
        pass
    
    @abstractmethod
    def find_element_by_semantic(self, page_id: int, semantic_name: str) -> Optional[Element]:
        pass
    
    @abstractmethod
    def save_action(self, action: Action) -> Action:
        pass
    
    @abstractmethod
    def get_actions_from_page(self, page_id: int) -> List[Action]:
        pass
    
    @abstractmethod
    def get_action_to_page(self, source_page_id: int, target_page_id: int) -> Optional[Action]:
        pass
    
    @abstractmethod
    def save_task_path(self, task_path: TaskPath) -> TaskPath:
        pass
    
    @abstractmethod
    def find_task_path(self, site_id: int, task_description: str) -> Optional[TaskPath]:
        pass
    
    @abstractmethod
    def get_task_paths_by_site(self, site_id: int) -> List[TaskPath]:
        pass
    
    @abstractmethod
    def save_exploration_log(self, log: ExplorationLog) -> ExplorationLog:
        pass


class SQLiteDatabase(DatabaseInterface):
    """SQLite 数据库实现"""
    
    def __init__(self, db_path: str = "web_agent_memory.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self) -> None:
        import sqlite3
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.init_schema()
    
    def close(self) -> None:
        if self.conn:
            self.conn.close()
    
    def init_schema(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            url_pattern TEXT NOT NULL,
            title_pattern TEXT DEFAULT '',
            page_type TEXT DEFAULT 'unknown',
            semantic_description TEXT DEFAULT '',
            key_features TEXT DEFAULT '{}',
            sample_url TEXT DEFAULT '',
            visit_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        );
        
        CREATE TABLE IF NOT EXISTS elements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL,
            element_type TEXT DEFAULT 'other',
            semantic_name TEXT NOT NULL,
            semantic_description TEXT DEFAULT '',
            text_content TEXT DEFAULT '',
            aria_label TEXT DEFAULT '',
            placeholder TEXT DEFAULT '',
            css_selector_hint TEXT DEFAULT '',
            position_hint TEXT DEFAULT '',
            importance INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (page_id) REFERENCES pages(id)
        );
        
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            source_page_id INTEGER NOT NULL,
            element_id INTEGER,
            action_type TEXT NOT NULL,
            action_params TEXT DEFAULT '{}',
            target_page_id INTEGER,
            success_rate REAL DEFAULT 1.0,
            execution_count INTEGER DEFAULT 1,
            avg_duration_ms INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id),
            FOREIGN KEY (source_page_id) REFERENCES pages(id),
            FOREIGN KEY (element_id) REFERENCES elements(id),
            FOREIGN KEY (target_page_id) REFERENCES pages(id)
        );
        
        CREATE TABLE IF NOT EXISTS task_paths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            task_description TEXT NOT NULL,
            task_keywords TEXT DEFAULT '',
            action_sequence TEXT DEFAULT '[]',
            start_page_id INTEGER,
            end_page_id INTEGER,
            success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        );
        
        CREATE TABLE IF NOT EXISTS exploration_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            page_id INTEGER,
            action_taken TEXT DEFAULT '',
            result TEXT DEFAULT '',
            screenshot_path TEXT DEFAULT '',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_pages_site ON pages(site_id);
        CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(url_pattern);
        CREATE INDEX IF NOT EXISTS idx_elements_page ON elements(page_id);
        CREATE INDEX IF NOT EXISTS idx_elements_semantic ON elements(semantic_name);
        CREATE INDEX IF NOT EXISTS idx_actions_source ON actions(source_page_id);
        CREATE INDEX IF NOT EXISTS idx_task_paths_site ON task_paths(site_id);
        """
        self.cursor.executescript(schema)
        self.conn.commit()
    
    def get_or_create_site(self, domain: str, name: str = "", description: str = "") -> Site:
        self.cursor.execute("SELECT * FROM sites WHERE domain = ?", (domain,))
        row = self.cursor.fetchone()
        if row:
            return Site(
                id=row['id'],
                domain=row['domain'],
                name=row['name'],
                description=row['description'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.now()
            )
        
        self.cursor.execute(
            "INSERT INTO sites (domain, name, description) VALUES (?, ?, ?)",
            (domain, name or domain, description)
        )
        self.conn.commit()
        return Site(
            id=self.cursor.lastrowid,
            domain=domain,
            name=name or domain,
            description=description
        )
    
    def get_site_by_domain(self, domain: str) -> Optional[Site]:
        self.cursor.execute("SELECT * FROM sites WHERE domain = ?", (domain,))
        row = self.cursor.fetchone()
        if not row:
            return None
        return Site(
            id=row['id'],
            domain=row['domain'],
            name=row['name'],
            description=row['description']
        )
    
    def save_page(self, page: Page) -> Page:
        if page.id:
            self.cursor.execute("""
                UPDATE pages SET 
                    url_pattern=?, title_pattern=?, page_type=?, semantic_description=?,
                    key_features=?, sample_url=?, visit_count=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (
                page.url_pattern, page.title_pattern, page.page_type.value,
                page.semantic_description, page.key_features, page.sample_url,
                page.visit_count, page.id
            ))
        else:
            self.cursor.execute("""
                INSERT INTO pages (site_id, url_pattern, title_pattern, page_type, 
                    semantic_description, key_features, sample_url, visit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                page.site_id, page.url_pattern, page.title_pattern, page.page_type.value,
                page.semantic_description, page.key_features, page.sample_url, page.visit_count
            ))
            page.id = self.cursor.lastrowid
        self.conn.commit()
        return page
    
    def get_page_by_url(self, site_id: int, url: str) -> Optional[Page]:
        parsed = urlparse(url)
        url_base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        self.cursor.execute("""
            SELECT * FROM pages WHERE site_id = ? AND (url_pattern = ? OR sample_url = ?)
        """, (site_id, url_base, url))
        row = self.cursor.fetchone()
        if not row:
            return None
        return self._row_to_page(row)
    
    def get_pages_by_site(self, site_id: int) -> List[Page]:
        self.cursor.execute("SELECT * FROM pages WHERE site_id = ?", (site_id,))
        return [self._row_to_page(row) for row in self.cursor.fetchall()]
    
    def find_similar_page(self, site_id: int, url: str, title: str) -> Optional[Page]:
        self.cursor.execute("SELECT * FROM pages WHERE site_id = ?", (site_id,))
        for row in self.cursor.fetchall():
            page = self._row_to_page(row)
            if self._url_matches_pattern(url, page.url_pattern):
                return page
            if title and page.title_pattern and title.lower() in page.title_pattern.lower():
                return page
        return None
    
    def _url_matches_pattern(self, url: str, pattern: str) -> bool:
        if not pattern:
            return False
        parsed_url = urlparse(url)
        parsed_pattern = urlparse(pattern)
        
        url_parts = parsed_url.path.strip('/').split('/')
        pattern_parts = parsed_pattern.path.strip('/').split('/')
        
        if len(url_parts) != len(pattern_parts):
            return False
        
        for u, p in zip(url_parts, pattern_parts):
            if p == '*' or p == u:
                continue
            if u.isdigit() and p.isdigit():
                continue
            return False
        return True
    
    def _row_to_page(self, row) -> Page:
        return Page(
            id=row['id'],
            site_id=row['site_id'],
            url_pattern=row['url_pattern'],
            title_pattern=row['title_pattern'],
            page_type=PageType(row['page_type']) if row['page_type'] else PageType.UNKNOWN,
            semantic_description=row['semantic_description'],
            key_features=row['key_features'],
            sample_url=row['sample_url'],
            visit_count=row['visit_count']
        )
    
    def save_element(self, element: Element) -> Element:
        if element.id:
            self.cursor.execute("""
                UPDATE elements SET 
                    element_type=?, semantic_name=?, semantic_description=?, text_content=?,
                    aria_label=?, placeholder=?, css_selector_hint=?, position_hint=?, importance=?
                WHERE id=?
            """, (
                element.element_type.value, element.semantic_name, element.semantic_description,
                element.text_content, element.aria_label, element.placeholder,
                element.css_selector_hint, element.position_hint, element.importance, element.id
            ))
        else:
            self.cursor.execute("""
                INSERT INTO elements (page_id, element_type, semantic_name, semantic_description,
                    text_content, aria_label, placeholder, css_selector_hint, position_hint, importance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                element.page_id, element.element_type.value, element.semantic_name,
                element.semantic_description, element.text_content, element.aria_label,
                element.placeholder, element.css_selector_hint, element.position_hint, element.importance
            ))
            element.id = self.cursor.lastrowid
        self.conn.commit()
        return element
    
    def get_elements_by_page(self, page_id: int) -> List[Element]:
        self.cursor.execute("SELECT * FROM elements WHERE page_id = ?", (page_id,))
        return [self._row_to_element(row) for row in self.cursor.fetchall()]
    
    def find_element_by_semantic(self, page_id: int, semantic_name: str) -> Optional[Element]:
        self.cursor.execute("""
            SELECT * FROM elements WHERE page_id = ? AND 
            (semantic_name LIKE ? OR semantic_description LIKE ?)
        """, (page_id, f"%{semantic_name}%", f"%{semantic_name}%"))
        row = self.cursor.fetchone()
        return self._row_to_element(row) if row else None
    
    def _row_to_element(self, row) -> Element:
        return Element(
            id=row['id'],
            page_id=row['page_id'],
            element_type=ElementType(row['element_type']) if row['element_type'] else ElementType.OTHER,
            semantic_name=row['semantic_name'],
            semantic_description=row['semantic_description'],
            text_content=row['text_content'],
            aria_label=row['aria_label'],
            placeholder=row['placeholder'],
            css_selector_hint=row['css_selector_hint'],
            position_hint=row['position_hint'],
            importance=row['importance']
        )
    
    def save_action(self, action: Action) -> Action:
        if action.id:
            self.cursor.execute("""
                UPDATE actions SET 
                    element_id=?, action_type=?, action_params=?, target_page_id=?,
                    success_rate=?, execution_count=?, avg_duration_ms=?, notes=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (
                action.element_id, action.action_type.value, action.action_params,
                action.target_page_id, action.success_rate, action.execution_count,
                action.avg_duration_ms, action.notes, action.id
            ))
        else:
            self.cursor.execute("""
                INSERT INTO actions (site_id, source_page_id, element_id, action_type,
                    action_params, target_page_id, success_rate, execution_count, avg_duration_ms, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                action.site_id, action.source_page_id, action.element_id, action.action_type.value,
                action.action_params, action.target_page_id, action.success_rate,
                action.execution_count, action.avg_duration_ms, action.notes
            ))
            action.id = self.cursor.lastrowid
        self.conn.commit()
        return action
    
    def get_actions_from_page(self, page_id: int) -> List[Action]:
        self.cursor.execute("SELECT * FROM actions WHERE source_page_id = ?", (page_id,))
        return [self._row_to_action(row) for row in self.cursor.fetchall()]
    
    def get_action_to_page(self, source_page_id: int, target_page_id: int) -> Optional[Action]:
        self.cursor.execute("""
            SELECT * FROM actions WHERE source_page_id = ? AND target_page_id = ?
        """, (source_page_id, target_page_id))
        row = self.cursor.fetchone()
        return self._row_to_action(row) if row else None
    
    def _row_to_action(self, row) -> Action:
        return Action(
            id=row['id'],
            site_id=row['site_id'],
            source_page_id=row['source_page_id'],
            element_id=row['element_id'],
            action_type=ActionType(row['action_type']) if row['action_type'] else ActionType.CLICK,
            action_params=row['action_params'],
            target_page_id=row['target_page_id'],
            success_rate=row['success_rate'],
            execution_count=row['execution_count'],
            avg_duration_ms=row['avg_duration_ms'],
            notes=row['notes']
        )
    
    def save_task_path(self, task_path: TaskPath) -> TaskPath:
        if task_path.id:
            self.cursor.execute("""
                UPDATE task_paths SET 
                    task_description=?, task_keywords=?, action_sequence=?,
                    start_page_id=?, end_page_id=?, success_count=?, fail_count=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (
                task_path.task_description, task_path.task_keywords, task_path.action_sequence,
                task_path.start_page_id, task_path.end_page_id, task_path.success_count,
                task_path.fail_count, task_path.id
            ))
        else:
            self.cursor.execute("""
                INSERT INTO task_paths (site_id, task_description, task_keywords, action_sequence,
                    start_page_id, end_page_id, success_count, fail_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_path.site_id, task_path.task_description, task_path.task_keywords,
                task_path.action_sequence, task_path.start_page_id, task_path.end_page_id,
                task_path.success_count, task_path.fail_count
            ))
            task_path.id = self.cursor.lastrowid
        self.conn.commit()
        return task_path
    
    def find_task_path(self, site_id: int, task_description: str) -> Optional[TaskPath]:
        keywords = task_description.lower().split()
        self.cursor.execute("SELECT * FROM task_paths WHERE site_id = ?", (site_id,))
        
        best_match = None
        best_score = 0
        
        for row in self.cursor.fetchall():
            task_path = self._row_to_task_path(row)
            score = sum(1 for kw in keywords if kw in task_path.task_keywords.lower())
            if score > best_score:
                best_score = score
                best_match = task_path
        
        return best_match if best_score > 0 else None
    
    def get_task_paths_by_site(self, site_id: int) -> List[TaskPath]:
        self.cursor.execute("SELECT * FROM task_paths WHERE site_id = ?", (site_id,))
        return [self._row_to_task_path(row) for row in self.cursor.fetchall()]
    
    def _row_to_task_path(self, row) -> TaskPath:
        return TaskPath(
            id=row['id'],
            site_id=row['site_id'],
            task_description=row['task_description'],
            task_keywords=row['task_keywords'],
            action_sequence=row['action_sequence'],
            start_page_id=row['start_page_id'],
            end_page_id=row['end_page_id'],
            success_count=row['success_count'],
            fail_count=row['fail_count']
        )
    
    def save_exploration_log(self, log: ExplorationLog) -> ExplorationLog:
        self.cursor.execute("""
            INSERT INTO exploration_logs (site_id, session_id, page_id, action_taken, result, screenshot_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            log.site_id, log.session_id, log.page_id, log.action_taken, log.result, log.screenshot_path
        ))
        log.id = self.cursor.lastrowid
        self.conn.commit()
        return log


class MySQLDatabase(DatabaseInterface):
    """MySQL 数据库实现"""
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None
    
    def connect(self) -> None:
        import mysql.connector
        self.conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self.cursor = self.conn.cursor(dictionary=True)
        self.init_schema()
    
    def close(self) -> None:
        if self.conn:
            self.conn.close()
    
    def init_schema(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS sites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            domain VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) DEFAULT '',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS pages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            site_id INT NOT NULL,
            url_pattern VARCHAR(500) NOT NULL,
            title_pattern VARCHAR(255) DEFAULT '',
            page_type VARCHAR(50) DEFAULT 'unknown',
            semantic_description TEXT,
            key_features JSON,
            sample_url VARCHAR(500) DEFAULT '',
            visit_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id),
            INDEX idx_site (site_id),
            INDEX idx_url (url_pattern(255))
        );
        
        CREATE TABLE IF NOT EXISTS elements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            page_id INT NOT NULL,
            element_type VARCHAR(50) DEFAULT 'other',
            semantic_name VARCHAR(255) NOT NULL,
            semantic_description TEXT,
            text_content TEXT,
            aria_label VARCHAR(255) DEFAULT '',
            placeholder VARCHAR(255) DEFAULT '',
            css_selector_hint VARCHAR(500) DEFAULT '',
            position_hint VARCHAR(255) DEFAULT '',
            importance INT DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (page_id) REFERENCES pages(id),
            INDEX idx_page (page_id),
            INDEX idx_semantic (semantic_name)
        );
        
        CREATE TABLE IF NOT EXISTS actions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            site_id INT NOT NULL,
            source_page_id INT NOT NULL,
            element_id INT,
            action_type VARCHAR(50) NOT NULL,
            action_params JSON,
            target_page_id INT,
            success_rate FLOAT DEFAULT 1.0,
            execution_count INT DEFAULT 1,
            avg_duration_ms INT DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id),
            FOREIGN KEY (source_page_id) REFERENCES pages(id),
            FOREIGN KEY (element_id) REFERENCES elements(id),
            FOREIGN KEY (target_page_id) REFERENCES pages(id),
            INDEX idx_source (source_page_id)
        );
        
        CREATE TABLE IF NOT EXISTS task_paths (
            id INT AUTO_INCREMENT PRIMARY KEY,
            site_id INT NOT NULL,
            task_description TEXT NOT NULL,
            task_keywords TEXT,
            action_sequence JSON,
            start_page_id INT,
            end_page_id INT,
            success_count INT DEFAULT 0,
            fail_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id),
            INDEX idx_site (site_id)
        );
        
        CREATE TABLE IF NOT EXISTS exploration_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            site_id INT NOT NULL,
            session_id VARCHAR(100) NOT NULL,
            page_id INT,
            action_taken TEXT,
            result TEXT,
            screenshot_path VARCHAR(500) DEFAULT '',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        );
        """
        for statement in schema.split(';'):
            statement = statement.strip()
            if statement:
                try:
                    self.cursor.execute(statement)
                except Exception:
                    pass
        self.conn.commit()
    
    def get_or_create_site(self, domain: str, name: str = "", description: str = "") -> Site:
        self.cursor.execute("SELECT * FROM sites WHERE domain = %s", (domain,))
        row = self.cursor.fetchone()
        if row:
            return Site(
                id=row['id'],
                domain=row['domain'],
                name=row['name'],
                description=row['description']
            )
        
        self.cursor.execute(
            "INSERT INTO sites (domain, name, description) VALUES (%s, %s, %s)",
            (domain, name or domain, description)
        )
        self.conn.commit()
        return Site(
            id=self.cursor.lastrowid,
            domain=domain,
            name=name or domain,
            description=description
        )
    
    def get_site_by_domain(self, domain: str) -> Optional[Site]:
        self.cursor.execute("SELECT * FROM sites WHERE domain = %s", (domain,))
        row = self.cursor.fetchone()
        if not row:
            return None
        return Site(id=row['id'], domain=row['domain'], name=row['name'], description=row['description'])
    
    def save_page(self, page: Page) -> Page:
        if page.id:
            self.cursor.execute("""
                UPDATE pages SET 
                    url_pattern=%s, title_pattern=%s, page_type=%s, semantic_description=%s,
                    key_features=%s, sample_url=%s, visit_count=%s
                WHERE id=%s
            """, (
                page.url_pattern, page.title_pattern, page.page_type.value,
                page.semantic_description, page.key_features, page.sample_url,
                page.visit_count, page.id
            ))
        else:
            self.cursor.execute("""
                INSERT INTO pages (site_id, url_pattern, title_pattern, page_type, 
                    semantic_description, key_features, sample_url, visit_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                page.site_id, page.url_pattern, page.title_pattern, page.page_type.value,
                page.semantic_description, page.key_features, page.sample_url, page.visit_count
            ))
            page.id = self.cursor.lastrowid
        self.conn.commit()
        return page
    
    def get_page_by_url(self, site_id: int, url: str) -> Optional[Page]:
        parsed = urlparse(url)
        url_base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        self.cursor.execute(
            "SELECT * FROM pages WHERE site_id = %s AND (url_pattern = %s OR sample_url = %s)",
            (site_id, url_base, url)
        )
        row = self.cursor.fetchone()
        return self._row_to_page(row) if row else None
    
    def get_pages_by_site(self, site_id: int) -> List[Page]:
        self.cursor.execute("SELECT * FROM pages WHERE site_id = %s", (site_id,))
        return [self._row_to_page(row) for row in self.cursor.fetchall()]
    
    def find_similar_page(self, site_id: int, url: str, title: str) -> Optional[Page]:
        self.cursor.execute("SELECT * FROM pages WHERE site_id = %s", (site_id,))
        for row in self.cursor.fetchall():
            page = self._row_to_page(row)
            if title and page.title_pattern and title.lower() in page.title_pattern.lower():
                return page
        return None
    
    def _row_to_page(self, row) -> Page:
        return Page(
            id=row['id'],
            site_id=row['site_id'],
            url_pattern=row['url_pattern'],
            title_pattern=row['title_pattern'],
            page_type=PageType(row['page_type']) if row['page_type'] else PageType.UNKNOWN,
            semantic_description=row['semantic_description'] or '',
            key_features=row['key_features'] if isinstance(row['key_features'], str) else json.dumps(row['key_features'] or {}),
            sample_url=row['sample_url'] or '',
            visit_count=row['visit_count'] or 0
        )
    
    def save_element(self, element: Element) -> Element:
        if element.id:
            self.cursor.execute("""
                UPDATE elements SET 
                    element_type=%s, semantic_name=%s, semantic_description=%s, text_content=%s,
                    aria_label=%s, placeholder=%s, css_selector_hint=%s, position_hint=%s, importance=%s
                WHERE id=%s
            """, (
                element.element_type.value, element.semantic_name, element.semantic_description,
                element.text_content, element.aria_label, element.placeholder,
                element.css_selector_hint, element.position_hint, element.importance, element.id
            ))
        else:
            self.cursor.execute("""
                INSERT INTO elements (page_id, element_type, semantic_name, semantic_description,
                    text_content, aria_label, placeholder, css_selector_hint, position_hint, importance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                element.page_id, element.element_type.value, element.semantic_name,
                element.semantic_description, element.text_content, element.aria_label,
                element.placeholder, element.css_selector_hint, element.position_hint, element.importance
            ))
            element.id = self.cursor.lastrowid
        self.conn.commit()
        return element
    
    def get_elements_by_page(self, page_id: int) -> List[Element]:
        self.cursor.execute("SELECT * FROM elements WHERE page_id = %s", (page_id,))
        return [self._row_to_element(row) for row in self.cursor.fetchall()]
    
    def find_element_by_semantic(self, page_id: int, semantic_name: str) -> Optional[Element]:
        self.cursor.execute("""
            SELECT * FROM elements WHERE page_id = %s AND 
            (semantic_name LIKE %s OR semantic_description LIKE %s)
        """, (page_id, f"%{semantic_name}%", f"%{semantic_name}%"))
        row = self.cursor.fetchone()
        return self._row_to_element(row) if row else None
    
    def _row_to_element(self, row) -> Element:
        return Element(
            id=row['id'],
            page_id=row['page_id'],
            element_type=ElementType(row['element_type']) if row['element_type'] else ElementType.OTHER,
            semantic_name=row['semantic_name'],
            semantic_description=row['semantic_description'] or '',
            text_content=row['text_content'] or '',
            aria_label=row['aria_label'] or '',
            placeholder=row['placeholder'] or '',
            css_selector_hint=row['css_selector_hint'] or '',
            position_hint=row['position_hint'] or '',
            importance=row['importance'] or 5
        )
    
    def save_action(self, action: Action) -> Action:
        if action.id:
            self.cursor.execute("""
                UPDATE actions SET 
                    element_id=%s, action_type=%s, action_params=%s, target_page_id=%s,
                    success_rate=%s, execution_count=%s, avg_duration_ms=%s, notes=%s
                WHERE id=%s
            """, (
                action.element_id, action.action_type.value, action.action_params,
                action.target_page_id, action.success_rate, action.execution_count,
                action.avg_duration_ms, action.notes, action.id
            ))
        else:
            self.cursor.execute("""
                INSERT INTO actions (site_id, source_page_id, element_id, action_type,
                    action_params, target_page_id, success_rate, execution_count, avg_duration_ms, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                action.site_id, action.source_page_id, action.element_id, action.action_type.value,
                action.action_params, action.target_page_id, action.success_rate,
                action.execution_count, action.avg_duration_ms, action.notes
            ))
            action.id = self.cursor.lastrowid
        self.conn.commit()
        return action
    
    def get_actions_from_page(self, page_id: int) -> List[Action]:
        self.cursor.execute("SELECT * FROM actions WHERE source_page_id = %s", (page_id,))
        return [self._row_to_action(row) for row in self.cursor.fetchall()]
    
    def get_action_to_page(self, source_page_id: int, target_page_id: int) -> Optional[Action]:
        self.cursor.execute(
            "SELECT * FROM actions WHERE source_page_id = %s AND target_page_id = %s",
            (source_page_id, target_page_id)
        )
        row = self.cursor.fetchone()
        return self._row_to_action(row) if row else None
    
    def _row_to_action(self, row) -> Action:
        return Action(
            id=row['id'],
            site_id=row['site_id'],
            source_page_id=row['source_page_id'],
            element_id=row['element_id'],
            action_type=ActionType(row['action_type']) if row['action_type'] else ActionType.CLICK,
            action_params=row['action_params'] if isinstance(row['action_params'], str) else json.dumps(row['action_params'] or {}),
            target_page_id=row['target_page_id'],
            success_rate=row['success_rate'] or 1.0,
            execution_count=row['execution_count'] or 1,
            avg_duration_ms=row['avg_duration_ms'] or 0,
            notes=row['notes'] or ''
        )
    
    def save_task_path(self, task_path: TaskPath) -> TaskPath:
        if task_path.id:
            self.cursor.execute("""
                UPDATE task_paths SET 
                    task_description=%s, task_keywords=%s, action_sequence=%s,
                    start_page_id=%s, end_page_id=%s, success_count=%s, fail_count=%s
                WHERE id=%s
            """, (
                task_path.task_description, task_path.task_keywords, task_path.action_sequence,
                task_path.start_page_id, task_path.end_page_id, task_path.success_count,
                task_path.fail_count, task_path.id
            ))
        else:
            self.cursor.execute("""
                INSERT INTO task_paths (site_id, task_description, task_keywords, action_sequence,
                    start_page_id, end_page_id, success_count, fail_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                task_path.site_id, task_path.task_description, task_path.task_keywords,
                task_path.action_sequence, task_path.start_page_id, task_path.end_page_id,
                task_path.success_count, task_path.fail_count
            ))
            task_path.id = self.cursor.lastrowid
        self.conn.commit()
        return task_path
    
    def find_task_path(self, site_id: int, task_description: str) -> Optional[TaskPath]:
        keywords = task_description.lower().split()
        self.cursor.execute("SELECT * FROM task_paths WHERE site_id = %s", (site_id,))
        
        best_match = None
        best_score = 0
        
        for row in self.cursor.fetchall():
            task_path = self._row_to_task_path(row)
            score = sum(1 for kw in keywords if kw in task_path.task_keywords.lower())
            if score > best_score:
                best_score = score
                best_match = task_path
        
        return best_match if best_score > 0 else None
    
    def get_task_paths_by_site(self, site_id: int) -> List[TaskPath]:
        self.cursor.execute("SELECT * FROM task_paths WHERE site_id = %s", (site_id,))
        return [self._row_to_task_path(row) for row in self.cursor.fetchall()]
    
    def _row_to_task_path(self, row) -> TaskPath:
        return TaskPath(
            id=row['id'],
            site_id=row['site_id'],
            task_description=row['task_description'],
            task_keywords=row['task_keywords'] or '',
            action_sequence=row['action_sequence'] if isinstance(row['action_sequence'], str) else json.dumps(row['action_sequence'] or []),
            start_page_id=row['start_page_id'],
            end_page_id=row['end_page_id'],
            success_count=row['success_count'] or 0,
            fail_count=row['fail_count'] or 0
        )
    
    def save_exploration_log(self, log: ExplorationLog) -> ExplorationLog:
        self.cursor.execute("""
            INSERT INTO exploration_logs (site_id, session_id, page_id, action_taken, result, screenshot_path)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            log.site_id, log.session_id, log.page_id, log.action_taken, log.result, log.screenshot_path
        ))
        log.id = self.cursor.lastrowid
        self.conn.commit()
        return log


def create_database(config) -> DatabaseInterface:
    """根据配置创建数据库实例"""
    if hasattr(config, 'type'):
        db_type = config.type.lower()
        host = getattr(config, 'host', 'localhost')
        port = getattr(config, 'port', 3306)
        user = getattr(config, 'user', 'root')
        password = getattr(config, 'password', '')
        database = getattr(config, 'database', 'web_agent')
        path = getattr(config, 'path', 'web_agent_memory.db')
    else:
        db_type = config.get('type', 'sqlite').lower()
        host = config.get('host', 'localhost')
        port = config.get('port', 3306)
        user = config.get('user', 'root')
        password = config.get('password', '')
        database = config.get('database', 'web_agent')
        path = config.get('path', 'web_agent_memory.db')
    
    if db_type == 'mysql':
        return MySQLDatabase(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
    else:
        return SQLiteDatabase(db_path=path)
