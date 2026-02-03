<div align="center">

# 🕷️ Claweb

**基于 Tarsier 和视觉 LLM 的智能 Web 自动化 Agent**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Playwright](https://img.shields.io/badge/Playwright-1.40+-orange.svg)](https://playwright.dev/)

[English](README.md) | [中文](README_CN.md)

</div>

---

## ✨ 特性

- 🧠 **视觉 LLM 驱动** - 使用 GPT-4V/Claude 进行智能页面理解
- 🏷️ **Tarsier 集成** - 自动元素标记和识别
- 🧭 **智能导航** - 自然语言任务执行
- 📚 **记忆系统** - 学习和记忆网站结构
- 🔍 **自动探索** - 自主探索和映射网站
- 💾 **持久化存储** - 支持 SQLite/MySQL 知识库

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/ai-claw/claweb.git
cd claweb

# 使用 pip 安装（开发模式）
pip install -e .

# 或从 PyPI 安装（发布后）
pip install claweb

# 安装 Playwright 浏览器
playwright install chromium
```

## ⚙️ 配置

创建 `.env` 文件：

```bash
cp .env.example .env
```

配置参数：

```env
# LLM 配置（必需）
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4o

# 浏览器配置
HEADLESS=false
BROWSER_WIDTH=1280
BROWSER_HEIGHT=800

# 数据库配置
DB_TYPE=sqlite
DB_PATH=web_agent_memory.db
```

## 🚀 快速开始

### 命令行使用

```bash
# 交互模式
claweb --url https://example.com

# 任务模式
claweb --url https://example.com --task "搜索产品"

# 探索模式
claweb --url https://example.com --explore --site-name "示例网站"
```

### Python API

```python
import asyncio
from claweb import WebAgent, load_config

async def main():
    config = load_config()
    agent = WebAgent(config)
    
    await agent.start()
    await agent.goto("https://example.com")
    
    # 执行任务
    result = await agent.execute_task("点击登录按钮")
    print(result)
    
    await agent.stop()

asyncio.run(main())
```

## 📁 项目结构

```
claweb/
├── src/
│   └── claweb/
│       ├── __init__.py         # 包导出
│       ├── cli.py              # CLI 入口
│       ├── core/               # 核心模块
│       │   ├── agent.py        # WebAgent 主类
│       │   ├── browser.py      # 浏览器管理
│       │   └── config.py       # 配置管理
│       ├── llm/                # LLM 集成
│       │   └── client.py       # 视觉 LLM 客户端
│       ├── tagger/             # 页面标记
│       │   └── page_tagger.py  # Tarsier 集成
│       ├── executor/           # 动作执行
│       │   └── action_executor.py
│       ├── explorer/           # 网站探索
│       │   └── explorer.py
│       ├── storage/            # 数据持久化
│       │   ├── database.py     # 数据库抽象层
│       │   └── models.py       # 数据模型
│       └── utils/              # 工具函数
├── tests/                      # 测试套件
├── pyproject.toml              # 项目配置
├── .env.example                # 环境变量模板
└── README.md
```

## 🎮 支持的操作

| 命令 | 说明 | 示例 |
|------|------|------|
| `CLICK [ID]` | 点击元素 | `CLICK [5]` |
| `TYPE [ID] "文本"` | 输入文本 | `TYPE [3] "你好"` |
| `SCROLL UP/DOWN` | 滚动页面 | `SCROLL DOWN` |
| `GOTO "url"` | 导航跳转 | `GOTO "https://..."` |
| `WAIT n` | 等待秒数 | `WAIT 3` |
| `PAUSE` | 暂停等待人工操作 | `PAUSE` |
| `DONE` | 任务完成 | `DONE` |

## 🔧 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src/
isort src/

# 类型检查
mypy src/
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🤝 贡献

欢迎贡献！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。
