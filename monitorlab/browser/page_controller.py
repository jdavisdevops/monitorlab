"""High-level page controller for common browser actions."""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Union
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class PageController:
    """High-level controller for page interactions."""

    def __init__(self, page: Page):
        """Initialize page controller.

        Args:
            page: Playwright page instance
        """
        self.page = page

    async def navigate(self, url: str, wait_until: str = "load") -> bool:
        """Navigate to a URL.

        Args:
            url: URL to navigate to
            wait_until: When to consider navigation successful
                       ('load', 'domcontentloaded', 'networkidle')

        Returns:
            True if navigation successful
        """
        try:
            await self.page.goto(url, wait_until=wait_until)
            logger.info(f"Navigated to {url}")
            return True
        except Exception as e:
            logger.error(f"Navigation to {url} failed: {e}")
            return False

    async def click(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Click an element.

        Args:
            selector: CSS selector
            timeout: Optional timeout in milliseconds

        Returns:
            True if click successful
        """
        try:
            await self.page.click(selector, timeout=timeout)
            logger.info(f"Clicked: {selector}")
            return True
        except Exception as e:
            logger.error(f"Click failed for {selector}: {e}")
            return False

    async def fill(self, selector: str, value: str, timeout: Optional[int] = None) -> bool:
        """Fill an input field.

        Args:
            selector: CSS selector
            value: Value to fill
            timeout: Optional timeout in milliseconds

        Returns:
            True if fill successful
        """
        try:
            await self.page.fill(selector, value, timeout=timeout)
            logger.info(f"Filled {selector} with value")
            return True
        except Exception as e:
            logger.error(f"Fill failed for {selector}: {e}")
            return False

    async def type_text(
        self, selector: str, text: str, delay: int = 50, timeout: Optional[int] = None
    ) -> bool:
        """Type text into an element with delay between keystrokes.

        Args:
            selector: CSS selector
            text: Text to type
            delay: Delay between keystrokes in milliseconds
            timeout: Optional timeout in milliseconds

        Returns:
            True if typing successful
        """
        try:
            await self.page.type(selector, text, delay=delay, timeout=timeout)
            logger.info(f"Typed text into {selector}")
            return True
        except Exception as e:
            logger.error(f"Type failed for {selector}: {e}")
            return False

    async def select_option(
        self, selector: str, value: Union[str, List[str]], timeout: Optional[int] = None
    ) -> bool:
        """Select option(s) in a select element.

        Args:
            selector: CSS selector
            value: Value(s) to select
            timeout: Optional timeout in milliseconds

        Returns:
            True if selection successful
        """
        try:
            await self.page.select_option(selector, value, timeout=timeout)
            logger.info(f"Selected option in {selector}")
            return True
        except Exception as e:
            logger.error(f"Select failed for {selector}: {e}")
            return False

    async def check(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Check a checkbox or radio button.

        Args:
            selector: CSS selector
            timeout: Optional timeout in milliseconds

        Returns:
            True if check successful
        """
        try:
            await self.page.check(selector, timeout=timeout)
            logger.info(f"Checked: {selector}")
            return True
        except Exception as e:
            logger.error(f"Check failed for {selector}: {e}")
            return False

    async def uncheck(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Uncheck a checkbox.

        Args:
            selector: CSS selector
            timeout: Optional timeout in milliseconds

        Returns:
            True if uncheck successful
        """
        try:
            await self.page.uncheck(selector, timeout=timeout)
            logger.info(f"Unchecked: {selector}")
            return True
        except Exception as e:
            logger.error(f"Uncheck failed for {selector}: {e}")
            return False

    async def wait_for_selector(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[int] = None,
    ) -> bool:
        """Wait for an element to be in a specific state.

        Args:
            selector: CSS selector
            state: State to wait for ('attached', 'detached', 'visible', 'hidden')
            timeout: Optional timeout in milliseconds

        Returns:
            True if element reached desired state
        """
        try:
            await self.page.wait_for_selector(selector, state=state, timeout=timeout)
            logger.info(f"Element {selector} reached state: {state}")
            return True
        except PlaywrightTimeoutError:
            logger.warning(f"Timeout waiting for {selector} to be {state}")
            return False
        except Exception as e:
            logger.error(f"Error waiting for {selector}: {e}")
            return False

    async def wait_for_url(self, url: str, timeout: Optional[int] = None) -> bool:
        """Wait for URL to match pattern.

        Args:
            url: URL pattern to wait for
            timeout: Optional timeout in milliseconds

        Returns:
            True if URL matched
        """
        try:
            await self.page.wait_for_url(url, timeout=timeout)
            logger.info(f"URL matched: {url}")
            return True
        except PlaywrightTimeoutError:
            logger.warning(f"Timeout waiting for URL: {url}")
            return False
        except Exception as e:
            logger.error(f"Error waiting for URL {url}: {e}")
            return False

    async def wait_for_load_state(self, state: str = "load") -> bool:
        """Wait for page load state.

        Args:
            state: State to wait for ('load', 'domcontentloaded', 'networkidle')

        Returns:
            True if state reached
        """
        try:
            await self.page.wait_for_load_state(state)
            logger.info(f"Page reached load state: {state}")
            return True
        except Exception as e:
            logger.error(f"Error waiting for load state {state}: {e}")
            return False

    async def get_text(self, selector: str, timeout: Optional[int] = None) -> Optional[str]:
        """Get text content of an element.

        Args:
            selector: CSS selector
            timeout: Optional timeout in milliseconds

        Returns:
            Text content or None if failed
        """
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            if element:
                text = await element.text_content()
                logger.info(f"Got text from {selector}")
                return text
            return None
        except Exception as e:
            logger.error(f"Error getting text from {selector}: {e}")
            return None

    async def get_attribute(
        self, selector: str, attribute: str, timeout: Optional[int] = None
    ) -> Optional[str]:
        """Get attribute value of an element.

        Args:
            selector: CSS selector
            attribute: Attribute name
            timeout: Optional timeout in milliseconds

        Returns:
            Attribute value or None if failed
        """
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            if element:
                value = await element.get_attribute(attribute)
                logger.info(f"Got attribute {attribute} from {selector}")
                return value
            return None
        except Exception as e:
            logger.error(f"Error getting attribute {attribute} from {selector}: {e}")
            return None

    async def is_visible(self, selector: str, timeout: int = 1000) -> bool:
        """Check if element is visible.

        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds (short default)

        Returns:
            True if element is visible
        """
        try:
            await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except:
            return False

    async def is_enabled(self, selector: str) -> bool:
        """Check if element is enabled.

        Args:
            selector: CSS selector

        Returns:
            True if element is enabled
        """
        try:
            return await self.page.is_enabled(selector)
        except Exception as e:
            logger.error(f"Error checking if {selector} is enabled: {e}")
            return False

    async def scroll_to(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Scroll element into view.

        Args:
            selector: CSS selector
            timeout: Optional timeout in milliseconds

        Returns:
            True if scroll successful
        """
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            if element:
                await element.scroll_into_view_if_needed()
                logger.info(f"Scrolled to {selector}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error scrolling to {selector}: {e}")
            return False

    async def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript on the page.

        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script

        Returns:
            Result of script execution
        """
        try:
            result = await self.page.evaluate(script, *args)
            logger.info("Executed JavaScript")
            return result
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return None

    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information.

        Returns:
            Dictionary with page info (url, title, etc.)
        """
        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "viewport": self.page.viewport_size,
        }

    async def wait_for_timeout(self, timeout: int):
        """Wait for a specific amount of time.

        Args:
            timeout: Time to wait in milliseconds
        """
        await self.page.wait_for_timeout(timeout)
        logger.info(f"Waited for {timeout}ms")
