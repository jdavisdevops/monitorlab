"""Simple usage example for MonitorLab."""

import asyncio
from monitorlab import AgentOrchestrator, NavigatorAgent, VisionAgent, ValidatorAgent


async def main():
    """Simple example of using MonitorLab programmatically."""

    # Create orchestrator
    orchestrator = AgentOrchestrator(shared_browser=True)

    try:
        # Setup
        await orchestrator.setup()

        # Spawn agents
        orchestrator.spawn_agent(
            NavigatorAgent,
            task="Navigate to https://example.com and wait for page load",
        )

        orchestrator.spawn_agent(
            VisionAgent,
            task="Take a screenshot and verify the page renders correctly",
        )

        orchestrator.spawn_agent(
            ValidatorAgent,
            task="Verify that the page title contains 'Example Domain' and the main heading is visible",
        )

        # Run agents sequentially
        results = await orchestrator.run(mode="sequential")

        # Display results
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)

        for result in results:
            print(f"\nAgent: {result.agent_type}")
            print(f"Status: {result.status.value}")
            print(f"Execution time: {result.execution_time:.2f}s")

            if result.error:
                print(f"Error: {result.error}")
            elif result.output.get("success"):
                print("✓ Success")

                # Show specific output
                if "screenshot_path" in result.output:
                    print(f"Screenshot: {result.output['screenshot_path']}")

                if "final_url" in result.output:
                    print(f"Final URL: {result.output['final_url']}")

        # Summary
        summary = orchestrator.get_summary()
        print(f"\nSummary: {summary['completed']}/{summary['total_agents']} completed")
        print(f"Success rate: {summary['success_rate']}")

    finally:
        # Cleanup
        await orchestrator.teardown()


if __name__ == "__main__":
    asyncio.run(main())
