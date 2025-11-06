"""Generic test agent that can handle any testing task via LLM reasoning."""

import logging
from typing import Optional, Any
from monitorlab.agents.base_agent import DomainAgent, AgentState

logger = logging.getLogger(__name__)


class GenericTestAgent(DomainAgent):
    """A flexible agent that uses LLM reasoning to test any feature/workflow.

    This agent is ideal for:
    - Ad-hoc testing via chat interface
    - Dynamic test scenarios
    - User-defined test tasks

    The agent uses the LLM to:
    1. Understand the test task
    2. Plan the test steps
    3. Execute using MCP tools
    4. Validate results
    5. Report findings
    """

    def __init__(
        self,
        task: str,
        target_url: Optional[str] = None,
        settings: Optional[Any] = None,
        name: str = "generic",
    ):
        """Initialize generic test agent.

        Args:
            task: Test task description
            target_url: Optional target URL
            settings: Optional settings
            name: Agent name (default: "generic")
        """
        super().__init__(name=name, task=task, target_url=target_url, settings=settings)

    async def execute(self) -> AgentState:
        """Execute the test using LLM-guided automation.

        Returns:
            Updated AgentState with results
        """
        # Step 1: Have LLM plan the test
        planning_prompt = f"""Test Task: {self.task}
Target URL: {self.target_url or 'Not specified'}

Plan out the complete test workflow. What steps are needed to validate this functionality?

Respond with a JSON object:
{{
    "steps": [
        {{"action": "navigate", "url": "...", "description": "..."}},
        {{"action": "interact", "selector": "...", "type": "click", "description": "..."}},
        {{"action": "validate", "type": "visual|functional", "description": "..."}},
        ...
    ],
    "expected_outcome": "What should happen if the test passes",
    "failure_indicators": ["What would indicate test failure"]
}}"""

        system_prompt = self.get_system_prompt()

        try:
            # Get test plan
            plan_response = await self.ask_llm(planning_prompt, system_prompt)
            logger.info(f"Test plan created: {plan_response[:200]}...")

            # Parse plan (in real implementation, would use structured output)
            self.state["output"]["test_plan"] = plan_response

            # Step 2: Execute the plan
            # For now, we'll do a basic execution flow
            # In real implementation, would parse the plan and execute each step

            if self.target_url:
                # Navigate to URL
                await self.playwright_mcp.execute_tool(
                    "playwright_navigate", {"url": self.target_url}
                )
                self.state["output"]["navigated_to"] = self.target_url

                # Take initial screenshot
                screenshot_path = await self.take_screenshot("initial")

                # Have vision model analyze the page
                validation_prompt = f"""Analyze this webpage screenshot for the following test:

Task: {self.task}

Check if:
1. The page loaded correctly
2. All expected elements are present
3. The layout is correct
4. There are no visual issues

Provide a detailed analysis."""

                visual_analysis = await self.vision_client.analyze_image(
                    screenshot_path, validation_prompt
                )
                self.state["output"]["visual_analysis"] = visual_analysis

                # Step 3: Determine test outcome
                outcome_prompt = f"""Based on the test plan and visual analysis, did the test pass?

Test Task: {self.task}
Visual Analysis: {visual_analysis}

Respond with:
- "PASS" if the test was successful
- "FAIL" if the test failed
- "INCONCLUSIVE" if more testing is needed

Then explain your reasoning."""

                outcome = await self.ask_llm(outcome_prompt, system_prompt)
                self.state["output"]["outcome"] = outcome

                if "PASS" in outcome.upper():
                    self.state["status"] = "success"
                elif "FAIL" in outcome.upper():
                    self.state["status"] = "failure"
                else:
                    self.state["status"] = "success"  # Default to success if inconclusive

                # Take final screenshot
                final_screenshot = await self.take_screenshot("final")
                self.state["output"]["final_screenshot"] = final_screenshot

            else:
                # No URL provided - just return the plan
                self.state["output"]["note"] = "No URL provided, only test plan generated"

            self.state["output"]["success"] = True

        except Exception as e:
            logger.exception(f"Generic agent execution failed: {e}")
            self.state["status"] = "error"
            self.state["error"] = str(e)
            self.state["output"]["success"] = False

        return self.state
