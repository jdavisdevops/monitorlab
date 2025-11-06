"""Agent orchestrator for managing and coordinating multiple agents."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Type
from datetime import datetime

from monitorlab.agents.base_agent import BaseAgent, AgentResult, AgentStatus
from monitorlab.browser.browser_manager import BrowserManager
from monitorlab.models.llm_client import LLMClient
from monitorlab.models.vision_client import VisionClient
from monitorlab.config.settings import get_settings

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates multiple agents for complex testing workflows."""

    def __init__(self, settings: Optional[Any] = None, shared_browser: bool = True):
        """Initialize orchestrator.

        Args:
            settings: Optional settings object
            shared_browser: Whether agents share a browser instance
        """
        self.settings = settings or get_settings()
        self.shared_browser = shared_browser

        # Shared resources
        self.browser_manager: Optional[BrowserManager] = None
        self.llm_client = LLMClient(self.settings)
        self.vision_client = VisionClient(self.settings)

        # Agent management
        self.agents: List[BaseAgent] = []
        self.results: List[AgentResult] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    async def setup(self):
        """Setup shared resources."""
        if self.shared_browser:
            self.browser_manager = BrowserManager(self.settings)
            await self.browser_manager.start()
            logger.info("Orchestrator browser started")

    async def teardown(self):
        """Clean up shared resources."""
        if self.browser_manager:
            await self.browser_manager.stop()
            logger.info("Orchestrator browser stopped")

    def spawn_agent(
        self,
        agent_class: Type[BaseAgent],
        task: str,
        agent_id: Optional[str] = None,
        **kwargs,
    ) -> BaseAgent:
        """Spawn a new agent.

        Args:
            agent_class: Agent class to instantiate
            task: Task description for the agent
            agent_id: Optional unique identifier
            **kwargs: Additional agent parameters

        Returns:
            Created agent instance
        """
        agent = agent_class(
            task=task,
            agent_id=agent_id,
            browser_manager=self.browser_manager if self.shared_browser else None,
            llm_client=self.llm_client,
            vision_client=self.vision_client,
            settings=self.settings,
            **kwargs,
        )
        self.agents.append(agent)
        logger.info(f"Spawned {agent.agent_type} agent: {agent.agent_id}")
        return agent

    async def run_agent(self, agent: BaseAgent) -> AgentResult:
        """Run a single agent.

        Args:
            agent: Agent to run

        Returns:
            Agent result
        """
        result = await agent.run()
        self.results.append(result)
        return result

    async def run_sequential(self) -> List[AgentResult]:
        """Run all agents sequentially.

        Returns:
            List of agent results
        """
        logger.info(f"Running {len(self.agents)} agents sequentially")
        results = []

        for agent in self.agents:
            result = await self.run_agent(agent)
            results.append(result)

            # Optionally stop on failure
            if result.status == AgentStatus.FAILED:
                logger.warning(f"Agent {agent.agent_id} failed, but continuing...")

        return results

    async def run_parallel(self, max_concurrent: Optional[int] = None) -> List[AgentResult]:
        """Run agents in parallel with concurrency limit.

        Args:
            max_concurrent: Maximum concurrent agents (default from settings)

        Returns:
            List of agent results
        """
        max_concurrent = max_concurrent or self.settings.max_concurrent_agents
        logger.info(
            f"Running {len(self.agents)} agents in parallel "
            f"(max concurrent: {max_concurrent})"
        )

        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_limit(agent: BaseAgent) -> AgentResult:
            async with semaphore:
                return await self.run_agent(agent)

        tasks = [run_with_limit(agent) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent {self.agents[i].agent_id} raised exception: {result}")
                # Create a failed result
                error_result = AgentResult(
                    agent_id=self.agents[i].agent_id,
                    agent_type=self.agents[i].agent_type,
                    status=AgentStatus.FAILED,
                    error=str(result),
                )
                results[i] = error_result
                self.results.append(error_result)

        return results

    async def run(self, mode: str = "sequential") -> List[AgentResult]:
        """Run all spawned agents.

        Args:
            mode: Execution mode ('sequential' or 'parallel')

        Returns:
            List of agent results
        """
        if not self.agents:
            logger.warning("No agents to run")
            return []

        self.start_time = datetime.now()

        try:
            await self.setup()

            if mode == "sequential":
                results = await self.run_sequential()
            elif mode == "parallel":
                results = await self.run_parallel()
            else:
                raise ValueError(f"Unknown mode: {mode}")

            self.end_time = datetime.now()
            execution_time = (self.end_time - self.start_time).total_seconds()

            logger.info(
                f"Orchestrator completed in {execution_time:.2f}s. "
                f"Results: {self.get_summary()}"
            )

            return results

        finally:
            await self.teardown()

    def get_results(self) -> List[AgentResult]:
        """Get all agent results.

        Returns:
            List of agent results
        """
        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary.

        Returns:
            Dictionary with summary statistics
        """
        total = len(self.results)
        completed = sum(1 for r in self.results if r.status == AgentStatus.COMPLETED)
        failed = sum(1 for r in self.results if r.status == AgentStatus.FAILED)
        timeout = sum(1 for r in self.results if r.status == AgentStatus.TIMEOUT)

        return {
            "total_agents": total,
            "completed": completed,
            "failed": failed,
            "timeout": timeout,
            "success_rate": f"{(completed / total * 100):.1f}%" if total > 0 else "0%",
            "total_time": (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time
                else None
            ),
        }

    def clear(self):
        """Clear all agents and results."""
        self.agents.clear()
        self.results.clear()
        logger.info("Orchestrator cleared")

    async def __aenter__(self):
        """Context manager entry."""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.teardown()
