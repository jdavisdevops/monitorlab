"""Interaction agent for complex user interactions like form filling."""

import logging
from typing import Dict, Any
from monitorlab.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class InteractionAgent(BaseAgent):
    """Agent specialized in user interactions like clicking, typing, form filling."""

    async def execute(self) -> Dict[str, Any]:
        """Execute interaction task.

        The LLM determines what interaction actions to take.

        Returns:
            Dictionary with interaction results
        """
        if not self.page_controller:
            raise RuntimeError("InteractionAgent requires a browser manager")

        # Ask LLM to plan interaction actions
        system_prompt = """You are a web interaction specialist. Given a task, determine what interaction actions are needed.

Respond in JSON format with this structure:
{
    "actions": [
        {"type": "click", "selector": "button.submit"},
        {"type": "fill", "selector": "input[name='email']", "value": "test@example.com"},
        {"type": "type", "selector": "input[name='search']", "text": "query", "delay": 50},
        {"type": "select", "selector": "select#country", "value": "US"},
        {"type": "check", "selector": "input[type='checkbox']#agree"},
        {"type": "uncheck", "selector": "input[type='checkbox']#marketing"},
        {"type": "wait_for_selector", "selector": "...", "state": "visible"},
        ...
    ]
}

Available action types:
- click: Click element (params: selector)
- fill: Fill input field instantly (params: selector, value)
- type: Type text with delay (params: selector, text, delay)
- select: Select dropdown option (params: selector, value)
- check: Check checkbox/radio (params: selector)
- uncheck: Uncheck checkbox (params: selector)
- wait_for_selector: Wait for element (params: selector, state)
- scroll_to: Scroll to element (params: selector)
"""

        # Get current page HTML context (first 2000 chars) to help LLM
        try:
            page_content = await self.page_controller.page.content()
            page_preview = page_content[:2000] if len(page_content) > 2000 else page_content
        except:
            page_preview = "Unable to get page content"

        planning_prompt = f"""Task: {self.task}

Current page URL: {self.page_controller.page.url}

Page preview (first 2000 chars of HTML):
{page_preview}

What interaction actions should be performed? Be specific with selectors.
If the task mentions form fields, use appropriate CSS selectors like input[name='...'], #id, .class, etc.
"""

        try:
            plan_json = await self.llm_client.extract_json(
                prompt=planning_prompt,
                system_prompt=system_prompt,
            )

            results = {
                "task": self.task,
                "plan": plan_json,
                "actions_performed": [],
                "success": True,
            }

            # Perform each action
            for action in plan_json.get("actions", []):
                action_type = action.get("type")
                action_result = {"type": action_type, "params": action}

                try:
                    if action_type == "click":
                        success = await self.page_controller.click(action["selector"])
                        action_result["success"] = success

                    elif action_type == "fill":
                        success = await self.page_controller.fill(
                            action["selector"], action["value"]
                        )
                        action_result["success"] = success

                    elif action_type == "type":
                        success = await self.page_controller.type_text(
                            action["selector"],
                            action["text"],
                            delay=action.get("delay", 50),
                        )
                        action_result["success"] = success

                    elif action_type == "select":
                        success = await self.page_controller.select_option(
                            action["selector"], action["value"]
                        )
                        action_result["success"] = success

                    elif action_type == "check":
                        success = await self.page_controller.check(action["selector"])
                        action_result["success"] = success

                    elif action_type == "uncheck":
                        success = await self.page_controller.uncheck(action["selector"])
                        action_result["success"] = success

                    elif action_type == "wait_for_selector":
                        success = await self.page_controller.wait_for_selector(
                            action["selector"],
                            state=action.get("state", "visible"),
                        )
                        action_result["success"] = success

                    elif action_type == "scroll_to":
                        success = await self.page_controller.scroll_to(action["selector"])
                        action_result["success"] = success

                    else:
                        logger.warning(f"Unknown action type: {action_type}")
                        action_result["success"] = False

                except Exception as e:
                    logger.error(f"Action {action_type} failed: {e}")
                    action_result["success"] = False
                    action_result["error"] = str(e)

                results["actions_performed"].append(action_result)

                # If action failed and it's critical, stop
                if not action_result.get("success", True):
                    results["success"] = False
                    # Optionally continue or break based on action importance
                    # For now, we continue

            # Get final page info
            page_info = await self.page_controller.get_page_info()
            results["final_url"] = page_info["url"]
            results["page_title"] = page_info["title"]

            # Determine overall success
            failed_actions = [a for a in results["actions_performed"] if not a.get("success", True)]
            if failed_actions:
                results["success"] = False
                results["failed_actions"] = failed_actions
            else:
                results["success"] = True

            return results

        except Exception as e:
            logger.exception(f"Interaction agent execution failed: {e}")
            return {
                "task": self.task,
                "success": False,
                "error": str(e),
            }
