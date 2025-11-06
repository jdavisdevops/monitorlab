"""Basic MonitorLab usage example."""

import asyncio
from monitorlab import TestOrchestrator, HomepageAgent, GenericTestAgent


async def main():
    """Run a basic test."""
    
    # Create orchestrator
    orchestrator = TestOrchestrator()
    await orchestrator.initialize()
    
    # Add agents
    orchestrator.add_agent(
        HomepageAgent(target_url="https://example.com")
    )
    
    orchestrator.add_agent(
        GenericTestAgent(
            task="Verify the page has proper SEO elements",
            target_url="https://example.com"
        )
    )
    
    # Run tests in parallel
    results = await orchestrator.run_parallel("Basic Example Test")
    
    # Print results
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Test Run ID: {results['test_run_id']}")
    print(f"Status: {results['status']}")
    print(f"\nStatistics:")
    for key, value in results['statistics'].items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
