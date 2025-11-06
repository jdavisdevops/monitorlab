# MonitorLab Examples

This directory contains example pipelines and usage demonstrations for MonitorLab.

## Pipeline Examples

### basic_website_check.yaml
Simple smoke test that verifies a website loads and renders correctly.

**Usage:**
```bash
monitorlab-run run basic_website_check.yaml
```

**What it does:**
1. Navigates to the target URL
2. Takes a screenshot and validates rendering
3. Verifies basic page elements

### login_form_test.yaml
Tests login form functionality including form validation and submission.

**Usage:**
```bash
monitorlab-run run login_form_test.yaml
```

**What it does:**
1. Navigates to login page
2. Validates form rendering
3. Fills in credentials
4. Submits form and verifies result

### comprehensive_test.yaml
Complete e-commerce workflow test including search and product viewing.

**Usage:**
```bash
monitorlab-run run comprehensive_test.yaml
```

**What it does:**
1. Loads homepage and validates rendering
2. Performs product search
3. Validates search results
4. Opens product detail page
5. Validates product information

## Programmatic Usage

### simple_usage.py
Demonstrates how to use MonitorLab programmatically in Python.

**Usage:**
```bash
python simple_usage.py
```

**Key concepts:**
- Creating an orchestrator
- Spawning agents
- Running agents sequentially or in parallel
- Accessing results

## Creating Custom Pipelines

### Pipeline YAML Structure

```yaml
name: "Your Pipeline Name"
description: "What this pipeline does"
target_url: "https://your-site.com"
mode: "sequential"  # or "parallel"

agents:
  - type: navigator  # or interaction, vision, validator
    task: "Describe what this agent should do"
    # Optional agent-specific parameters

metadata:
  author: "Your Name"
  version: "1.0"
  tags: ["tag1", "tag2"]
```

### Agent Types

**Navigator Agent**
- Purpose: Page navigation, waiting for elements
- Use when: You need to load pages, wait for content
- Example task: "Navigate to https://example.com and wait for page load"

**Interaction Agent**
- Purpose: User interactions (clicks, form filling)
- Use when: You need to interact with page elements
- Example task: "Click the login button and fill in the form"

**Vision Agent**
- Purpose: Visual validation using vision models
- Use when: You need to verify CSS, images, layout
- Example task: "Verify the page renders correctly with no visual issues"

**Validator Agent**
- Purpose: Functional validation and assertions
- Use when: You need to check page state, elements, URLs
- Example task: "Verify the page title and check that the submit button is enabled"

## Variables in Pipelines

You can use variables in your pipeline YAML files:

```yaml
target_url: "https://example.com/{page_name}"

agents:
  - type: navigator
    task: "Navigate to {target_url}"
```

Then pass variables when running:

```bash
monitorlab-run run your_pipeline.yaml -v page_name=contact -v target_url=https://mysite.com
```

## Tips

1. **Start simple**: Begin with basic pipelines and add complexity gradually
2. **Sequential vs Parallel**: Use sequential mode when agents depend on each other, parallel for independent tasks
3. **Vision validation**: Vision agents are great for catching CSS/styling issues that functional tests might miss
4. **Task descriptions**: Be specific in agent tasks - the LLM uses these to determine actions
5. **Error handling**: Pipelines continue even if an agent fails, check results to see what succeeded

## Troubleshooting

**Pipeline fails immediately**
- Check that LM Studio is running and serving the API
- Verify your .env configuration
- Check logs in monitorlab.log

**Vision validation doesn't work**
- Ensure you have a vision model loaded in LM Studio
- Check that screenshots are being saved to the configured directory
- Try with a smaller/faster vision model first

**Browser automation fails**
- Run `playwright install` to ensure browsers are installed
- Try running in non-headless mode (set HEADLESS=false)
- Check if the website requires specific viewport sizes

## Next Steps

- Modify these examples for your own websites
- Create custom pipelines for your specific workflows
- Integrate MonitorLab into your CI/CD pipeline
- Explore the Python API for advanced use cases
