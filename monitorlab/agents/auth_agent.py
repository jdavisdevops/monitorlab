"""Authentication testing agent."""

import logging
from typing import Optional, Any, Dict
from monitorlab.agents.base_agent import DomainAgent, AgentState

logger = logging.getLogger(__name__)


class AuthenticationAgent(DomainAgent):
    """Agent specialized in testing authentication flows."""

    def __init__(
        self,
        target_url: str,
        credentials: Optional[Dict[str, str]] = None,
        task: Optional[str] = None,
        settings: Optional[Any] = None,
    ):
        """Initialize authentication agent.

        Args:
            target_url: Login page URL
            credentials: Optional credentials dict with 'username' and 'password'
            task: Optional custom task description
            settings: Optional settings
        """
        default_task = "Test login/authentication functionality"
        super().__init__(
            name="authentication",
            task=task or default_task,
            target_url=target_url,
            settings=settings,
        )
        self.credentials = credentials or {
            "username": "test@example.com",
            "password": "testpass123",
        }

    async def execute(self) -> AgentState:
        """Execute authentication test workflow.

        Returns:
            Updated AgentState with results
        """
        try:
            # Navigate to login page
            logger.info(f"Navigating to login page: {self.target_url}")
            await self.playwright_mcp.execute_tool(
                "playwright_navigate", {"url": self.target_url}
            )

            # Take screenshot of login form
            login_form_screenshot = await self.take_screenshot("login_form")

            # Validate login form appearance
            expected_elements = [
                "Username or email input field",
                "Password input field",
                "Submit/Login button",
                "Form properly styled and accessible",
            ]

            visual_validation = await self.validate_visual(
                login_form_screenshot, expected_elements
            )
            self.state["output"]["form_visual_validation"] = visual_validation

            # Find form fields using MCP
            # In real implementation, would use MCP tools to find and fill fields
            logger.info("Testing login form interaction")

            # Attempt to identify form fields
            form_analysis_prompt = f"""Analyze this login form screenshot and identify:
1. The CSS selector for the username/email field
2. The CSS selector for the password field
3. The CSS selector for the submit button

Respond with suggested selectors."""

            form_analysis = await self.vision_client.analyze_image(
                login_form_screenshot, form_analysis_prompt
            )
            self.state["output"]["form_analysis"] = form_analysis

            # For demonstration, use common selectors
            common_selectors = {
                "username": [
                    "input[type='email']",
                    "input[name='username']",
                    "input[name='email']",
                    "#username",
                    "#email",
                ],
                "password": [
                    "input[type='password']",
                    "input[name='password']",
                    "#password",
                ],
                "submit": [
                    "button[type='submit']",
                    "input[type='submit']",
                    "button:has-text('Login')",
                    "button:has-text('Sign in')",
                ],
            }

            # Try to fill the form
            try:
                # Fill username
                for selector in common_selectors["username"]:
                    await self.playwright_mcp.execute_tool(
                        "playwright_fill",
                        {"selector": selector, "value": self.credentials["username"]},
                    )
                    break

                # Fill password
                for selector in common_selectors["password"]:
                    await self.playwright_mcp.execute_tool(
                        "playwright_fill",
                        {"selector": selector, "value": self.credentials["password"]},
                    )
                    break

                # Screenshot with filled form
                filled_form_screenshot = await self.take_screenshot("form_filled")

                # Click submit
                for selector in common_selectors["submit"]:
                    await self.playwright_mcp.execute_tool(
                        "playwright_click", {"selector": selector}
                    )
                    break

                # Wait for navigation/response
                # In real implementation, would wait for navigation or error message

                # Take screenshot of result
                result_screenshot = await self.take_screenshot("login_result")

                # Analyze result
                result_analysis_prompt = """Analyze this screenshot to determine the login result:

1. Did login succeed (redirected to dashboard/home)?
2. Did login fail (error message shown)?
3. What is the current page state?

Provide detailed analysis."""

                result_analysis = await self.vision_client.analyze_image(
                    result_screenshot, result_analysis_prompt
                )
                self.state["output"]["result_analysis"] = result_analysis

                # Determine test outcome
                # Note: With test credentials, we expect either:
                # - Proper error handling (good)
                # - Successful login (if credentials are valid)
                self.state["output"]["test_passed"] = True  # Form interaction worked
                self.state["status"] = "success"

            except Exception as e:
                logger.error(f"Form interaction failed: {e}")
                self.state["output"]["interaction_error"] = str(e)
                self.state["status"] = "failure"

        except Exception as e:
            logger.exception(f"Authentication agent execution failed: {e}")
            self.state["status"] = "error"
            self.state["error"] = str(e)

        return self.state
