"""Navigator agent for page navigation and basic interactions."""

import logging
from typing import Dict, Any, Optional
from monitorlab.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class NavigatorAgent(BaseAgent):
    """Agent specialized in page navigation and waiting for elements."""

    async def execute(self) -> Dict[str, Any]:
        """Execute navigation task.

        The LLM determines what navigation actions to take based on the task.

        Returns:
            Dictionary with navigation results
        """
        if not self.page_controller:
            raise RuntimeError("NavigatorAgent requires a browser manager")

        # Ask LLM to plan navigation actions
        system_prompt = """You are a web navigation specialist. Given a task, determine what navigation actions are needed.

Respond in JSON format with this structure:
{
    "url": "URL to navigate to (if needed)",
    "wait_for": "CSS selector to wait for (optional)",
    "wait_state": "load state to wait for: load/domcontentloaded/networkidle (default: load)",
    "actions": [
        {"type": "wait_for_selector", "selector": "...", "state": "visible"},
        {"type": "scroll_to", "selector": "..."},
        ...
    ]
}

Available action types:
- wait_for_selector: Wait for element (params: selector, state)
- wait_for_url: Wait for URL pattern (params: url)
- scroll_to: Scroll element into view (params: selector)
- wait_timeout: Wait for time (params: timeout in ms)
"""

        planning_prompt = f"""Task: {self.task}

Current page URL: {self.page_controller.page.url if hasattr(self.page_controller.page, 'url') else 'Not loaded yet'}

What navigation actions should be performed?"""

        try:
            plan_json = await self.llm_client.extract_json(
                prompt=planning_prompt,
                system_prompt=system_prompt,
            )

            results = {
                "task": self.task,
                "plan": plan_json,
                "actions_performed": [],
                "final_url": None,
                "success": True,
            }

            # Navigate to URL if specified
            if plan_json.get("url"):
                url = plan_json["url"]
                wait_state = plan_json.get("wait_state", "load")
                success = await self.page_controller.navigate(url, wait_until=wait_state)

                results["actions_performed"].append({
                    "type": "navigate",
                    "url": url,
                    "success": success,
                })

                if not success:
                    results["success"] = False
                    return results

            # Wait for specific selector if specified
            if plan_json.get("wait_for"):
                selector = plan_json["wait_for"]
                success = await self.page_controller.wait_for_selector(selector)
                results["actions_performed"].append({
                    "type": "wait_for_selector",
                    "selector": selector,
                    "success": success,
                })

            # Perform additional actions
            for action in plan_json.get("actions", []):
                action_type = action.get("type")
                action_result = {"type": action_type, "params": action}

                try:
                    if action_type == "wait_for_selector":
                        success = await self.page_controller.wait_for_selector(
                            action["selector"],
                            state=action.get("state", "visible"),
                        )
                        action_result["success"] = success

                    elif action_type == "wait_for_url":
                        success = await self.page_controller.wait_for_url(action["url"])
                        action_result["success"] = success

                    elif action_type == "scroll_to":
                        success = await self.page_controller.scroll_to(action["selector"])
                        action_result["success"] = success

                    elif action_type == "wait_timeout":
                        await self.page_controller.wait_for_timeout(action["timeout"])
                        action_result["success"] = True

                    else:
                        logger.warning(f"Unknown action type: {action_type}")
                        action_result["success"] = False

                except Exception as e:
                    logger.error(f"Action {action_type} failed: {e}")
                    action_result["success"] = False
                    action_result["error"] = str(e)

                results["actions_performed"].append(action_result)

            # Get final page info
            page_info = await self.page_controller.get_page_info()
            results["final_url"] = page_info["url"]
            results["page_title"] = page_info["title"]

            # Determine overall success
            failed_actions = [a for a in results["actions_performed"] if not a.get("success", True)]
            if failed_actions:
                results["success"] = False
                results["failed_actions"] = failed_actions

            return results

        except Exception as e:
            logger.exception(f"Navigator agent execution failed: {e}")
            return {
                "task": self.task,
                "success": False,
                "error": str(e),
            }
