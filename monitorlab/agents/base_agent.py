"""Base agent class for domain agents."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, TypedDict
from pathlib import Path

from langchain_openai import ChatOpenAI
from monitorlab.config.settings import get_settings
from monitorlab.models.vision_client import VisionClient
from monitorlab.mcp.playwright_client import PlaywrightMCPClient

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State object for agent execution (used by LangGraph)."""

    agent_name: str
    task: str
    target_url: Optional[str]
    status: str  # pending, running, success, failure, error
    start_time: datetime
    end_time: Optional[datetime]
    output: Dict[str, Any]
    error: Optional[str]
    screenshots: list[str]
    test_run_id: Optional[int]


class DomainAgent(ABC):
    """Base class for domain agents that test complete features/workflows.

    Domain agents are autonomous and responsible for testing entire features,
    not just performing specialized tasks. For example:
    - HomepageAgent tests the entire homepage functionality
    - CheckoutAgent tests the complete checkout flow
    - AuthAgent tests authentication features

    This is different from specialized worker agents (navigator, validator, etc.)
    """

    def __init__(
        self,
        name: str,
        task: str,
        target_url: Optional[str] = None,
        settings: Optional[Any] = None,
    ):
        """Initialize domain agent.

        Args:
            name: Agent name (e.g., "homepage", "checkout")
            task: Task description
            target_url: Optional target URL
            settings: Optional settings object
        """
        self.name = name
        self.task = task
        self.target_url = target_url
        self.settings = settings or get_settings()

        # Initialize clients
        self.llm = ChatOpenAI(
            base_url=self.settings.llm_api_base,
            api_key=self.settings.llm_api_key,
            model=self.settings.llm_model,
            temperature=self.settings.llm_temperature,
        )

        self.vision_client = VisionClient(self.settings)
        self.playwright_mcp = PlaywrightMCPClient()

        # State
        self.state: AgentState = {
            "agent_name": name,
            "task": task,
            "target_url": target_url,
            "status": "pending",
            "start_time": datetime.utcnow(),
            "end_time": None,
            "output": {},
            "error": None,
            "screenshots": [],
            "test_run_id": None,
        }

    @abstractmethod
    async def execute(self) -> AgentState:
        """Execute the agent's complete test workflow.

        This method should:
        1. Navigate to target URL(s)
        2. Perform all necessary interactions
        3. Validate functionality and visual appearance
        4. Capture evidence (screenshots)
        5. Return comprehensive results

        Returns:
            Updated AgentState with results
        """
        pass

    async def run(self) -> AgentState:
        """Run the agent with proper error handling and state management.

        Returns:
            Final AgentState
        """
        self.state["status"] = "running"
        self.state["start_time"] = datetime.utcnow()

        try:
            logger.info(f"Starting agent: {self.name} - {self.task}")
            self.state = await self.execute()
            self.state["status"] = "success"
            logger.info(f"Agent {self.name} completed successfully")

        except Exception as e:
            logger.exception(f"Agent {self.name} failed: {e}")
            self.state["status"] = "error"
            self.state["error"] = str(e)

        finally:
            self.state["end_time"] = datetime.utcnow()
            duration = (
                self.state["end_time"] - self.state["start_time"]
            ).total_seconds()
            self.state["output"]["duration_seconds"] = duration

            # Cleanup
            await self.playwright_mcp.cleanup()

        return self.state

    async def take_screenshot(self, name: str) -> str:
        """Take a screenshot and save it.

        Args:
            name: Screenshot name

        Returns:
            Path to saved screenshot
        """
        screenshot_dir = Path(self.settings.screenshot_dir)
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.name}_{name}_{timestamp}.png"
        filepath = screenshot_dir / filename

        # Use MCP to take screenshot
        await self.playwright_mcp.execute_tool(
            "playwright_screenshot",
            {"name": str(filepath), "full_page": True},
        )

        self.state["screenshots"].append(str(filepath))
        logger.info(f"Screenshot saved: {filepath}")
        return str(filepath)

    async def validate_visual(
        self, screenshot_path: str, expected_elements: list[str]
    ) -> Dict[str, Any]:
        """Validate visual rendering using vision model.

        Args:
            screenshot_path: Path to screenshot
            expected_elements: List of expected UI elements

        Returns:
            Validation results
        """
        return await self.vision_client.validate_rendering(
            screenshot_path, expected_elements
        )

    async def ask_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Ask the LLM a question.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            LLM response
        """
        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("user", prompt))

        response = await self.llm.ainvoke(messages)
        return response.content

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent.

        Returns:
            System prompt describing agent capabilities
        """
        base_prompt = f"""You are a {self.name} testing agent responsible for: {self.task}

Your capabilities:
- Browser automation via Playwright MCP tools
- Visual validation using Qwen2-VL vision model
- Comprehensive functional testing
- Screenshot capture and analysis

{self.playwright_mcp.get_system_prompt_addition()}

Execute your tests thoroughly and provide detailed results."""

        return base_prompt
