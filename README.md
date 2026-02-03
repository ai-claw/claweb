<div align="center">

# 🕷️ Claweb

**Intelligent Web Automation Agent based on Tarsier and Vision LLM**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Playwright](https://img.shields.io/badge/Playwright-1.40+-orange.svg)](https://playwright.dev/)

[English](README.md) | [中文](README_CN.md)

</div>

---

## ✨ Features

- 🧠 **Vision LLM Powered** - Uses GPT-4V/Claude for intelligent page understanding
- 🏷️ **Tarsier Integration** - Automatic element tagging and identification
- 🧭 **Smart Navigation** - Natural language task execution
- 📚 **Memory System** - Learn and remember website structures
- 🔍 **Auto Exploration** - Autonomously explore and map websites
- 💾 **Persistent Storage** - SQLite/MySQL support for knowledge base

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/ai-claw/claweb.git
cd claweb

# Install with pip (editable mode for development)
pip install -e .

# Or install from PyPI (when published)
pip install claweb

# Install Playwright browsers
playwright install chromium
```

## ⚙️ Configuration

Create a `.env` file:

```bash
cp .env.example .env
```

Configure your settings:

```env
# LLM Configuration (Required)
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4o

# Browser Configuration
HEADLESS=false
BROWSER_WIDTH=1280
BROWSER_HEIGHT=800

# Database Configuration
DB_TYPE=sqlite
DB_PATH=web_agent_memory.db
```

## 🚀 Quick Start

### CLI Usage

```bash
# Interactive mode
claweb --url https://example.com

# Task mode
claweb --url https://example.com --task "search for products"

# Exploration mode
claweb --url https://example.com --explore --site-name "Example Site"
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
    
    # Execute task
    result = await agent.execute_task("click login button")
    print(result)
    
    await agent.stop()

asyncio.run(main())
```

## 📁 Project Structure

```
claweb/
├── src/
│   └── claweb/
│       ├── __init__.py         # Package exports
│       ├── cli.py              # CLI entry point
│       ├── core/               # Core modules
│       │   ├── agent.py        # WebAgent main class
│       │   ├── browser.py      # Browser manager
│       │   └── config.py       # Configuration
│       ├── llm/                # LLM integration
│       │   └── client.py       # Vision LLM client
│       ├── tagger/             # Page tagging
│       │   └── page_tagger.py  # Tarsier integration
│       ├── executor/           # Action execution
│       │   └── action_executor.py
│       ├── explorer/           # Site exploration
│       │   └── explorer.py
│       ├── storage/            # Data persistence
│       │   ├── database.py     # DB abstraction
│       │   └── models.py       # Data models
│       └── utils/              # Utilities
├── tests/                      # Test suite
├── pyproject.toml              # Project configuration
├── .env.example                # Environment template
└── README.md
```

## 🎮 Supported Actions

| Command | Description | Example |
|---------|-------------|---------|
| `CLICK [ID]` | Click element | `CLICK [5]` |
| `TYPE [ID] "text"` | Input text | `TYPE [3] "hello"` |
| `SCROLL UP/DOWN` | Scroll page | `SCROLL DOWN` |
| `GOTO "url"` | Navigate | `GOTO "https://..."` |
| `WAIT n` | Wait seconds | `WAIT 3` |
| `PAUSE` | Manual intervention | `PAUSE` |
| `DONE` | Task complete | `DONE` |

## 🔧 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black src/
isort src/

# Type checking
mypy src/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.
