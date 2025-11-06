"""Interactive chat interface for spawning agents and running tests."""

import asyncio
import logging
from typing import Optional, Dict, Any
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from monitorlab.core.orchestrator import AgentOrchestrator
from monitorlab.agents.navigator import NavigatorAgent
from monitorlab.agents.interaction import InteractionAgent
from monitorlab.agents.vision import VisionAgent
from monitorlab.agents.validator import ValidatorAgent
from monitorlab.models.llm_client import LLMClient
from monitorlab.config.settings import get_settings

logger = logging.getLogger(__name__)


class ChatInterface:
    """Interactive chat interface for MonitorLab."""

    AGENT_TYPES = {
        "navigator": NavigatorAgent,
        "interaction": InteractionAgent,
        "vision": VisionAgent,
        "validator": ValidatorAgent,
    }

    def __init__(self, settings: Optional[Any] = None):
        """Initialize chat interface.

        Args:
            settings: Optional settings object
        """
        self.settings = settings or get_settings()
        self.console = Console()
        self.llm_client = LLMClient(self.settings)
        self.orchestrator: Optional[AgentOrchestrator] = None
        self.session_active = False

    def print_welcome(self):
        """Print welcome message."""
        welcome_text = """
# Welcome to MonitorLab Chat Interface

Ask me to validate websites, test functionality, or check visual rendering.

**Examples:**
- "Check if https://example.com loads correctly"
- "Verify the login form on https://myapp.com works"
- "Take a screenshot of https://example.com and validate it looks good"
- "Test the search functionality on https://site.com"

**Commands:**
- `exit` or `quit` - Exit the chat
- `help` - Show this help message
- `status` - Show current session status
- `clear` - Clear current session

Type your request below:
"""
        self.console.print(Panel(Markdown(welcome_text), title="MonitorLab", border_style="blue"))

    def print_help(self):
        """Print help message."""
        help_text = """
## Available Commands

- `exit`, `quit` - Exit the chat interface
- `help` - Show this help message
- `status` - Show current orchestrator status
- `clear` - Clear current session and agents

## How It Works

1. Describe what you want to test or validate
2. MonitorLab will determine which agents to spawn
3. Agents will execute your request using local LLMs
4. You'll see the results with details

## Agent Types

- **Navigator**: Handles page navigation and waiting
- **Interaction**: Performs clicks, form filling, etc.
- **Vision**: Validates visual rendering with vision models
- **Validator**: Checks functionality and makes assertions
"""
        self.console.print(Markdown(help_text))

    async def initialize_orchestrator(self):
        """Initialize or reset the orchestrator."""
        if self.orchestrator:
            await self.orchestrator.teardown()

        self.orchestrator = AgentOrchestrator(settings=self.settings, shared_browser=True)
        await self.orchestrator.setup()
        self.session_active = True
        logger.info("Orchestrator initialized")

    async def process_user_request(self, user_input: str) -> Dict[str, Any]:
        """Process user request and spawn appropriate agents.

        Args:
            user_input: User's natural language request

        Returns:
            Dictionary with processing results
        """
        # Ask LLM to determine what agents to spawn
        system_prompt = """You are MonitorLab's task planner. Given a user request, determine what agents should be spawned to fulfill it.

Available agent types:
- navigator: Navigate to URLs, wait for elements
- interaction: Click buttons, fill forms, interact with page elements
- vision: Take screenshots and validate visual rendering
- validator: Validate functionality, check assertions

Respond in JSON format:
{
    "agents": [
        {"type": "navigator", "task": "Navigate to https://example.com and wait for page load"},
        {"type": "vision", "task": "Take screenshot and verify page renders correctly"},
        ...
    ],
    "mode": "sequential"  // or "parallel" if agents can run simultaneously
}

Rules:
- Always start with navigator if a URL needs to be visited
- Use interaction for form filling, clicking, etc.
- Use vision for visual validation
- Use validator for functional checks
- Order matters for sequential execution
"""

        planning_prompt = f"""User request: {user_input}

What agents should be spawned to fulfill this request?"""

        try:
            with self.console.status("[bold blue]Planning task..."):
                plan = await self.llm_client.extract_json(
                    prompt=planning_prompt,
                    system_prompt=system_prompt,
                )

            self.console.print(f"[green]✓[/green] Task plan created")

            # Display plan
            table = Table(title="Agent Plan", show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=3)
            table.add_column("Agent Type", style="cyan")
            table.add_column("Task", style="white")

            for i, agent_config in enumerate(plan.get("agents", []), 1):
                table.add_row(
                    str(i),
                    agent_config.get("type", "unknown"),
                    agent_config.get("task", "")[:80] + "...",
                )

            self.console.print(table)

            # Confirm
            self.console.print(
                f"\n[yellow]Mode:[/yellow] {plan.get('mode', 'sequential')}"
            )

            # Spawn agents
            if not self.orchestrator:
                await self.initialize_orchestrator()
            else:
                # Clear previous agents
                self.orchestrator.clear()

            for i, agent_config in enumerate(plan.get("agents", [])):
                agent_type = agent_config.get("type")
                if agent_type not in self.AGENT_TYPES:
                    self.console.print(f"[red]Unknown agent type: {agent_type}[/red]")
                    continue

                agent_class = self.AGENT_TYPES[agent_type]
                self.orchestrator.spawn_agent(
                    agent_class,
                    task=agent_config.get("task", ""),
                    agent_id=f"{agent_type}_{i}",
                )

            # Run agents
            mode = plan.get("mode", "sequential")
            with self.console.status(f"[bold blue]Running agents ({mode})..."):
                results = await self.orchestrator.run(mode=mode)

            # Display results
            self.display_results(results)

            return {
                "success": True,
                "plan": plan,
                "results": results,
            }

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            logger.exception("Error processing user request")
            return {
                "success": False,
                "error": str(e),
            }

    def display_results(self, results):
        """Display agent results.

        Args:
            results: List of AgentResult objects
        """
        self.console.print("\n")
        self.console.print(Panel("[bold green]Results[/bold green]", expand=False))

        for result in results:
            status_color = {
                "completed": "green",
                "failed": "red",
                "timeout": "yellow",
            }.get(result.status.value, "white")

            status_symbol = {
                "completed": "✓",
                "failed": "✗",
                "timeout": "⏱",
            }.get(result.status.value, "•")

            self.console.print(
                f"\n[{status_color}]{status_symbol}[/{status_color}] "
                f"[bold]{result.agent_type}[/bold] ({result.execution_time:.2f}s)"
            )

            if result.error:
                self.console.print(f"  [red]Error:[/red] {result.error}")
            elif result.output:
                # Display key output information
                if result.output.get("success"):
                    self.console.print(f"  [green]Success[/green]")

                # Show relevant output based on agent type
                if "final_url" in result.output:
                    self.console.print(f"  URL: {result.output['final_url']}")

                if "validation" in result.output:
                    val = result.output["validation"]
                    if isinstance(val, dict):
                        self.console.print(
                            f"  Valid: {val.get('overall_valid', 'unknown')}"
                        )
                        if val.get("overall_notes"):
                            self.console.print(f"  Notes: {val['overall_notes'][:100]}...")

                if "screenshot_path" in result.output:
                    self.console.print(f"  Screenshot: {result.output['screenshot_path']}")

        # Summary
        summary = self.orchestrator.get_summary()
        self.console.print(
            f"\n[bold]Summary:[/bold] {summary['completed']}/{summary['total_agents']} "
            f"completed, {summary['failed']} failed ({summary['success_rate']})"
        )

    def display_status(self):
        """Display current session status."""
        if not self.orchestrator or not self.session_active:
            self.console.print("[yellow]No active session[/yellow]")
            return

        summary = self.orchestrator.get_summary()
        table = Table(title="Session Status", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Active Agents", str(len(self.orchestrator.agents)))
        table.add_row("Completed", str(summary.get("completed", 0)))
        table.add_row("Failed", str(summary.get("failed", 0)))
        table.add_row("Success Rate", summary.get("success_rate", "0%"))

        self.console.print(table)

    async def start(self):
        """Start the interactive chat interface."""
        self.print_welcome()

        try:
            # Initialize orchestrator
            await self.initialize_orchestrator()

            # Main loop
            while True:
                try:
                    # Get user input
                    user_input = self.console.input("\n[bold cyan]You:[/bold cyan] ").strip()

                    if not user_input:
                        continue

                    # Handle commands
                    if user_input.lower() in ["exit", "quit"]:
                        self.console.print("[yellow]Goodbye![/yellow]")
                        break

                    elif user_input.lower() == "help":
                        self.print_help()
                        continue

                    elif user_input.lower() == "status":
                        self.display_status()
                        continue

                    elif user_input.lower() == "clear":
                        await self.initialize_orchestrator()
                        self.console.print("[green]Session cleared[/green]")
                        continue

                    # Process user request
                    await self.process_user_request(user_input)

                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                    continue

        finally:
            # Cleanup
            if self.orchestrator:
                await self.orchestrator.teardown()
                self.session_active = False


async def main():
    """Main entry point for chat interface."""
    interface = ChatInterface()
    await interface.start()


if __name__ == "__main__":
    asyncio.run(main())
