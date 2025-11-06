# MonitorLab

**AI-Enhanced Website Monitoring with Multi-Agent Architecture**

MonitorLab is a modern website monitoring and validation system powered by locally-hosted LLMs, LangGraph orchestration, and autonomous domain agents.

## 🎯 What's Different

Unlike traditional testing frameworks, MonitorLab uses **domain agents** that autonomously test complete features:

```python
# Traditional approach (what we DON'T do):
navigator.goto(url)
interactor.click(button)
validator.check(result)

# MonitorLab approach (what we DO):
homepage_agent = HomepageAgent("https://example.com")
checkout_agent = CheckoutAgent("https://shop.com/cart")  
auth_agent = AuthenticationAgent("https://app.com/login")

# Each agent tests the ENTIRE flow autonomously
await orchestrator.run_parallel([homepage_agent, checkout_agent, auth_agent])
```

## 🚀 Key Features

- **🤖 Domain Agents**: Autonomous agents that test complete features (not just tasks)
- **🧠 LangGraph Orchestration**: State management and complex workflows
- **👁️ Qwen2-VL-4B Vision**: Best-in-class local vision model for UI validation
- **🎭 Playwright MCP**: Browser automation via Model Context Protocol
- **📊 Run History**: SQLite tracking with full test history
- **💬 Gradio UI**: Modern chat interface (not built from scratch!)
- **📦 uv-ready**: Modern Python packaging with `uv`
- **🔒 Privacy First**: Everything runs locally

## Architecture

```
┌─────────────────────────────────────────────┐
│           Gradio Chat Interface             │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      LangGraph Test Orchestrator            │
│  (Parallel/Sequential Agent Coordination)   │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐  ┌────────▼────────┐
│ Domain Agents  │  │  Infrastructure │
│                │  │                 │
│ • Homepage     │  │ • LM Studio LLM │
│ • Auth         │  │ • Qwen2-VL      │
│ • Checkout     │  │ • Playwright MCP│
│ • Generic      │  │ • SQLite DB     │
└────────────────┘  └─────────────────┘
```

## Installation

### Prerequisites

