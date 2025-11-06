"""Vision agent for visual validation using vision models."""

import logging
from pathlib import Path
from typing import Dict, Any
from monitorlab.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class VisionAgent(BaseAgent):
    """Agent specialized in visual validation using vision models."""

    async def execute(self) -> Dict[str, Any]:
        """Execute vision validation task.

        Takes a screenshot and analyzes it with a vision model.

        Returns:
            Dictionary with validation results
        """
        if not self.page_controller:
            raise RuntimeError("VisionAgent requires a browser manager")

        # Take screenshot
        screenshot_dir = Path(self.settings.screenshot_dir)
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = screenshot_dir / f"vision_{self.agent_id}.jpg"

        try:
            await self.browser_manager.take_screenshot(
                self.page_controller.page,
                path=str(screenshot_path),
            )

            results = {
                "task": self.task,
                "screenshot_path": str(screenshot_path),
                "success": True,
            }

            # Ask LLM what we should be checking for
            system_prompt = """You are a QA specialist planning visual validation checks.
Given a task description, determine what visual elements should be validated.

Respond in JSON format:
{
    "expected_elements": ["list of UI elements that should be present"],
    "additional_checks": ["list of visual quality checks like 'no broken images', 'proper styling', etc."]
}
"""

            planning_prompt = f"""Task: {self.task}
Current URL: {self.page_controller.page.url}

What visual elements and checks should be validated on this page?"""

            try:
                plan_json = await self.llm_client.extract_json(
                    prompt=planning_prompt,
                    system_prompt=system_prompt,
                )

                expected_elements = plan_json.get("expected_elements", [])
                additional_checks = plan_json.get("additional_checks", [])

                results["plan"] = plan_json

                # Perform visual validation
                validation_result = await self.vision_client.validate_rendering(
                    screenshot_path,
                    expected_elements=expected_elements,
                    additional_checks=additional_checks,
                )

                results["validation"] = validation_result
                results["success"] = validation_result.get("overall_valid", False)

            except Exception as e:
                logger.error(f"Vision validation planning/execution failed: {e}")
                # Fall back to general analysis
                analysis = await self.vision_client.analyze_image(
                    screenshot_path,
                    prompt=f"Analyze this webpage screenshot for the following task: {self.task}",
                )
                results["analysis"] = analysis
                results["success"] = True  # We got some analysis at least

            # Get page info
            page_info = await self.page_controller.get_page_info()
            results["page_url"] = page_info["url"]
            results["page_title"] = page_info["title"]

            return results

        except Exception as e:
            logger.exception(f"Vision agent execution failed: {e}")
            return {
                "task": self.task,
                "success": False,
                "error": str(e),
            }
