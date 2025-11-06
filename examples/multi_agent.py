"""Multi-agent parallel testing example."""

import asyncio
from monitorlab import (
    TestOrchestrator,
    HomepageAgent,
    AuthenticationAgent,
    CheckoutAgent,
)


async def main():
    """Run multiple agents in parallel to test different features."""
    
    # Create orchestrator
    orchestrator = TestOrchestrator()
    await orchestrator.initialize()
    
    # Add multiple domain agents - each tests a complete feature
    orchestrator.add_agent(
        HomepageAgent(
            target_url="https://myecommercesite.com",
            task="Validate homepage loads correctly with all products visible"
        )
    )
    
    orchestrator.add_agent(
        AuthenticationAgent(
            target_url="https://myecommercesite.com/login",
            credentials={"username": "test@example.com", "password": "testpass"},
            task="Test login form functionality and error handling"
        )
    )
    
    orchestrator.add_agent(
        CheckoutAgent(
            target_url="https://myecommercesite.com/cart",
            task="Validate checkout flow and payment page rendering"
        )
    )
    
    # Run all agents in parallel
    # Each agent works autonomously on its feature
    print("🚀 Running 3 agents in parallel...")
    print("   - Homepage validation")
    print("   - Authentication testing")
    print("   - Checkout flow testing")
    print()
    
    results = await orchestrator.run_parallel("E-Commerce Full Suite")
    
    # Print detailed results
    print("\n" + "=" * 70)
    print("MULTI-AGENT TEST RESULTS")
    print("=" * 70)
    
    stats = results['statistics']
    print(f"\n📊 Overall Statistics:")
    print(f"   Test Run ID: #{stats['test_run_id']}")
    print(f"   Total Agents: {stats['total_agents']}")
    print(f"   Success: {stats['success']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Success Rate: {stats['success_rate']}")
    print(f"   Duration: {stats['duration_seconds']:.2f}s")
    
    print(f"\n🤖 Individual Agent Results:")
    for result in results['results']:
        status_emoji = "✅" if result['status'] == "success" else "❌"
        print(f"\n   {status_emoji} {result['agent_name'].upper()}")
        print(f"      Status: {result['status']}")
        print(f"      Task: {result['task']}")
        if result.get('screenshots'):
            print(f"      Screenshots: {len(result['screenshots'])}")
        if result.get('error'):
            print(f"      Error: {result['error']}")
    
    print("\n" + "=" * 70)
    
    # Show how to access detailed results
    print("\n💡 Tip: View full results in the Gradio UI or query the database:")
    print(f"   from monitorlab.database import TestRunRepository")
    print(f"   run = await TestRunRepository.get_test_run({stats['test_run_id']})")


if __name__ == "__main__":
    asyncio.run(main())
