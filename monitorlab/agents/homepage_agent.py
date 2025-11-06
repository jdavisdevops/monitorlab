"""Homepage testing agent."""

import logging
from typing import Optional, Any
from monitorlab.agents.base_agent import DomainAgent, AgentState

logger = logging.getLogger(__name__)


class HomepageAgent(DomainAgent):
    """Agent specialized in testing homepage functionality."""

    def __init__(
        self,
        target_url: str,
        task: Optional[str] = None,
        settings: Optional[Any] = None,
    ):
        """Initialize homepage agent.

        Args:
            target_url: Homepage URL to test
            task: Optional custom task description
            settings: Optional settings
        """
        default_task = "Test homepage loading, layout, and core elements"
        super().__init__(
            name="homepage",
            task=task or default_task,
            target_url=target_url,
            settings=settings,
        )

    async def execute(self) -> AgentState:
        """Execute homepage test workflow.

        Returns:
            Updated AgentState with results
        """
        try:
            # Navigate to homepage
            logger.info(f"Navigating to homepage: {self.target_url}")
            await self.playwright_mcp.execute_tool(
                "playwright_navigate",
                {"url": self.target_url, "wait_until": "networkidle"},
            )

            # Take initial screenshot
            screenshot_path = await self.take_screenshot("homepage_load")

            # Validate page loaded
            expected_elements = [
                "Navigation menu or header",
                "Main content area",
                "Logo",
                "Footer (if applicable)",
                "Call-to-action buttons or links",
            ]

            # Visual validation
            visual_validation = await self.validate_visual(screenshot_path, expected_elements)
            self.state["output"]["visual_validation"] = visual_validation

            # Get page title
            title_result = await self.playwright_mcp.execute_tool(
                "playwright_evaluate", {"expression": "document.title"}
            )
            self.state["output"]["page_title"] = title_result

            # Check for common homepage elements
            checks = {
                "navigation": "nav, header, [role='navigation']",
                "main_content": "main, [role='main'], #content",
                "footer": "footer, [role='contentinfo']",
            }

            element_checks = {}
            for name, selector in checks.items():
                result = await self.playwright_mcp.execute_tool(
                    "playwright_wait_for_selector",
                    {"selector": selector, "state": "attached"},
                )
                element_checks[name] = result
                logger.info(f"Element check {name}: {result}")

            self.state["output"]["element_checks"] = element_checks

            # Have LLM analyze overall page quality
            analysis_prompt = f"""Analyze this homepage screenshot for quality and completeness.

Check for:
1. Professional appearance
2. Clear navigation
3. Readable text
4. Proper layout
5. No broken images or missing content
6. Overall user experience

Provide a comprehensive assessment."""

            llm_analysis = await self.vision_client.analyze_image(
                screenshot_path, analysis_prompt
            )
            self.state["output"]["llm_analysis"] = llm_analysis

            # Determine success
            all_elements_found = all(element_checks.values())
            visual_valid = visual_validation.get("overall_valid", False)

            self.state["output"]["all_elements_found"] = all_elements_found
            self.state["output"]["visual_valid"] = visual_valid
            self.state["output"]["test_passed"] = all_elements_found and visual_valid

            if self.state["output"]["test_passed"]:
                self.state["status"] = "success"
            else:
                self.state["status"] = "failure"

        except Exception as e:
            logger.exception(f"Homepage agent execution failed: {e}")
            self.state["status"] = "error"
            self.state["error"] = str(e)

        return self.state
