# Claweb

<p align="center">
  <strong>🕷️ AI-powered Web Automation Agent with Visual Understanding</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#usage">Usage</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

---

Claweb 是一个基于视觉大模型的 Web 自动化 Agent，利用 [Tarsier](https://github.com/reworkd/tarsier) 进行页面元素标注，让 AI 能够"看懂"网页并执行自动化操作。

与传统的基于选择器的自动化工具不同，Claweb 通过视觉理解来识别页面元素，无需编写脆弱的 CSS/XPath 选择器，能够适应页面结构的变化。

## Features

- **视觉驱动**：基于 Vision LLM（如 GPT-4o）理解页面内容，无需硬编码选择器
- **智能标注**：使用 Tarsier 自动标注页面可交互元素，建立视觉与 DOM 的映射
- **记忆系统**：自动学习网站结构，记住操作路径，下次执行更快更准
- **自动探索**：支持自动探索网站功能，发现导航菜单、CRUD 操作等
- **多模式运行**：
  - 交互模式：实时输入指令
  - 任务模式：执行单次任务
  - 探索模式：自动学习网站
- **可扩展存储**：支持 SQLite（默认）和 MySQL

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js (for Playwright)

### Installation

```bash
# Clone the repository
git clone https://github.com/ai-claw/claweb.git
cd claweb

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Configuration

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
vim .env
```

Required configuration:
```env
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o  # or other vision-capable model
```

## Usage

### Interactive Mode

```bash
python main.py
```

Commands:
- `goto <url>` - Navigate to URL
- `do <instruction>` - Execute natural language instruction
- `explore` - Auto-explore current website
- `memory` - Show memory statistics
- `wait` - Pause for manual operation (login, captcha)
- `quit` - Exit

### Task Mode

Execute a single task:

```bash
python main.py --url "https://example.com" --task "Click the login button"
```

### Explore Mode

Auto-explore a website and build memory:

```bash
python main.py --url "https://example.com/dashboard" --explore --site-name "Example Site"
```

### Examples

```bash
# Login to a website
python main.py --url "https://example.com/login" \
  --task "Login with username admin@test.com and password 123456"

# Explore admin panel
python main.py --url "https://admin.example.com" --explore

# Execute without memory (fresh start)
python main.py --url "https://example.com" --no-memory \
  --task "Click the search button"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Input                          │
│                    (Natural Language Task)                  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        WebAgent                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │   Browser   │  │  PageTagger  │  │   VisionLLM       │  │
│  │   Manager   │  │  (Tarsier)   │  │   Client          │  │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬─────────┘  │
│         │                │                     │            │
│         ▼                ▼                     ▼            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ActionExecutor                          │   │
│  │   CLICK / TYPE / SCROLL / GOTO / WAIT / PAUSE       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Memory System                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Site   │  │   Page   │  │  Element │  │ TaskPath │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Description |
|-----------|-------------|
| `agent.py` | Main WebAgent class, orchestrates all components |
| `browser.py` | Playwright browser management |
| `page_tagger.py` | Tarsier integration for element tagging |
| `llm_client.py` | Vision LLM client (OpenAI compatible) |
| `action_executor.py` | Parse and execute LLM commands |
| `explorer.py` | Site exploration and learning |
| `models.py` | Data models for memory system |
| `database.py` | Database abstraction (SQLite/MySQL) |

### Supported Actions

| Command | Description | Example |
|---------|-------------|---------|
| `CLICK [ID]` | Click element | `CLICK [$5]` |
| `TYPE [ID] "text"` | Input text | `TYPE [#3] "hello"` |
| `SCROLL UP/DOWN` | Scroll page | `SCROLL DOWN` |
| `GOTO "url"` | Navigate | `GOTO "https://..."` |
| `WAIT n` | Wait seconds | `WAIT 3` |
| `PAUSE` | Wait for manual input | `PAUSE` |
| `DONE` | Task complete | `DONE` |

## Configuration Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_API_BASE` | LLM API endpoint | `https://api.openai.com/v1` |
| `LLM_API_KEY` | API key | (required) |
| `LLM_MODEL` | Model name | `gpt-4o` |
| `HEADLESS` | Run browser headlessly | `false` |
| `BROWSER_WIDTH` | Browser width | `1280` |
| `BROWSER_HEIGHT` | Browser height | `800` |
| `DB_TYPE` | Database type | `sqlite` |
| `DB_PATH` | SQLite file path | `web_agent_memory.db` |
| `EXPLORE_MAX_PAGES` | Max pages to explore | `50` |
| `EXPLORE_MAX_DEPTH` | Max exploration depth | `5` |
| `SCREENSHOT_DIR` | Screenshot directory | `screenshots` |

## How It Works

1. **Page Tagging**: Tarsier marks interactive elements with visible labels (`[#1]`, `[$2]`, etc.)
2. **Screenshot Capture**: Take a screenshot with the tags visible
3. **LLM Analysis**: Send screenshot + element info to Vision LLM
4. **Action Decision**: LLM outputs a single action command
5. **Execution**: Execute the action using Playwright
6. **Memory Update**: Record successful operations for future use
7. **Repeat**: Continue until task is complete

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
python -m pytest test_explorer.py -v
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Tarsier](https://github.com/reworkd/tarsier) - Web page element tagging
- [Playwright](https://playwright.dev/) - Browser automation
- [OpenAI](https://openai.com/) - Vision language models
