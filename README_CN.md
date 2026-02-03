# Claweb

<p align="center">
  <strong>🕷️ 基于视觉大模型的 Web 自动化 Agent</strong>
</p>

<p align="center">
  <a href="#特性">特性</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#使用方法">使用方法</a> •
  <a href="#架构设计">架构设计</a> •
  <a href="#贡献指南">贡献指南</a>
</p>

[English](README.md) | 中文

---

Claweb 是一个基于视觉大模型的 Web 自动化 Agent，利用 [Tarsier](https://github.com/reworkd/tarsier) 进行页面元素标注，让 AI 能够"看懂"网页并执行自动化操作。

与传统的基于选择器的自动化工具不同，Claweb 通过视觉理解来识别页面元素，无需编写脆弱的 CSS/XPath 选择器，能够适应页面结构的变化。

## 特性

- **视觉驱动**：基于 Vision LLM（如 GPT-4o）理解页面内容，无需硬编码选择器
- **智能标注**：使用 Tarsier 自动标注页面可交互元素，建立视觉与 DOM 的映射
- **记忆系统**：自动学习网站结构，记住操作路径，下次执行更快更准
- **自动探索**：支持自动探索网站功能，发现导航菜单、CRUD 操作等
- **多模式运行**：
  - 交互模式：实时输入指令
  - 任务模式：执行单次任务
  - 探索模式：自动学习网站
- **可扩展存储**：支持 SQLite（默认）和 MySQL

## 快速开始

### 环境要求

- Python 3.10+
- Node.js（Playwright 依赖）

### 安装

```bash
# 克隆仓库
git clone https://github.com/ai-claw/claweb.git
cd claweb

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env
```

必要配置：
```env
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o  # 或其他支持视觉的模型
```

## 使用方法

### 交互模式

```bash
python main.py
```

可用命令：
- `goto <url>` - 导航到指定网址
- `do <指令>` - 执行自然语言指令
- `explore` - 自动探索当前网站
- `memory` - 显示记忆统计
- `wait` - 等待手动操作（登录、验证码等）
- `quit` - 退出

### 任务模式

执行单次任务：

```bash
python main.py --url "https://example.com" --task "点击登录按钮"
```

### 探索模式

自动探索网站并建立记忆：

```bash
python main.py --url "https://example.com/dashboard" --explore --site-name "示例网站"
```

### 使用示例

```bash
# 登录网站
python main.py --url "https://example.com/login" \
  --task "使用用户名 admin@test.com 密码 123456 登录"

# 探索后台管理
python main.py --url "https://admin.example.com" --explore

# 无记忆模式执行
python main.py --url "https://example.com" --no-memory \
  --task "点击搜索按钮"
```

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                         用户输入                             │
│                    （自然语言任务描述）                        │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        WebAgent                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │   浏览器     │  │   页面标注    │  │   视觉大模型      │  │
│  │   管理器     │  │  (Tarsier)   │  │   客户端          │  │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬─────────┘  │
│         │                │                     │            │
│         ▼                ▼                     ▼            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  动作执行器                           │   │
│  │   CLICK / TYPE / SCROLL / GOTO / WAIT / PAUSE       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       记忆系统                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   网站   │  │   页面    │  │   元素   │  │  任务路径 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 说明 |
|-----|------|
| `agent.py` | 核心 WebAgent 类，协调各组件 |
| `browser.py` | Playwright 浏览器管理 |
| `page_tagger.py` | Tarsier 集成，元素标注 |
| `llm_client.py` | 视觉大模型客户端 |
| `action_executor.py` | 解析执行 LLM 命令 |
| `explorer.py` | 网站探索与学习 |
| `models.py` | 记忆系统数据模型 |
| `database.py` | 数据库抽象层 |

### 支持的操作

| 命令 | 说明 | 示例 |
|-----|------|------|
| `CLICK [ID]` | 点击元素 | `CLICK [$5]` |
| `TYPE [ID] "文本"` | 输入文本 | `TYPE [#3] "hello"` |
| `SCROLL UP/DOWN` | 滚动页面 | `SCROLL DOWN` |
| `GOTO "url"` | 导航 | `GOTO "https://..."` |
| `WAIT n` | 等待秒数 | `WAIT 3` |
| `PAUSE` | 等待手动操作 | `PAUSE` |
| `DONE` | 任务完成 | `DONE` |

## 工作原理

1. **页面标注**：Tarsier 为可交互元素添加可见标签（`[#1]`、`[$2]` 等）
2. **截图捕获**：获取带标签的页面截图
3. **LLM 分析**：将截图和元素信息发送给视觉大模型
4. **动作决策**：LLM 输出单个操作命令
5. **执行操作**：通过 Playwright 执行操作
6. **更新记忆**：记录成功的操作供后续使用
7. **循环**：重复直到任务完成

## 配置参考

| 变量 | 说明 | 默认值 |
|-----|------|-------|
| `LLM_API_BASE` | LLM API 地址 | `https://api.openai.com/v1` |
| `LLM_API_KEY` | API 密钥 | （必填） |
| `LLM_MODEL` | 模型名称 | `gpt-4o` |
| `HEADLESS` | 无头模式 | `false` |
| `BROWSER_WIDTH` | 浏览器宽度 | `1280` |
| `BROWSER_HEIGHT` | 浏览器高度 | `800` |
| `DB_TYPE` | 数据库类型 | `sqlite` |
| `DB_PATH` | SQLite 文件路径 | `web_agent_memory.db` |
| `EXPLORE_MAX_PAGES` | 最大探索页面数 | `50` |
| `EXPLORE_MAX_DEPTH` | 最大探索深度 | `5` |
| `SCREENSHOT_DIR` | 截图保存目录 | `screenshots` |

## 贡献指南

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 致谢

- [Tarsier](https://github.com/reworkd/tarsier) - 网页元素标注
- [Playwright](https://playwright.dev/) - 浏览器自动化
- [OpenAI](https://openai.com/) - 视觉语言模型
