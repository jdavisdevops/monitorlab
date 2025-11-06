"""LangGraph-based test orchestration."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Type, Optional

from langgraph.graph import StateGraph, END
from monitorlab.agents.base_agent import DomainAgent, AgentState
from monitorlab.database import TestRunRepository, init_db
from monitorlab.config.settings import get_settings

logger = logging.getLogger(__name__)


class TestOrchestrator:
    """Orchestrates multiple test agents using LangGraph.

    This orchestrator:
    - Manages parallel and sequential agent execution
    - Tracks run history in database
    - Provides state management via LangGraph
    - Handles agent dependencies and coordination
    """

    def __init__(self, settings: Optional[Any] = None):
        """Initialize test orchestrator.

        Args:
            settings: Optional settings object
        """
        self.settings = settings or get_settings()
        self.agents: List[DomainAgent] = []
        self.test_run_id: Optional[int] = None
        self.graph = None

    async def initialize(self):
        """Initialize database and resources."""
        await init_db(self.settings.database_url)
        logger.info("Test orchestrator initialized")

    def add_agent(self, agent: DomainAgent):
        """Add an agent to the test run.

        Args:
            agent: Domain agent to add
        """
        self.agents.append(agent)
        logger.info(f"Added agent: {agent.name}")

    async def run_parallel(self, name: str = "Parallel Test Run") -> Dict[str, Any]:
        """Run all agents in parallel.

        Args:
            name: Test run name

        Returns:
            Test run results
        """
        # Create test run
        test_run = await TestRunRepository.create_test_run(
            name=name,
            description=f"Parallel execution of {len(self.agents)} agents",
            metadata={"mode": "parallel", "agent_count": len(self.agents)},
        )
        self.test_run_id = test_run.id
        start_time = datetime.utcnow()

        # Run all agents concurrently
        logger.info(f"Starting parallel execution of {len(self.agents)} agents")

        try:
            # Execute all agents in parallel
            tasks = [agent.run() for agent in self.agents]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and save to database
            for agent, result in zip(self.agents, results):
                if isinstance(result, Exception):
                    logger.error(f"Agent {agent.name} failed with exception: {result}")
                    await TestRunRepository.add_test_result(
                        test_run_id=self.test_run_id,
                        agent_name=agent.name,
                        agent_type=agent.__class__.__name__,
                        task=agent.task,
                        status="error",
                        started_at=start_time,
                        completed_at=datetime.utcnow(),
                        duration_seconds=0,
                        error=str(result),
                    )
                else:
                    # Save successful result
                    await TestRunRepository.add_test_result(
                        test_run_id=self.test_run_id,
                        agent_name=result["agent_name"],
                        agent_type=agent.__class__.__name__,
                        task=result["task"],
                        status=result["status"],
                        started_at=result["start_time"],
                        completed_at=result["end_time"],
                        duration_seconds=result["output"].get("duration_seconds"),
                        output=result["output"],
                        error=result.get("error"),
                        screenshot_path=(
                            result["screenshots"][0] if result["screenshots"] else None
                        ),
                    )

            # Update test run status
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            await TestRunRepository.update_test_run(
                test_run_id=self.test_run_id,
                status="completed",
                completed_at=end_time,
                duration_seconds=duration,
            )

            # Get statistics
            stats = await TestRunRepository.get_test_statistics(self.test_run_id)

            return {
                "test_run_id": self.test_run_id,
                "status": "completed",
                "statistics": stats,
                "results": [r if not isinstance(r, Exception) else {"error": str(r)} for r in results],
            }

        except Exception as e:
            logger.exception(f"Parallel execution failed: {e}")
            await TestRunRepository.update_test_run(
                test_run_id=self.test_run_id,
                status="failed",
                completed_at=datetime.utcnow(),
            )
            raise

    async def run_sequential(self, name: str = "Sequential Test Run") -> Dict[str, Any]:
        """Run all agents sequentially.

        Args:
            name: Test run name

        Returns:
            Test run results
        """
        # Create test run
        test_run = await TestRunRepository.create_test_run(
            name=name,
            description=f"Sequential execution of {len(self.agents)} agents",
            metadata={"mode": "sequential", "agent_count": len(self.agents)},
        )
        self.test_run_id = test_run.id
        start_time = datetime.utcnow()

        logger.info(f"Starting sequential execution of {len(self.agents)} agents")

        results = []

        try:
            for agent in self.agents:
                logger.info(f"Running agent: {agent.name}")
                result = await agent.run()
                results.append(result)

                # Save result to database
                await TestRunRepository.add_test_result(
                    test_run_id=self.test_run_id,
                    agent_name=result["agent_name"],
                    agent_type=agent.__class__.__name__,
                    task=result["task"],
                    status=result["status"],
                    started_at=result["start_time"],
                    completed_at=result["end_time"],
                    duration_seconds=result["output"].get("duration_seconds"),
                    output=result["output"],
                    error=result.get("error"),
                    screenshot_path=result["screenshots"][0] if result["screenshots"] else None,
                )

            # Update test run
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            await TestRunRepository.update_test_run(
                test_run_id=self.test_run_id,
                status="completed",
                completed_at=end_time,
                duration_seconds=duration,
            )

            # Get statistics
            stats = await TestRunRepository.get_test_statistics(self.test_run_id)

            return {
                "test_run_id": self.test_run_id,
                "status": "completed",
                "statistics": stats,
                "results": results,
            }

        except Exception as e:
            logger.exception(f"Sequential execution failed: {e}")
            await TestRunRepository.update_test_run(
                test_run_id=self.test_run_id,
                status="failed",
                completed_at=datetime.utcnow(),
            )
            raise


def create_test_graph(agents: List[DomainAgent]) -> StateGraph:
    """Create a LangGraph state graph for agent execution.

    This provides more advanced orchestration capabilities like:
    - Agent dependencies
    - Conditional execution
    - Parallel branches
    - State persistence

    Args:
        agents: List of domain agents

    Returns:
        LangGraph StateGraph
    """
    # Define the state structure
    class TestGraphState(Dict):
        """State for test execution graph."""
        agent_results: List[AgentState]
        current_agent_index: int
        total_agents: int

    # Create the graph
    workflow = StateGraph(TestGraphState)

    # Add nodes for each agent
    for i, agent in enumerate(agents):
        async def agent_node(state: TestGraphState, agent=agent) -> TestGraphState:
            """Execute agent and update state."""
            result = await agent.run()
            state["agent_results"].append(result)
            state["current_agent_index"] += 1
            return state

        workflow.add_node(f"agent_{i}", agent_node)

    # Set up edges (sequential execution for now)
    workflow.set_entry_point("agent_0")

    for i in range(len(agents) - 1):
        workflow.add_edge(f"agent_{i}", f"agent_{i+1}")

    workflow.add_edge(f"agent_{len(agents)-1}", END)

    return workflow.compile()
