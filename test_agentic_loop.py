"""Quick test of agentic loop with holiday query"""
import asyncio
import os
from agent.core.orchestrator import Orchestrator

# Wayinn hotel credentials
PMS_TYPE = "minihotel"
PMS_USERNAME = "visitguide"
PMS_PASSWORD = "visg#!71R"
HOTEL_ID = "wayinn"
USE_SANDBOX = False


async def test_holiday_query():
    """Test agentic loop with date-only query"""
    print("\n" + "=" * 70)
    print("AGENTIC LOOP TEST: Date-Only Query")
    print("=" * 70)

    # Create orchestrator
    orchestrator = Orchestrator.create_default()

    # Test message - date-only query (should NOT check availability)
    message = "book a room for one night during Hanukkah"

    print(f"\nMessage: '{message}'")
    print("\nExecuting...\n")

    # Process with debug enabled
    result = await orchestrator.process_message(
        message=message,
        pms_type=PMS_TYPE,
        pms_username=PMS_USERNAME,
        pms_password=PMS_PASSWORD,
        hotel_id=HOTEL_ID,
        pms_use_sandbox=USE_SANDBOX,
        debug=True  # Enable debug output
    )

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Action: {result['action']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Tools executed: {result['tools']}")
    print(f"Results keys: {list(result['results'].keys())}")
    print("\n" + "=" * 70)

    # Verify expectations
    assert result['iterations'] >= 1, "Should have at least 1 iteration"
    assert len(result['results']) > 0, "Should have tool results"

    print("\n✓ Agentic loop test PASSED")
    print(f"  - {result['iterations']} iterations completed")
    print(f"  - {len(result['results'])} tool results returned")

    return result


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        exit(1)

    # Run test
    asyncio.run(test_holiday_query())
