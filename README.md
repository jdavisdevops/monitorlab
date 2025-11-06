# MonitorLab

AI-enhanced website monitoring and validation system with vision capabilities, powered by locally-hosted LLMs.

## Overview

MonitorLab is a multi-agent framework for automated website testing and validation using:
- **Local LLMs** via LM Studio for privacy and control
- **Vision models** for visual validation of CSS, images, and rendering
- **Browser automation** with Playwright for realistic interactions
- **Multi-agent architecture** for parallel testing and intelligent coordination
- **Chat interface** for interactive agent spawning and ad-hoc testing

## Features

- 🤖 **Multi-Agent Framework**: Spawn specialized agents for different testing tasks
- 👁️ **Vision Validation**: AI-powered visual verification of website rendering
- 🔒 **Privacy First**: All models run locally on your Mac (M-series optimized)
- 🌐 **Browser Automation**: Full Playwright integration for realistic testing
- 💬 **Chat Interface**: Interactive agent spawning via natural language
- 📋 **Testing Pipelines**: Define and run comprehensive test suites
- 🔄 **Post-Deployment Validation**: Verify changes after code updates

## Architecture

```
monitorlab/
├── core/           # Core framework and orchestration
├── agents/         # Agent implementations (Navigator, Validator, Tester)
├── browser/        # Browser automation wrapper
├── models/         # LLM and vision model clients
├── pipelines/      # Testing pipeline framework
├── chat/           # Interactive chat interface
├── config/         # Configuration management
└── examples/       # Example pipelines and usage
```

## Requirements

- **Hardware**: Mac with M-series chip, 16GB+ RAM
- **Software**: Python 3.10+, LM Studio
- **Models**:
  - LLM: Llama 3.2 3B or similar (for reasoning)
  - Vision: LLaVA 1.6 7B or Moondream2 (for visual validation)

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium
```

### 2. Configure LM Studio

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Load your preferred models:
   - **LLM**: `TheBloke/Llama-3.2-3B-Instruct-GGUF` or similar
   - **Vision**: `llava-v1.6-7b` or `vikhyatk/moondream2`
3. Start the local API server (port 1234 by default)

### 3. Configure MonitorLab

Create a `.env` file:

```env
# LM Studio API Configuration
LLM_API_BASE=http://localhost:1234/v1
LLM_API_KEY=not-needed
LLM_MODEL=local-model

# Vision Model Configuration
VISION_API_BASE=http://localhost:1234/v1
VISION_MODEL=local-vision-model

# Browser Configuration
HEADLESS=false
BROWSER_TIMEOUT=30000
```

### 4. Run Your First Test

```bash
# Interactive chat mode
monitorlab-chat

# Run a predefined pipeline
monitorlab-run --pipeline examples/basic_website_check.yaml
```

## Usage Examples

### Interactive Chat Mode

```python
from monitorlab.chat import ChatInterface

chat = ChatInterface()
chat.start()

# In chat:
# > Check if https://example.com loads correctly
# > Verify the login form works on https://myapp.com
# > Take screenshots of https://myapp.com across different viewports
```

### Programmatic Usage

```python
from monitorlab import AgentOrchestrator, NavigatorAgent, VisionAgent

# Create orchestrator
orchestrator = AgentOrchestrator()

# Spawn agents
navigator = orchestrator.spawn_agent(NavigatorAgent, task="navigate to https://example.com")
vision = orchestrator.spawn_agent(VisionAgent, task="verify page rendering")

# Run agents
await orchestrator.run()

# Get results
results = orchestrator.get_results()
```

### Define Testing Pipelines

```yaml
# my_test_pipeline.yaml
name: "Homepage Validation"
target_url: "https://myapp.com"

agents:
  - type: navigator
    task: "Navigate to homepage and wait for load"

  - type: interaction
    task: "Click on login button"
    wait_for: "input[name='username']"

  - type: vision
    task: "Verify login form is properly rendered"
    checks:
      - "Login form is visible"
      - "Username and password fields are present"
      - "Submit button is properly styled"

  - type: validator
    task: "Verify form functionality"
    actions:
      - fill: {selector: "input[name='username']", value: "test@example.com"}
      - fill: {selector: "input[name='password']", value: "test123"}
      - click: "button[type='submit']"
    expect:
      - url_contains: "/dashboard"
```

## Agent Types

### NavigatorAgent
Handles page navigation, waiting for elements, and basic interactions.

### InteractionAgent
Performs complex user interactions like form filling, clicking, scrolling.

### VisionAgent
Uses vision models to validate visual rendering, layout, and styling.

### ValidatorAgent
Validates functionality, checks assertions, and verifies expected outcomes.

### OrchestratorAgent
Coordinates multiple agents and manages test execution flow.

## Configuration

See `config/README.md` for detailed configuration options.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black monitorlab/
ruff check monitorlab/
```

## Model Recommendations

### For 16GB RAM (M-series Mac):

**LLM Options:**
- Llama 3.2 3B Instruct (best balance)
- Phi-3 Mini (3.8B, fast)
- Mistral 7B Q4 (more capable, slower)

**Vision Options:**
- Moondream2 (1.6B, fastest, good quality)
- LLaVA 1.6 7B Q4 (more accurate, requires more RAM)
- BakLLaVA (7B, good for detailed analysis)

## Troubleshooting

### Common Issues

**LM Studio Connection Error**
- Ensure LM Studio server is running
- Check the API port (default: 1234)
- Verify model is loaded in LM Studio

**Browser Automation Fails**
- Run `playwright install` to install browsers
- Check if running in headless mode helps
- Verify page load timeout settings

**Vision Model Memory Issues**
- Use smaller vision models (Moondream2)
- Process screenshots at lower resolution
- Reduce concurrent agent count

## License

MIT

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.
