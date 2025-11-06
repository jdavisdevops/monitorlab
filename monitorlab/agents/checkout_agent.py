"""Checkout flow testing agent."""

import logging
from typing import Optional, Any
from monitorlab.agents.base_agent import DomainAgent, AgentState

logger = logging.getLogger(__name__)


class CheckoutAgent(DomainAgent):
    """Agent specialized in testing e-commerce checkout flows."""

    def __init__(
        self,
        target_url: str,
        task: Optional[str] = None,
        settings: Optional[Any] = None,
    ):
        """Initialize checkout agent.

        Args:
            target_url: Checkout page or cart URL
            task: Optional custom task description
            settings: Optional settings
        """
        default_task = "Test checkout flow including cart, billing, and payment steps"
        super().__init__(
            name="checkout",
            task=task or default_task,
            target_url=target_url,
            settings=settings,
        )

    async def execute(self) -> AgentState:
        """Execute checkout test workflow.

        Returns:
            Updated AgentState with results
        """
        try:
            # Navigate to checkout/cart
            logger.info(f"Navigating to checkout: {self.target_url}")
            await self.playwright_mcp.execute_tool(
                "playwright_navigate", {"url": self.target_url}
            )

            # Take initial screenshot
            initial_screenshot = await self.take_screenshot("checkout_start")

            # Validate checkout page elements
            expected_elements = [
                "Shopping cart or order summary",
                "Product listings with prices",
                "Total price display",
                "Checkout or proceed button",
                "Payment method options (if on payment page)",
            ]

            visual_validation = await self.validate_visual(
                initial_screenshot, expected_elements
            )
            self.state["output"]["visual_validation"] = visual_validation

            # Analyze checkout flow with vision model
            checkout_analysis_prompt = """Analyze this checkout page screenshot:

1. Is the cart/order summary clearly displayed?
2. Are prices shown correctly?
3. Is the checkout flow intuitive?
4. Are all necessary form fields present?
5. Is the payment section secure-looking?
6. Are there any visual issues or broken elements?

Provide comprehensive analysis."""

            checkout_analysis = await self.vision_client.analyze_image(
                initial_screenshot, checkout_analysis_prompt
            )
            self.state["output"]["checkout_analysis"] = checkout_analysis

            # Check for key checkout elements
            key_elements = {
                "cart_items": ".cart-item, .product-item, [data-testid*='cart']",
                "total_price": ".total, .grand-total, [data-testid*='total']",
                "checkout_button": "button:has-text('Checkout'), button:has-text('Proceed'), button[type='submit']",
            }

            element_presence = {}
            for name, selector in key_elements.items():
                result = await self.playwright_mcp.execute_tool(
                    "playwright_wait_for_selector", {"selector": selector, "state": "attached"}
                )
                element_presence[name] = result
                logger.info(f"Checkout element {name}: {result}")

            self.state["output"]["element_presence"] = element_presence

            # Test progression through checkout (without actually purchasing)
            # This would click through steps but stop before final submission

            logger.info("Testing checkout flow progression")

            # Take screenshot of each major step we can identify
            # In a real implementation, would navigate through:
            # 1. Cart review
            # 2. Shipping info
            # 3. Payment info
            # 4. Order review

            # For now, take a final screenshot
            final_screenshot = await self.take_screenshot("checkout_review")

            # Determine test success
            all_elements_present = all(element_presence.values())
            visual_valid = visual_validation.get("overall_valid", False)

            self.state["output"]["all_elements_present"] = all_elements_present
            self.state["output"]["visual_valid"] = visual_valid
            self.state["output"]["test_passed"] = all_elements_present

            if self.state["output"]["test_passed"]:
                self.state["status"] = "success"
            else:
                self.state["status"] = "failure"

        except Exception as e:
            logger.exception(f"Checkout agent execution failed: {e}")
            self.state["status"] = "error"
            self.state["error"] = str(e)

        return self.state
