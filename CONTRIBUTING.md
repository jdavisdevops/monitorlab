# Contributing to MonitorLab

Thank you for your interest in contributing to MonitorLab! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.10+
- Mac with M-series chip (for testing)
- LM Studio for testing with local models
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/monitorlab.git
   cd monitorlab
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   playwright install
   ```

4. **Setup pre-commit hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

### Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Run before committing:
```bash
# Format code
black monitorlab/

# Lint
ruff check monitorlab/

# Type check
mypy monitorlab/
```

Or run all at once:
```bash
pre-commit run --all-files
```

### Code Structure

```
monitorlab/
├── agents/          # Agent implementations
├── browser/         # Browser automation
├── chat/           # Chat interface
├── config/         # Configuration management
├── core/           # Core framework (orchestrator)
├── models/         # LLM and vision clients
├── pipelines/      # Pipeline framework
└── tests/          # Tests
```

### Writing Tests

We use pytest for testing. Tests should be placed in the `tests/` directory.

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=monitorlab
```

Example test:
```python
import pytest
from monitorlab.agents.navigator import NavigatorAgent

@pytest.mark.asyncio
async def test_navigator_agent():
    agent = NavigatorAgent(task="Test task")
    assert agent.agent_type == "NavigatorAgent"
    assert agent.task == "Test task"
```

## Contributing Guidelines

### Reporting Issues

When reporting issues, please include:

- **Description**: Clear description of the issue
- **Steps to reproduce**: Detailed steps to reproduce the problem
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Environment**:
  - OS and version
  - Python version
  - MonitorLab version
  - LM Studio version (if applicable)
- **Logs**: Relevant logs from `monitorlab.log`

### Submitting Pull Requests

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, concise code
   - Follow existing code style
   - Add tests for new features
   - Update documentation as needed

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

   Commit message format:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test additions or changes
   - `refactor:` Code refactoring
   - `chore:` Maintenance tasks

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **PR Description should include:**
   - What changes were made
   - Why the changes were needed
   - How to test the changes
   - Any breaking changes
   - Related issue numbers

### Pull Request Checklist

- [ ] Code follows the project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated (for significant changes)
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages are clear and descriptive

## Areas for Contribution

### High Priority

- **Test Coverage**: Add tests for existing functionality
- **Documentation**: Improve docs, add examples
- **Error Handling**: Better error messages and recovery
- **Performance**: Optimize agent execution

### New Features

- **Additional Agent Types**: New specialized agents
- **Pipeline Features**: Enhanced pipeline capabilities
- **Integrations**: CI/CD integrations, webhooks
- **Reporting**: Better result visualization and reporting

### Code Quality

- **Type Hints**: Add type hints to all functions
- **Logging**: Improve logging throughout
- **Validation**: Better input validation
- **Error Messages**: More helpful error messages

## Development Tips

### Local Testing with LM Studio

For testing, you can use smaller models:
- **LLM**: Llama-3.2-1B-Instruct (faster for dev)
- **Vision**: Moondream2 (1.6B, very fast)

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or in .env:
```env
LOG_LEVEL=DEBUG
```

### Testing Specific Components

```python
# Test browser automation
from monitorlab.browser import BrowserManager

async def test():
    manager = BrowserManager()
    await manager.start()
    page = await manager.create_page("test")
    await page.goto("https://example.com")
    await manager.stop()

# Test LLM client
from monitorlab.models import LLMClient

async def test():
    client = LLMClient()
    response = await client.generate("Say hello")
    print(response)
```

## Architecture Decisions

### Why Playwright?
- Better than Selenium for modern web apps
- Excellent async support
- Built-in waiting mechanisms
- Cross-browser support

### Why LM Studio?
- Easy local model hosting
- OpenAI-compatible API
- Good Mac optimization
- User-friendly interface

### Why Async?
- Better performance for I/O operations
- Natural fit for browser automation
- Allows parallel agent execution

## Code Examples

### Adding a New Agent Type

```python
# monitorlab/agents/my_agent.py
from monitorlab.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    """Description of what this agent does."""

    async def execute(self) -> Dict[str, Any]:
        """Execute the agent's task."""
        # Your implementation
        return {
            "task": self.task,
            "success": True,
            "data": {},
        }
```

Register in `monitorlab/agents/__init__.py`:
```python
from monitorlab.agents.my_agent import MyAgent

__all__ = [..., "MyAgent"]
```

### Adding Configuration Options

```python
# In monitorlab/config/settings.py
class Settings(BaseSettings):
    # Add new setting
    my_setting: str = Field(default="value", alias="MY_SETTING")
```

Update `.env.example`:
```env
MY_SETTING=value
```

## Documentation

### Docstring Format

We use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails
    """
    pass
```

### README Updates

When adding features:
1. Update main README.md
2. Update relevant documentation
3. Add examples if appropriate
4. Update CHANGELOG.md

## Questions?

- Check existing issues and discussions
- Ask in pull request comments
- Create a discussion for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to make MonitorLab better!
