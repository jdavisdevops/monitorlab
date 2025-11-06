# MonitorLab Quick Start Guide

Get started with MonitorLab's new architecture in 5 minutes!

## What's New in v0.2.0

- ✅ **LangGraph** for orchestration (not custom code)
- ✅ **Domain agents** that test complete features (not specialized workers)
- ✅ **Qwen2-VL-4B** vision model (not LLaVA)
- ✅ **Playwright MCP** (not custom browser wrappers)
- ✅ **Gradio UI** (not built from scratch)
- ✅ **SQLite history tracking** built-in
- ✅ **uv-ready** for modern Python packaging

## Prerequisites

- Mac with M-series chip (M1/M2/M3) and 16GB+ RAM
- Python 3.10+
- [LM Studio](https://lmstudio.ai/)

## Step 1: Install

### With uv (Recommended - Much Faster!)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install MonitorLab
cd monitorlab
uv pip install -e .
```

### With pip

```bash
pip install -e .
```

## Step 2: Setup LM Studio

1. **Download and launch LM Studio**

2. **Load models:**

   Navigate to "Discover" tab:

   **For Vision (Required):**
   - Search for "Qwen2-VL-4B-Instruct"
   - Download Q4 quantized version
   - Load it

   **For LLM (Required):**
   - Search for "Llama-3.2-3B-Instruct" or "Qwen2.5-3B-Instruct"
   - Download Q4 version
   - Load it

3. **Start API server:**
   - Go to "Local Server" tab
   - Click "Start Server"
   - Verify port is 1234
   - Keep LM Studio running

## Step 3: Configure

```bash
cp .env.example .env
# Default settings work fine!
```

## Step 4: Launch

```bash
monitorlab
```

The Gradio UI will open at http://localhost:7860

## Your First Test

In the Gradio chat interface, try:

```
Check if https://example.com loads correctly
```

Watch as MonitorLab:
1. 🤖 Understands your request
2. 🎯 Spawns appropriate agent (HomepageAgent)
3. 🌐 Navigates to the site
4. 👁️ Takes screenshot
5. ✅ Validates with Qwen2-VL
6. 📊 Reports results

All in ~5 seconds!

## Usage Patterns

### 1. Interactive Chat (Easiest)

Perfect for ad-hoc testing:

```
Test the login form at https://myapp.com/login
Verify checkout flow on https://shop.com/cart
Check if https://example.com has proper SEO
```

### 2. Programmatic (For CI/CD)

```python
import asyncio
from monitorlab import TestOrchestrator, HomepageAgent

async def test():
    orch = TestOrchestrator()
    await orch.initialize()
    
    orch.add_agent(HomepageAgent("https://mysite.com"))
    results = await orch.run_parallel("Deploy Check")
    
    print(f"Success: {results['statistics']['success_rate']}")

asyncio.run(test())
```

### 3. Multiple Agents in Parallel

```python
# Test multiple features simultaneously
orch.add_agent(HomepageAgent("https://site.com"))
orch.add_agent(CheckoutAgent("https://site.com/cart"))
orch.add_agent(AuthenticationAgent("https://site.com/login"))

# All run in parallel, each testing complete functionality
results = await orch.run_parallel()
```

## Key Concepts

### Domain Agents (NEW!)

Each agent tests an **entire feature**:

- `HomepageAgent`: Tests complete homepage (navigation, layout, content)
- `AuthenticationAgent`: Tests full login flow (form, submission, errors)
- `CheckoutAgent`: Tests checkout process (cart, billing, payment pages)
- `GenericTestAgent`: For custom tests via natural language

### LangGraph Orchestration

- Manages agent state
- Tracks execution history
- Handles parallel/sequential execution
- Provides checkpointing

### Run History

Every test is automatically saved:

```python
from monitorlab.database import TestRunRepository

# View recent runs
runs = await TestRunRepository.get_recent_test_runs()

# Get detailed stats
stats = await TestRunRepository.get_test_statistics(run_id=1)
```

Or view in the Gradio UI's "📊 Test History" tab.

## Examples

See `examples/` directory:

- `basic_usage.py`: Simple single-agent test
- `multi_agent.py`: Parallel multi-agent testing

Run them:

```bash
python examples/basic_usage.py
python examples/multi_agent.py
```

## Common Issues

### "Connection refused" error
**Problem:** LM Studio isn't running  
**Solution:** Open LM Studio → Local Server → Start Server

### "No model loaded"
**Problem:** Models not loaded in LM Studio  
**Solution:** Load Qwen2-VL-4B and a 3B LLM model

### Slow execution
**Problem:** Models too large or not quantized  
**Solution:** Use Q4 quantized models, close other apps

### Out of memory
**Problem:** Not enough RAM for models  
**Solution:** Use 3B models, Q4 quantization, close other apps

## Next Steps

1. **Try different agents:**
   ```python
   from monitorlab import (
       HomepageAgent,
       AuthenticationAgent,
       CheckoutAgent,
       GenericTestAgent,
   )
   ```

2. **Create custom domain agents:**
   ```python
   from monitorlab.agents import DomainAgent
   
   class MyFeatureAgent(DomainAgent):
       async def execute(self):
           # Test your complete feature
           pass
   ```

3. **Integrate with CI/CD:**
   - Run programmatically in headless mode
   - Check success rates
   - Fail builds on errors

4. **Explore LangGraph features:**
   - Conditional agent execution
   - Agent dependencies
   - State persistence

## Tips

- **Start small**: Test one page first, then expand
- **Use chat interface**: Fastest way to validate approach
- **Check history**: Learn from past runs
- **Parallel agents**: Test multiple features simultaneously
- **Custom agents**: Create domain agents for your specific features

## Getting Help

- **Logs**: Check `monitorlab.log`
- **Database**: Query `monitorlab.db` for detailed history
- **Docs**: See full [README.md](README.md)
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

Happy testing! 🚀
