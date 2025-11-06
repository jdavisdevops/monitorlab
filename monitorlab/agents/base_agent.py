"""Base agent class for MonitorLab agents."""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from monitorlab.browser.browser_manager import BrowserManager
from monitorlab.browser.page_controller import PageController
from monitorlab.models.llm_client import LLMClient
from monitorlab.models.vision_client import VisionClient
from monitorlab.config.settings import get_settings

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentResult:
    """Result of agent execution."""

    agent_id: str
    agent_type: str
    status: AgentStatus
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(
        self,
        task: str,
        agent_id: Optional[str] = None,
        browser_manager: Optional[BrowserManager] = None,
        llm_client: Optional[LLMClient] = None,
        vision_client: Optional[VisionClient] = None,
        settings: Optional[Any] = None,
        **kwargs,
    ):
        """Initialize base agent.

        Args:
            task: Task description for this agent
            agent_id: Optional unique identifier
            browser_manager: Optional browser manager instance
            llm_client: Optional LLM client instance
            vision_client: Optional vision client instance
            settings: Optional settings object
            **kwargs: Additional agent-specific parameters
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.task = task
        self.settings = settings or get_settings()
        self.kwargs = kwargs

        # Clients and managers
        self.browser_manager = browser_manager
        self.llm_client = llm_client or LLMClient(self.settings)
        self.vision_client = vision_client or VisionClient(self.settings)

        # Page controller (will be set when page is created)
        self.page_controller: Optional[PageController] = None
        self.page_id: Optional[str] = None

        # State
        self.status = AgentStatus.PENDING
        self.result: Optional[AgentResult] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    @property
    def agent_type(self) -> str:
        """Get agent type name."""
        return self.__class__.__name__

    async def setup(self):
        """Setup agent resources before execution."""
        # Create page if browser manager is provided
        if self.browser_manager:
            self.page_id = f"page_{self.agent_id}"
            page = await self.browser_manager.create_page(self.page_id)
            self.page_controller = PageController(page)
            logger.info(f"Agent {self.agent_id} setup complete with page")
        else:
            logger.info(f"Agent {self.agent_id} setup complete (no browser)")

    async def teardown(self):
        """Clean up agent resources after execution."""
        if self.browser_manager and self.page_id:
            try:
                await self.browser_manager.close_page(self.page_id)
                logger.info(f"Agent {self.agent_id} page closed")
            except Exception as e:
                logger.warning(f"Error closing page for agent {self.agent_id}: {e}")

    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """Execute the agent's task.

        This method must be implemented by subclasses.

        Returns:
            Dictionary with execution results
        """
        pass

    async def run(self) -> AgentResult:
        """Run the agent with proper lifecycle management.

        Returns:
            AgentResult with execution details
        """
        self.start_time = datetime.now()
        self.status = AgentStatus.RUNNING
        logger.info(f"Starting agent {self.agent_id} ({self.agent_type}): {self.task}")

        try:
            # Setup
            await self.setup()

            # Execute with timeout
            timeout = self.settings.agent_timeout
            try:
                output = await asyncio.wait_for(self.execute(), timeout=timeout)
                self.status = AgentStatus.COMPLETED
                error = None
            except asyncio.TimeoutError:
                logger.error(f"Agent {self.agent_id} timed out after {timeout}s")
                self.status = AgentStatus.TIMEOUT
                output = {}
                error = f"Execution timed out after {timeout} seconds"

        except Exception as e:
            logger.exception(f"Agent {self.agent_id} failed: {e}")
            self.status = AgentStatus.FAILED
            output = {}
            error = str(e)

        finally:
            # Teardown
            try:
                await self.teardown()
            except Exception as e:
                logger.warning(f"Error during teardown for agent {self.agent_id}: {e}")

            # Calculate execution time
            self.end_time = datetime.now()
            execution_time = (self.end_time - self.start_time).total_seconds()

            # Create result
            self.result = AgentResult(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                status=self.status,
                output=output,
                error=error,
                execution_time=execution_time,
                metadata={
                    "task": self.task,
                    "start_time": self.start_time.isoformat(),
                    "end_time": self.end_time.isoformat(),
                },
            )

            logger.info(
                f"Agent {self.agent_id} finished with status {self.status.value} "
                f"in {execution_time:.2f}s"
            )

        return self.result

    async def ask_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Ask the LLM a question.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override

        Returns:
            LLM response
        """
        return await self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
        )

    async def analyze_screenshot(
        self,
        screenshot_path: str,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Analyze a screenshot with vision model.

        Args:
            screenshot_path: Path to screenshot
            prompt: Analysis prompt
            system_prompt: Optional system prompt

        Returns:
            Analysis result
        """
        return await self.vision_client.analyze_image(
            screenshot_path,
            prompt,
            system_prompt=system_prompt,
        )

    def __repr__(self) -> str:
        return f"{self.agent_type}(id={self.agent_id}, task={self.task[:50]}...)"
