# Contributing to Claweb

Thank you for your interest in contributing to Claweb! This document provides guidelines and information for contributors.

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming community for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in [GitHub Issues](https://github.com/ai-claw/claweb/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or screenshots

### Suggesting Features

1. Open an issue with `[Feature]` prefix
2. Describe the use case and expected behavior
3. Explain why this would benefit the project

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write/update tests if applicable
5. Ensure code follows project style
6. Commit with clear messages
7. Push and create a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/claweb.git
cd claweb

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Copy and configure environment
cp .env.example .env
# Edit .env with your API key
```

## Code Style

### Python Guidelines

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for function signatures
- Write docstrings for public functions and classes
- Keep functions focused and small (< 50 lines preferred)

### Code Formatting

```bash
# Format code (if using black)
black .

# Sort imports (if using isort)
isort .
```

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add support for multiple browser contexts
fix: resolve element click timeout issue
docs: update configuration reference
refactor: simplify action executor logic
test: add unit tests for page analyzer
```

## Project Structure

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

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_agent.py -v

# Run with coverage
pytest --cov=src/claweb -v
```

## Areas for Contribution

- **LLM Providers**: Add support for more Vision LLM providers (Claude, Gemini, etc.)
- **Browser Features**: Multi-tab support, file upload handling
- **Memory System**: Improved task path matching, memory optimization
- **Documentation**: Tutorials, examples, translations
- **Testing**: More unit tests, integration tests
- **Performance**: Optimization, caching

## Questions?

Feel free to open an issue for any questions about contributing.
