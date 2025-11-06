"""Pipeline definition and execution framework."""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from monitorlab.core.orchestrator import AgentOrchestrator
from monitorlab.agents.navigator import NavigatorAgent
from monitorlab.agents.interaction import InteractionAgent
from monitorlab.agents.vision import VisionAgent
from monitorlab.agents.validator import ValidatorAgent
from monitorlab.agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Pipeline configuration."""

    name: str
    description: Optional[str] = None
    target_url: Optional[str] = None
    agents: List[Dict[str, Any]] = None
    mode: str = "sequential"  # sequential or parallel
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.agents is None:
            self.agents = []
        if self.metadata is None:
            self.metadata = {}


class Pipeline:
    """Testing pipeline definition."""

    AGENT_TYPES = {
        "navigator": NavigatorAgent,
        "interaction": InteractionAgent,
        "vision": VisionAgent,
        "validator": ValidatorAgent,
    }

    def __init__(self, config: PipelineConfig):
        """Initialize pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Pipeline":
        """Load pipeline from YAML file.

        Args:
            yaml_path: Path to YAML file

        Returns:
            Pipeline instance
        """
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        config = PipelineConfig(
            name=data.get("name", "Unnamed Pipeline"),
            description=data.get("description"),
            target_url=data.get("target_url"),
            agents=data.get("agents", []),
            mode=data.get("mode", "sequential"),
            metadata=data.get("metadata", {}),
        )

        return cls(config)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pipeline":
        """Create pipeline from dictionary.

        Args:
            data: Pipeline configuration dictionary

        Returns:
            Pipeline instance
        """
        config = PipelineConfig(
            name=data.get("name", "Unnamed Pipeline"),
            description=data.get("description"),
            target_url=data.get("target_url"),
            agents=data.get("agents", []),
            mode=data.get("mode", "sequential"),
            metadata=data.get("metadata", {}),
        )

        return cls(config)

    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline to dictionary.

        Returns:
            Pipeline configuration as dictionary
        """
        return {
            "name": self.config.name,
            "description": self.config.description,
            "target_url": self.config.target_url,
            "agents": self.config.agents,
            "mode": self.config.mode,
            "metadata": self.config.metadata,
        }

    def to_yaml(self, output_path: str):
        """Save pipeline to YAML file.

        Args:
            output_path: Path to output YAML file
        """
        with open(output_path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

        logger.info(f"Pipeline saved to {output_path}")


class PipelineRunner:
    """Runs testing pipelines."""

    def __init__(self, settings: Optional[Any] = None):
        """Initialize pipeline runner.

        Args:
            settings: Optional settings object
        """
        self.settings = settings

    async def run_pipeline(
        self, pipeline: Pipeline, variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Run a testing pipeline.

        Args:
            pipeline: Pipeline to run
            variables: Optional variables to substitute in pipeline

        Returns:
            Dictionary with execution results
        """
        logger.info(f"Starting pipeline: {pipeline.config.name}")

        if pipeline.config.description:
            logger.info(f"Description: {pipeline.config.description}")

        # Initialize orchestrator
        orchestrator = AgentOrchestrator(settings=self.settings, shared_browser=True)

        try:
            # Setup orchestrator
            await orchestrator.setup()

            # Process variables
            variables = variables or {}
            if pipeline.config.target_url:
                variables["target_url"] = pipeline.config.target_url

            # Spawn agents based on pipeline configuration
            for i, agent_config in enumerate(pipeline.config.agents):
                agent_type = agent_config.get("type")
                if agent_type not in Pipeline.AGENT_TYPES:
                    logger.error(f"Unknown agent type: {agent_type}")
                    continue

                agent_class = Pipeline.AGENT_TYPES[agent_type]

                # Substitute variables in task
                task = agent_config.get("task", "")
                for var_name, var_value in variables.items():
                    task = task.replace(f"{{{var_name}}}", var_value)

                # Create agent
                agent = orchestrator.spawn_agent(
                    agent_class,
                    task=task,
                    agent_id=f"{agent_type}_{i}",
                    **{k: v for k, v in agent_config.items() if k not in ["type", "task"]},
                )

                logger.info(f"Spawned agent {i+1}/{len(pipeline.config.agents)}: {agent_type}")

            # Run agents
            mode = pipeline.config.mode
            results = await orchestrator.run(mode=mode)

            # Compile results
            execution_result = {
                "pipeline_name": pipeline.config.name,
                "mode": mode,
                "agent_results": [self._result_to_dict(r) for r in results],
                "summary": orchestrator.get_summary(),
            }

            # Overall success
            execution_result["success"] = all(
                r.status.value == "completed" for r in results
            )

            logger.info(
                f"Pipeline completed. Success: {execution_result['success']}. "
                f"Summary: {execution_result['summary']}"
            )

            return execution_result

        finally:
            await orchestrator.teardown()

    async def run_pipeline_file(
        self, yaml_path: str, variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Run a pipeline from a YAML file.

        Args:
            yaml_path: Path to pipeline YAML file
            variables: Optional variables to substitute

        Returns:
            Dictionary with execution results
        """
        pipeline = Pipeline.from_yaml(yaml_path)
        return await self.run_pipeline(pipeline, variables)

    def _result_to_dict(self, result: AgentResult) -> Dict[str, Any]:
        """Convert AgentResult to dictionary.

        Args:
            result: Agent result

        Returns:
            Dictionary representation
        """
        return {
            "agent_id": result.agent_id,
            "agent_type": result.agent_type,
            "status": result.status.value,
            "output": result.output,
            "error": result.error,
            "execution_time": result.execution_time,
            "metadata": result.metadata,
        }
