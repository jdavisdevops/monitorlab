# MonitorLab Quick Start Guide

Get started with MonitorLab in 5 minutes!

## Prerequisites

- Mac with M-series chip (M1, M2, M3) and 16GB+ RAM
- Python 3.10 or higher
- [LM Studio](https://lmstudio.ai/) installed

## Step 1: Install MonitorLab

```bash
# Clone or navigate to the repository
cd monitorlab

# Install in development mode
pip install -e .

# Install Playwright browsers
playwright install chromium
```

## Step 2: Setup LM Studio

1. **Download and launch LM Studio**

2. **Load recommended models:**

   **For LLM (reasoning):**
   - Go to "Discover" tab
   - Search for "Llama-3.2-3B-Instruct"
   - Download and load the GGUF Q4 version

   **For Vision (visual validation):**
   - Search for "moondream2" or "llava-v1.6-7b"
   - Download the Q4 quantized version

3. **Start the API server:**
   - Go to "Local Server" tab
   - Click "Start Server"
   - Note the port (usually 1234)
   - Keep LM Studio running

## Step 3: Configure MonitorLab

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your settings (default values work for standard LM Studio setup):

```env
LLM_API_BASE=http://localhost:1234/v1
LLM_MODEL=local-model
VISION_API_BASE=http://localhost:1234/v1
VISION_MODEL=local-vision-model
HEADLESS=false
```

## Step 4: Run Your First Test

### Option A: Interactive Chat Mode (Recommended)

```bash
monitorlab-chat
```

Then try:
```
> Check if https://example.com loads correctly
```

### Option B: Run a Pipeline

```bash
monitorlab-run run examples/basic_website_check.yaml
```

### Option C: Python Script

Create `my_test.py`:

```python
import asyncio
from monitorlab import AgentOrchestrator, NavigatorAgent, VisionAgent

async def main():
    orchestrator = AgentOrchestrator()
    await orchestrator.setup()

    orchestrator.spawn_agent(
        NavigatorAgent,
        task="Navigate to https://example.com"
    )

    orchestrator.spawn_agent(
        VisionAgent,
        task="Verify the page renders correctly"
    )

    results = await orchestrator.run()

    for result in results:
        print(f"{result.agent_type}: {result.status.value}")

    await orchestrator.teardown()

asyncio.run(main())
```

Run it:
```bash
python my_test.py
```

## What Just Happened?

MonitorLab:
1. ✅ Started a browser using Playwright
2. ✅ Used your local LLM to understand the task
3. ✅ Navigated to the website
4. ✅ Took a screenshot
5. ✅ Used vision model to validate rendering
6. ✅ Reported results

All **completely locally** on your Mac! 🎉

## Common Issues

### "Connection refused" error
**Problem:** LM Studio isn't running or API server isn't started
**Solution:** Open LM Studio → Local Server → Start Server

### "No model loaded" error
**Problem:** No model loaded in LM Studio
**Solution:** Load a model in LM Studio (Models tab → Load Model)

### Browser doesn't launch
**Problem:** Playwright browsers not installed
**Solution:** Run `playwright install chromium`

### Out of memory errors
**Problem:** Model too large for your RAM
**Solution:** Use smaller models:
- LLM: Try Llama-3.2-1B or Phi-3-mini
- Vision: Try Moondream2 (only 1.6B parameters)

### Slow execution
**Problem:** Model inference is slow
**Solution:**
- Use quantized models (Q4_K_M or Q5_K_M)
- Reduce max_tokens in .env
- Use smaller models
- Close other applications

## Next Steps

Now that you have MonitorLab running:

1. **Try the chat interface** - Most intuitive way to test websites
   ```bash
   monitorlab-chat
   ```

2. **Create custom pipelines** - Define test workflows in YAML
   - See `examples/` directory
   - Check `examples/README.md` for guidance

3. **Integrate into CI/CD** - Run after deployments
   ```bash
   monitorlab-run run my_test_pipeline.yaml
   ```

4. **Explore the Python API** - Build custom automation
   - See `examples/simple_usage.py`
   - Check main README for API docs

## Example Test Ideas

### After deployment validation:
```yaml
# post_deploy_check.yaml
name: "Post-Deploy Validation"
target_url: "https://your-site.com"
agents:
  - type: navigator
    task: "Navigate to {target_url}"
  - type: vision
    task: "Verify homepage renders correctly"
  - type: validator
    task: "Check that all critical links work"
```

### Login flow test:
```bash
# In chat mode
> Test the login form at https://myapp.com/login with test credentials
```

### Visual regression:
```bash
# In chat mode
> Take screenshots of https://myapp.com at mobile and desktop sizes and verify rendering
```

## Getting Help

- **Documentation**: See main README.md
- **Examples**: Browse `examples/` directory
- **Logs**: Check `monitorlab.log` for detailed info
- **Issues**: Report at GitHub Issues (if this is a repo)

## Pro Tips

1. **Run in headless mode for CI/CD:**
   ```env
   HEADLESS=true
   ```

2. **Adjust timeouts for slow sites:**
   ```env
   BROWSER_TIMEOUT=60000  # 60 seconds
   ```

3. **Save screenshots automatically:**
   ```env
   SCREENSHOT_DIR=./test-screenshots
   ```

4. **Use variables in pipelines:**
   ```bash
   monitorlab-run run test.yaml -v env=staging
   ```

Happy testing! 🚀
