"""Browser manager for handling browser lifecycle and contexts."""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from pathlib import Path

from monitorlab.config.settings import get_settings

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages browser instances and contexts."""

    def __init__(self, settings: Optional[Any] = None):
        """Initialize browser manager.

        Args:
            settings: Optional settings object. If None, uses get_settings().
        """
        self.settings = settings or get_settings()
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self._lock = asyncio.Lock()

    async def start(self):
        """Start the browser."""
        async with self._lock:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=self.settings.headless,
                    slow_mo=self.settings.slow_mo,
                )
                logger.info("Browser started successfully")

    async def stop(self):
        """Stop the browser and clean up resources."""
        async with self._lock:
            # Close all pages
            for page in list(self.pages.values()):
                try:
                    await page.close()
                except Exception as e:
                    logger.warning(f"Error closing page: {e}")

            # Close all contexts
            for context in list(self.contexts.values()):
                try:
                    await context.close()
                except Exception as e:
                    logger.warning(f"Error closing context: {e}")

            # Close browser
            if self.browser:
                try:
                    await self.browser.close()
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")

            # Stop playwright
            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception as e:
                    logger.warning(f"Error stopping playwright: {e}")

            self.pages.clear()
            self.contexts.clear()
            self.browser = None
            self.playwright = None
            logger.info("Browser stopped successfully")

    async def create_context(
        self,
        context_id: str,
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None,
        **kwargs,
    ) -> BrowserContext:
        """Create a new browser context.

        Args:
            context_id: Unique identifier for this context
            viewport: Viewport size dict with 'width' and 'height'
            user_agent: Custom user agent string
            **kwargs: Additional context options

        Returns:
            BrowserContext instance
        """
        if not self.browser:
            await self.start()

        if context_id in self.contexts:
            logger.warning(f"Context {context_id} already exists, returning existing")
            return self.contexts[context_id]

        context_options = {
            "viewport": viewport
            or {
                "width": self.settings.default_viewport_width,
                "height": self.settings.default_viewport_height,
            },
            **kwargs,
        }

        if user_agent:
            context_options["user_agent"] = user_agent

        context = await self.browser.new_context(**context_options)
        self.contexts[context_id] = context
        logger.info(f"Created browser context: {context_id}")
        return context

    async def create_page(
        self,
        page_id: str,
        context_id: Optional[str] = None,
        **context_kwargs,
    ) -> Page:
        """Create a new page.

        Args:
            page_id: Unique identifier for this page
            context_id: Context to use (creates new if None)
            **context_kwargs: Context options if creating new context

        Returns:
            Page instance
        """
        if page_id in self.pages:
            logger.warning(f"Page {page_id} already exists, returning existing")
            return self.pages[page_id]

        # Get or create context
        if context_id and context_id in self.contexts:
            context = self.contexts[context_id]
        else:
            ctx_id = context_id or f"ctx_{page_id}"
            context = await self.create_context(ctx_id, **context_kwargs)

        # Create page
        page = await context.new_page()
        page.set_default_timeout(self.settings.browser_timeout)
        self.pages[page_id] = page
        logger.info(f"Created page: {page_id}")
        return page

    async def get_page(self, page_id: str) -> Optional[Page]:
        """Get an existing page by ID.

        Args:
            page_id: Page identifier

        Returns:
            Page instance or None if not found
        """
        return self.pages.get(page_id)

    async def close_page(self, page_id: str):
        """Close a page.

        Args:
            page_id: Page identifier
        """
        if page_id in self.pages:
            page = self.pages[page_id]
            await page.close()
            del self.pages[page_id]
            logger.info(f"Closed page: {page_id}")

    async def close_context(self, context_id: str):
        """Close a browser context and all its pages.

        Args:
            context_id: Context identifier
        """
        if context_id in self.contexts:
            # Close all pages in this context
            pages_to_close = [
                page_id for page_id, page in self.pages.items() if page.context == self.contexts[context_id]
            ]
            for page_id in pages_to_close:
                await self.close_page(page_id)

            # Close context
            context = self.contexts[context_id]
            await context.close()
            del self.contexts[context_id]
            logger.info(f"Closed context: {context_id}")

    async def take_screenshot(
        self,
        page: Page,
        path: Optional[str] = None,
        full_page: Optional[bool] = None,
    ) -> bytes:
        """Take a screenshot of a page.

        Args:
            page: Page to screenshot
            path: Optional path to save screenshot
            full_page: Whether to take full page screenshot

        Returns:
            Screenshot bytes
        """
        screenshot_options = {
            "full_page": full_page if full_page is not None else self.settings.screenshot_full_page,
            "type": "jpeg",
            "quality": self.settings.screenshot_quality,
        }

        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            screenshot_options["path"] = path

        screenshot = await page.screenshot(**screenshot_options)
        logger.info(f"Screenshot taken{f' and saved to {path}' if path else ''}")
        return screenshot

    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop()
