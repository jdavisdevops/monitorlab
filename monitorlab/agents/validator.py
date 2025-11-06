"""Validator agent for functional validation and assertions."""

import logging
from typing import Dict, Any
from monitorlab.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ValidatorAgent(BaseAgent):
    """Agent specialized in validating functionality and making assertions."""

    async def execute(self) -> Dict[str, Any]:
        """Execute validation task.

        Validates page state, elements, and functionality.

        Returns:
            Dictionary with validation results
        """
        if not self.page_controller:
            raise RuntimeError("ValidatorAgent requires a browser manager")

        # Ask LLM to plan validation checks
        system_prompt = """You are a QA validation specialist. Given a task, determine what validation checks are needed.

Respond in JSON format with this structure:
{
    "validations": [
        {"type": "element_visible", "selector": "button.submit"},
        {"type": "element_has_text", "selector": "h1", "expected_text": "Welcome"},
        {"type": "element_has_attribute", "selector": "input#email", "attribute": "type", "expected_value": "email"},
        {"type": "url_contains", "pattern": "/dashboard"},
        {"type": "url_equals", "url": "https://example.com/page"},
        {"type": "element_enabled", "selector": "button.submit"},
        {"type": "element_count", "selector": ".item", "expected_count": 5},
        ...
    ]
}

Available validation types:
- element_visible: Check if element is visible (params: selector)
- element_has_text: Check element text content (params: selector, expected_text)
- element_has_attribute: Check element attribute (params: selector, attribute, expected_value)
- url_contains: Check if URL contains pattern (params: pattern)
- url_equals: Check if URL equals value (params: url)
- element_enabled: Check if element is enabled (params: selector)
- element_count: Check number of matching elements (params: selector, expected_count)
- page_title_contains: Check page title (params: text)
"""

        planning_prompt = f"""Task: {self.task}

Current page URL: {self.page_controller.page.url}
Current page title: {await self.page_controller.page.title()}

What validation checks should be performed to verify the task requirements?"""

        try:
            plan_json = await self.llm_client.extract_json(
                prompt=planning_prompt,
                system_prompt=system_prompt,
            )

            results = {
                "task": self.task,
                "plan": plan_json,
                "validations_performed": [],
                "all_passed": True,
            }

            # Perform each validation
            for validation in plan_json.get("validations", []):
                val_type = validation.get("type")
                val_result = {"type": val_type, "params": validation}

                try:
                    passed = False

                    if val_type == "element_visible":
                        passed = await self.page_controller.is_visible(validation["selector"])
                        val_result["passed"] = passed

                    elif val_type == "element_has_text":
                        text = await self.page_controller.get_text(validation["selector"])
                        expected = validation["expected_text"]
                        passed = text is not None and expected in text
                        val_result["passed"] = passed
                        val_result["actual_text"] = text

                    elif val_type == "element_has_attribute":
                        attr_value = await self.page_controller.get_attribute(
                            validation["selector"],
                            validation["attribute"],
                        )
                        expected = validation["expected_value"]
                        passed = attr_value == expected
                        val_result["passed"] = passed
                        val_result["actual_value"] = attr_value

                    elif val_type == "url_contains":
                        current_url = self.page_controller.page.url
                        pattern = validation["pattern"]
                        passed = pattern in current_url
                        val_result["passed"] = passed
                        val_result["actual_url"] = current_url

                    elif val_type == "url_equals":
                        current_url = self.page_controller.page.url
                        expected_url = validation["url"]
                        passed = current_url == expected_url
                        val_result["passed"] = passed
                        val_result["actual_url"] = current_url

                    elif val_type == "element_enabled":
                        passed = await self.page_controller.is_enabled(validation["selector"])
                        val_result["passed"] = passed

                    elif val_type == "element_count":
                        elements = await self.page_controller.page.query_selector_all(
                            validation["selector"]
                        )
                        count = len(elements)
                        expected = validation["expected_count"]
                        passed = count == expected
                        val_result["passed"] = passed
                        val_result["actual_count"] = count

                    elif val_type == "page_title_contains":
                        title = await self.page_controller.page.title()
                        text = validation["text"]
                        passed = text in title
                        val_result["passed"] = passed
                        val_result["actual_title"] = title

                    else:
                        logger.warning(f"Unknown validation type: {val_type}")
                        val_result["passed"] = False
                        val_result["error"] = f"Unknown validation type: {val_type}"

                except Exception as e:
                    logger.error(f"Validation {val_type} failed with error: {e}")
                    val_result["passed"] = False
                    val_result["error"] = str(e)

                results["validations_performed"].append(val_result)

                # Track overall pass/fail
                if not val_result.get("passed", False):
                    results["all_passed"] = False

            # Get final page info
            page_info = await self.page_controller.get_page_info()
            results["final_url"] = page_info["url"]
            results["page_title"] = page_info["title"]

            # Summary
            total = len(results["validations_performed"])
            passed = sum(1 for v in results["validations_performed"] if v.get("passed", False))
            results["summary"] = {
                "total_validations": total,
                "passed": passed,
                "failed": total - passed,
            }

            results["success"] = results["all_passed"]

            return results

        except Exception as e:
            logger.exception(f"Validator agent execution failed: {e}")
            return {
                "task": self.task,
                "success": False,
                "error": str(e),
            }
