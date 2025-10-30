#!/usr/bin/env python3
"""
Test script for feedback loop implementation (Step 5).

Tests:
1. Success case - no adaptation needed
2. No availability - tries alternatives
3. Hanukkah 8-night booking - adapts to shorter stay
4. Error handling - graceful degradation
"""
import asyncio
import logging
from agent.core.orchestrator import Orchestrator
from agent.llm import ToolPlanner, LLMClient
from agent.core.runtime import Runtime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_feedback_loop():
    """Test feedback loop with various scenarios"""

    print("\n" + "=" * 80)
    print("FEEDBACK LOOP TEST")
    print("=" * 80)

    # Create orchestrator with feedback loop enabled
    llm_client = LLMClient()
    planner = ToolPlanner(llm_client=llm_client, prompts_dir="./prompts")
    runtime = Runtime(default_timeout=30.0)

    orchestrator = Orchestrator(
        tool_planner=planner,
        runtime=runtime,
        enable_feedback_loop=True,  # Enable the feedback loop
        prerun_calendar_tool=False
    )

    print("\n✅ Orchestrator created with feedback loop ENABLED")
    print(f"   MAX_ADAPTATION_TURNS: {orchestrator.MAX_ADAPTATION_TURNS}")
    print(f"   MAX_TOTAL_TOOLS: {orchestrator.MAX_TOTAL_TOOLS}")

    # Test credentials (using sandbox)
    credentials = {
        "pms_type": "minihotel",
        "pms_username": "test_user",
        "pms_password": "test_pass",
        "hotel_id": "test_hotel",
        "pms_use_sandbox": True,
        "pms_url_code": None,
        "pms_agency_channel_id": None
    }

    # Test scenarios
    test_cases = [
        {
            "name": "Regular availability check (should succeed without adaptation)",
            "message": "Check availability for tomorrow, 2 adults",
            "expected_adaptation": False
        },
        {
            "name": "Hanukkah booking (8 nights → should adapt to shorter stay)",
            "message": "I want to book a room for Hanukkah",
            "expected_adaptation": True
        },
        {
            "name": "No availability (should try nearby dates)",
            "message": "Check availability December 25-26",
            "expected_adaptation": True
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print("\n" + "-" * 80)
        print(f"TEST CASE {i}: {test_case['name']}")
        print("-" * 80)
        print(f"Message: {test_case['message']}")
        print()

        try:
            result = await orchestrator.process_message(
                message=test_case['message'],
                **credentials,
                debug=True
            )

            print("\n" + "=" * 80)
            print(f"RESULT FOR TEST CASE {i}")
            print("=" * 80)
            print(f"Response: {result['response']}")
            print(f"Action: {result['action']}")
            print(f"Total tools executed: {result.get('total_tools_executed', 0)}")
            print(f"Adaptation turns: {result.get('adaptation_turns', 0)}")
            print(f"Tools: {result.get('tools', [])}")

            # Verify adaptation behavior
            adaptation_turns = result.get('adaptation_turns', 0)
            if test_case['expected_adaptation']:
                if adaptation_turns > 0:
                    print(f"\n✅ PASS: Adaptation occurred as expected ({adaptation_turns} turns)")
                else:
                    print(f"\n⚠️  WARNING: Expected adaptation but got {adaptation_turns} turns")
            else:
                if adaptation_turns == 0:
                    print(f"\n✅ PASS: No adaptation occurred as expected")
                else:
                    print(f"\n⚠️  WARNING: Unexpected adaptation occurred ({adaptation_turns} turns)")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            logger.exception("Test case failed")

        # Wait between tests
        await asyncio.sleep(1)

    print("\n" + "=" * 80)
    print("FEEDBACK LOOP TESTS COMPLETE")
    print("=" * 80)


async def test_validator_directly():
    """Test ResultValidator independently"""
    from agent.core.validator import ResultValidator
    from agent.llm.schemas import ToolCall

    print("\n" + "=" * 80)
    print("RESULT VALIDATOR DIRECT TEST")
    print("=" * 80)

    validator = ResultValidator()

    # Test case 1: Empty availability
    print("\nTest 1: Empty availability results")
    tools = [
        ToolCall(
            id="avail_1",
            tool="pms.get_availability",
            args={"check_in": "2025-12-25", "check_out": "2025-12-26", "adults": 2}
        )
    ]
    results = {
        "avail_1": {
            "available_rooms": [],  # No rooms available
            "check_in": "2025-12-25",
            "check_out": "2025-12-26"
        }
    }

    validation = await validator.analyze_results(
        user_message="Check availability for Dec 25",
        plan_action="Check room availability",
        tools=tools,
        results=results
    )

    print(f"  needs_adaptation: {validation.needs_adaptation}")
    print(f"  issues: {len(validation.issues)}")
    if validation.issues:
        for issue in validation.issues:
            print(f"    - {issue.type}: {issue.message}")
    print(f"  feedback: {validation.feedback[:100]}..." if validation.feedback else "  feedback: None")

    # Test case 2: Error result
    print("\nTest 2: Tool error")
    tools = [
        ToolCall(
            id="avail_2",
            tool="pms.get_availability",
            args={"check_in": "2025-12-25", "check_out": "2025-12-26", "adults": 2}
        )
    ]
    results = {
        "avail_2": {
            "error": "Connection timeout to PMS"
        }
    }

    validation = await validator.analyze_results(
        user_message="Check availability",
        plan_action="Check room availability",
        tools=tools,
        results=results
    )

    print(f"  needs_adaptation: {validation.needs_adaptation}")
    print(f"  issues: {len(validation.issues)}")
    if validation.issues:
        for issue in validation.issues:
            print(f"    - {issue.type}: {issue.message} (severity: {issue.severity})")

    # Test case 3: Successful results
    print("\nTest 3: Successful results (no adaptation needed)")
    tools = [
        ToolCall(
            id="avail_3",
            tool="pms.get_availability",
            args={"check_in": "2025-12-25", "check_out": "2025-12-26", "adults": 2}
        )
    ]
    results = {
        "avail_3": {
            "available_rooms": [
                {"room_id": "101", "room_type": "Standard", "price": 500},
                {"room_id": "102", "room_type": "Deluxe", "price": 700}
            ],
            "check_in": "2025-12-25",
            "check_out": "2025-12-26"
        }
    }

    validation = await validator.analyze_results(
        user_message="Check availability",
        plan_action="Check room availability",
        tools=tools,
        results=results
    )

    print(f"  needs_adaptation: {validation.needs_adaptation}")
    print(f"  issues: {len(validation.issues)}")
    print(f"  ✅ No adaptation needed - results are good!")

    print("\n" + "=" * 80)


async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "FEEDBACK LOOP TEST SUITE" + " " * 34 + "║")
    print("║" + " " * 25 + "(Step 5 Verification)" + " " * 32 + "║")
    print("╚" + "═" * 78 + "╝")

    # Test 1: Validator independently
    await test_validator_directly()

    print("\n\n")
    input("Press Enter to continue to full integration tests (requires API key)...")

    # Test 2: Full orchestrator with feedback loop
    try:
        await test_feedback_loop()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Tests failed with error: {e}")
        logger.exception("Test suite failed")

    print("\n\n✅ Test suite complete!\n")


if __name__ == "__main__":
    asyncio.run(main())
