# MonitorLab Troubleshooting Guide

Common issues and their solutions.

## Installation Issues

### Playwright Installation Fails

**Error:** `playwright install` fails or browsers don't download

**Solutions:**
```bash
# Try with specific browser
playwright install chromium

# Install system dependencies (Linux)
playwright install-deps

# Check if browsers are installed
playwright --version
```

### Python Package Installation Fails

**Error:** `pip install -e .` fails

**Solutions:**
```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Use Python 3.10 or higher
python --version

# Create fresh virtual environment
python -m venv venv
source venv/bin/activate
pip install -e .
```

## LM Studio Issues

### Cannot Connect to LM Studio

**Error:** `Connection refused` or `Connection error`

**Checklist:**
1. ✅ LM Studio is running
2. ✅ Local Server is started (green indicator)
3. ✅ Port matches (default: 1234)
4. ✅ Model is loaded

**Solutions:**
```bash
# Test LM Studio API manually
curl http://localhost:1234/v1/models

# Check port in LM Studio → Local Server → Server Settings
# Update .env if port is different
LLM_API_BASE=http://localhost:YOUR_PORT/v1
```

### Model Loading Errors

**Error:** Model fails to load or runs out of memory

**Solutions:**

For 16GB RAM Macs:
- **LLM**: Use 3B models with Q4 quantization
  - ✅ Llama-3.2-3B-Instruct-Q4
  - ✅ Phi-3-mini-Q4
  - ❌ Avoid 7B+ models

- **Vision**: Use efficient models
  - ✅ Moondream2 (1.6B)
  - ✅ LLaVA 1.6 7B Q4 (if not running LLM simultaneously)
  - ❌ Avoid unquantized models

**Model Settings in LM Studio:**
- Set "Max Context Length" to 2048 or 4096
- Enable "GPU Offload" (Metal acceleration)
- Reduce "Number of GPU Layers" if memory issues persist

### Slow Inference

**Problem:** Models are very slow to respond

**Solutions:**

1. **Use quantized models**
   - Q4_K_M or Q5_K_M quantization
   - Avoid F16 or F32 models

2. **Optimize LM Studio settings**
   - Enable all GPU layers
   - Reduce max context length
   - Use flash attention if available

3. **Close other applications**
   - Free up RAM
   - Stop other intensive processes

4. **Adjust MonitorLab timeouts** (in .env):
   ```env
   AGENT_TIMEOUT=600  # Increase if needed
   LLM_MAX_TOKENS=1000  # Reduce token generation
   ```

## Browser Automation Issues

### Browser Doesn't Launch

**Error:** Browser fails to start or launch

**Solutions:**
```bash
# Reinstall Playwright browsers
playwright install --force chromium

# Check if running in headless mode
# Try non-headless in .env
HEADLESS=false

# Check permissions (macOS)
# System Preferences → Security & Privacy → Allow
```

### Page Load Timeouts

**Error:** `Timeout waiting for page load`

**Solutions:**

1. **Increase timeout** (in .env):
   ```env
   BROWSER_TIMEOUT=60000  # 60 seconds
   ```

2. **Use different wait strategy**:
   - Try `networkidle` instead of `load`
   - Modify in agent tasks or code

3. **Check website status**:
   - Verify site is accessible
   - Check for rate limiting
   - Test with simpler pages first

### Selector Not Found

**Error:** Element selector not found

**Solutions:**

1. **Verify selector**:
   - Use browser DevTools to test selector
   - Try more specific selectors
   - Check if element is in iframe

2. **Wait for element**:
   - Ensure navigator agent runs first
   - Add explicit waits in pipeline

3. **Check timing**:
   - Page might still be loading
   - Try adding wait_for_selector before interaction

## Vision Model Issues

### Vision Model Not Working

**Error:** Vision analysis fails or returns errors

**Solutions:**

1. **Verify vision model is loaded**:
   - Check LM Studio has vision model loaded
   - Confirm model supports image input

2. **Check screenshot generation**:
   ```bash
   # Verify screenshots directory
   ls -la screenshots/

   # Check permissions
   chmod 755 screenshots/
   ```

3. **Reduce image size** (in .env):
   ```env
   DEFAULT_VIEWPORT_WIDTH=1280
   DEFAULT_VIEWPORT_HEIGHT=720
   SCREENSHOT_QUALITY=70
   ```

4. **Try different vision model**:
   - Moondream2: Fastest, good quality
   - LLaVA 1.6: Better accuracy, slower
   - BakLLaVA: Alternative option

### Poor Vision Analysis Quality

**Problem:** Vision model gives inaccurate results

**Solutions:**

1. **Use larger vision model**:
   - Switch from 1B to 7B model
   - Use less quantization (Q5 vs Q4)

2. **Improve prompts**:
   - Be more specific in agent tasks
   - Provide more context

3. **Adjust screenshot settings**:
   - Increase quality
   - Capture full page if needed

## Agent Execution Issues

### Agent Timeout

**Error:** Agent times out before completing

**Solutions:**

1. **Increase timeout** (in .env):
   ```env
   AGENT_TIMEOUT=600  # 10 minutes
   ```

2. **Simplify agent tasks**:
   - Break complex tasks into multiple agents
   - Use sequential mode for dependent tasks

3. **Check for blocking operations**:
   - Verify page is not stuck
   - Check for unexpected popups/modals

### Agent Fails with JSON Parse Error

**Error:** `Could not extract valid JSON`

**Solutions:**

1. **Simplify task description**:
   - Use clearer, more explicit instructions
   - Break down complex tasks