- **Mac with M-series chip** (M1/M2/M3) and 16GB+ RAM
- **Python 3.10+**
- **LM Studio** ([download](https://lmstudio.ai/))
- **uv** (recommended) or pip

### Install with uv (Recommended)

```bash
# Install uv if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/yourusername/monitorlab.git
cd monitorlab

# Install with uv
uv pip install -e .
```

### Install with pip

```bash
pip install -e .
```

## Quick Start

### 1. Setup LM Studio

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Load **Qwen2-VL-4B-Instruct** model (recommended for vision)
3. Load any 3-7B instruct model for reasoning (e.g., Llama-3.2-3B-Instruct)
4. Go to **Local Server** tab → Click **Start Server** (port 1234)

### 2. Configure MonitorLab

```bash
cp .env.example .env
# Edit .env if needed (defaults work for standard LM Studio setup)
```

### 3. Launch

```bash
monitorlab
```

That's it! The Gradio UI will open in your browser.

## Usage

### Interactive Chat (Easiest)

```
You: Check if https://example.com loads correctly

MonitorLab: 🤖 Understanding your request...
✅ Using Homepage Agent
🚀 Running test...
📊 Test Results:
- Status: success  
- Success Rate: 100%
- Duration: 3.2s
```

### Programmatic Usage

```python
import asyncio
from monitorlab import TestOrchestrator, HomepageAgent, CheckoutAgent

async def test_my_site():
    # Create orchestrator
    orchestrator = TestOrchestrator()
    await orchestrator.initialize()
    
    # Add domain agents
    orchestrator.add_agent(HomepageAgent("https://mysite.com"))
    orchestrator.add_agent(CheckoutAgent("https://mysite.com/cart"))
    
    # Run in parallel - each agent tests complete functionality
    results = await orchestrator.run_parallel("Post-Deploy Validation")
    
    print(f"Success Rate: {results['statistics']['success_rate']}")

asyncio.run(test_my_site())
```

### Creating Custom Domain Agents

```python
from monitorlab.agents import DomainAgent

class SearchAgent(DomainAgent):
    """Tests complete search functionality."""
    
    async def execute(self) -> AgentState:
        # Navigate to site
        await self.playwright_mcp.execute_tool(
            "playwright_navigate",
            {"url": self.target_url}
        )
        
        # Perform search
        await self.playwright_mcp.execute_tool(
            "playwright_fill",
            {"selector": "input[type='search']", "value": "test query"}
        )
        
        # Take screenshot
        screenshot = await self.take_screenshot("search_results")
        
        # Validate with vision model
        validation = await self.validate_visual(
            screenshot,
            ["Search results displayed", "No errors", "Results are relevant"]
        )
        
        self.state["output"]["validation"] = validation
        self.state["status"] = "success" if validation["overall_valid"] else "failure"
        
        return self.state
```

## Why This Architecture?

### Domain Agents vs. Specialized Workers

**❌ Old Approach (Specialized Workers):**
```python
# Need to orchestrate multiple specialized agents for one test
navigator.goto("https://site.com")  
interaction.click("#login")
validator.check_result()
vision.verify_screenshot()
```

**✅ New Approach (Domain Agents):**
```python
# One agent handles entire login flow
auth_agent = AuthenticationAgent("https://site.com/login")
await auth_agent.run()  # Does everything: navigate, interact, validate, capture
```

### Why LangGraph?

- **State Management**: Built-in state persistence and checkpointing
- **Complex Workflows**: Handle agent dependencies and conditional execution
- **Run History**: Track every test execution
- **Battle-Tested**: Used in production by many companies

### Why Qwen2-VL-4B?

- **Latest & Greatest**: More recent than LLaVA
- **Better Performance**: Superior vision understanding
- **Right Size**: 4B parameters fits in 16GB RAM
- **Optimized**: Works great on Mac M-series chips

### Why Playwright MCP?

- **Standard Protocol**: MCP is becoming the standard for tool use
- **LLM-Native**: Designed for LLM interaction
- **Less Code**: No custom browser abstractions to maintain
- **Better Integration**: Direct communication with LangChain/LangGraph

### Why Gradio?

- **Pre-built Components**: Chat UI out of the box
- **Modern**: Better than building from scratch
- **Features**: Built-in history, file uploads, themes
- **Popular**: Large community and good docs

## Configuration

Key settings in `.env`:

```env
# LLM (reasoning)
LLM_API_BASE=http://localhost:1234/v1
LLM_MODEL=local-model

# Vision (Qwen2-VL-4B)
VISION_MODEL=Qwen2-VL-4B-Instruct
VISION_TEMPERATURE=0.2

# MCP
MCP_PLAYWRIGHT_ENABLED=true

# Agents
MAX_CONCURRENT_AGENTS=5

# Database
DATABASE_URL=sqlite+aiosqlite:///./monitorlab.db

# UI
GRADIO_SERVER_PORT=7860
```

## Run History & Tracking

All test runs are automatically saved to SQLite:

```python
from monitorlab.database import TestRunRepository

# Get recent runs
runs = await TestRunRepository.get_recent_test_runs(limit=10)

# Get detailed statistics
stats = await TestRunRepository.get_test_statistics(run_id=1)

# Query by name
my_tests = await TestRunRepository.get_test_runs_by_name("Post-Deploy Check")
```

View history in the Gradio UI under the **📊 Test History** tab.

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format monitorlab/

# Lint
ruff check monitorlab/
```

## Model Recommendations

### For 16GB RAM (M-series Mac):

**LLM (Reasoning):**
- ✅ Llama-3.2-3B-Instruct (best balance)
- ✅ Phi-3-Mini (3.8B, very fast)
- ✅ Qwen2.5-3B-Instruct (excellent quality)

**Vision:**
- ✅ **Qwen2-VL-4B-Instruct** (recommended!)
- ✅ Moondream2 (1.6B, fastest)
- ❌ LLaVA 1.6 7B (older, larger)

### For 32GB+ RAM:

- LLM: Llama-3.1-8B-Instruct or Qwen2.5-7B-Instruct
- Vision: Qwen2-VL-7B-Instruct

## Comparison

| Feature | MonitorLab v0.2 | Traditional Testing |
|---------|-----------------|---------------------|
| Agent Type | Domain (autonomous) | Task-based (orchestrated) |
| Orchestration | LangGraph | Custom code |
| Vision | Qwen2-VL-4B | Manual screenshots |
| Browser | Playwright MCP | Custom wrappers |
| History | SQLite built-in | DIY |
| UI | Gradio | Built from scratch |
| Package Manager | uv-ready | pip only |

## FAQ

**Q: Why not use Selenium?**  
A: Playwright is more modern, has better async support, and MCP integration.

**Q: Why not use cloud LLMs?**  
A: Privacy, cost, and latency. Local models are fast enough for testing.

**Q: Can I use GPT-4 Vision instead?**  
A: Yes, just change the vision client to use OpenAI API. But Qwen2-VL is free and private.

**Q: Does this replace Pytest/Selenium?**  
A: No, it complements them. Use for post-deploy validation and visual testing.

**Q: What about CI/CD integration?**  
A: Run programmatically in headless mode. See examples in `examples/`.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

**Common issues:**
- **LM Studio not connecting**: Make sure Local Server is started
- **Vision model errors**: Load Qwen2-VL-4B in LM Studio
- **Out of memory**: Use 3B LLM models, close other apps

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT

## Acknowledgments

- **LangGraph**: For the excellent orchestration framework
- **Qwen Team**: For the amazing Qwen2-VL model
- **Gradio**: For making UIs easy
- **Playwright**: For robust browser automation
- **LM Studio**: For making local LLMs accessible

---

**MonitorLab v0.2.0** - Built with LangGraph, Qwen2-VL, and ❤️