2. **Adjust LLM temperature**:
   ```python
   # In code
   llm_client.generate(prompt, temperature=0.1)  # More consistent
   ```

3. **Use different model**:
   - Try larger LLM for better JSON generation
   - Ensure model is instruction-tuned

### Multiple Agents Fail in Parallel Mode

**Error:** Agents fail when running in parallel

**Solutions:**

1. **Reduce concurrency** (in .env):
   ```env
   MAX_CONCURRENT_AGENTS=2  # Reduce from 3
   ```

2. **Use sequential mode**:
   ```yaml
   # In pipeline
   mode: "sequential"
   ```

3. **Check resource limits**:
   - Monitor RAM usage
   - Close unnecessary applications

## Pipeline Issues

### Pipeline YAML Syntax Error

**Error:** YAML parsing fails

**Solutions:**

1. **Validate YAML syntax**:
   ```bash
   # Use online YAML validator
   # Check indentation (use spaces, not tabs)
   ```

2. **Check example pipelines**:
   ```bash
   # Compare with working examples
   cat examples/basic_website_check.yaml
   ```

3. **Common YAML mistakes**:
   - Inconsistent indentation
   - Missing quotes around special characters
   - Incorrect list syntax

### Variables Not Substituted

**Problem:** Variables like `{target_url}` not replaced

**Solutions:**

1. **Verify variable format**:
   - Use `{variable_name}` format
   - Check spelling matches

2. **Pass variables correctly**:
   ```bash
   monitorlab-run run pipeline.yaml -v target_url=https://example.com
   ```

3. **Check variable scope**:
   - Variables are substituted in agent tasks
   - Not in agent type or other fields

## Performance Issues

### High Memory Usage

**Problem:** MonitorLab uses too much RAM

**Solutions:**

1. **Use smaller models**:
   - LLM: 1B-3B models
   - Vision: Moondream2

2. **Reduce concurrent agents**:
   ```env
   MAX_CONCURRENT_AGENTS=1
   ```

3. **Close browsers between tests**:
   ```python
   # In code
   await orchestrator.teardown()
   ```

4. **Monitor with Activity Monitor** (macOS):
   - Check what's using memory
   - Restart LM Studio if needed

### Slow Execution

**Problem:** Tests take too long to complete

**Solutions:**

1. **Use faster models**:
   - 1B-3B parameter models
   - Q4 quantization

2. **Optimize pipeline**:
   - Run independent agents in parallel
   - Remove unnecessary validation steps

3. **Reduce LLM token generation**:
   ```env
   LLM_MAX_TOKENS=1000
   VISION_MAX_TOKENS=500
   ```

4. **Use headless mode**:
   ```env
   HEADLESS=true
   ```

## Debugging Tips

### Enable Debug Logging

```env
# In .env
LOG_LEVEL=DEBUG
```

Or in code:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Logs

```bash
# View real-time logs
tail -f monitorlab.log

# Search for errors
grep ERROR monitorlab.log

# View last 100 lines
tail -100 monitorlab.log
```

### Test Components Individually

```python
# Test LLM connection
from monitorlab.models import LLMClient
import asyncio

async def test():
    client = LLMClient()
    response = await client.generate("Say hello")
    print(response)

asyncio.run(test())
```

```python
# Test browser automation
from monitorlab.browser import BrowserManager
import asyncio

async def test():
    manager = BrowserManager()
    await manager.start()
    page = await manager.create_page("test")
    await page.goto("https://example.com")
    print(f"Title: {await page.title()}")
    await manager.stop()

asyncio.run(test())
```

### Run with Minimal Configuration

Create a minimal test:
```python
# minimal_test.py
import asyncio
from monitorlab import AgentOrchestrator, NavigatorAgent

async def main():
    orch = AgentOrchestrator()
    await orch.setup()
    orch.spawn_agent(NavigatorAgent, task="Navigate to https://example.com")
    results = await orch.run()
    print(results[0].status)
    await orch.teardown()

asyncio.run(main())
```

## Getting Help

If you're still stuck:

1. **Check logs** in `monitorlab.log`
2. **Search existing issues** on GitHub
3. **Create detailed issue** with:
   - Error message
   - Steps to reproduce
   - Environment info (OS, Python version, etc.)
   - Relevant logs
   - What you've tried

## Common Error Messages

### "Model not found"
→ Load a model in LM Studio

### "Connection refused"
→ Start LM Studio Local Server

### "Playwright not installed"
→ Run `playwright install`

### "Permission denied"
→ Check file/directory permissions

### "Timeout"
→ Increase timeout settings

### "Out of memory"
→ Use smaller models, reduce concurrency

### "JSON parse error"
→ Simplify task, reduce temperature

### "Element not found"
→ Check selector, add wait time

## System Requirements Reminder

**Minimum:**
- Mac with M1/M2/M3 chip
- 16GB RAM
- 10GB free disk space
- macOS 12+ (Monterey or later)

**Recommended:**
- 32GB RAM for larger models
- SSD for better performance
- Latest macOS version

## Still Having Issues?

Create an issue with this information:

```
**Environment:**
- OS: macOS X.X
- Python version: X.X.X
- MonitorLab version: X.X.X
- LM Studio version: X.X.X

**Problem:**
[Clear description]

**Steps to reproduce:**
1.
2.
3.

**Expected behavior:**
[What should happen]

**Actual behavior:**
[What actually happens]

**Logs:**
```
[Paste relevant logs]
```

**What I've tried:**
-
-
```
