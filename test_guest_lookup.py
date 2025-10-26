#!/usr/bin/env python3
"""
Test guest information lookup with in-house and past reservations
"""
import asyncio
import os
from dotenv import load_dotenv
from agent.core.orchestrator import Orchestrator
from src.conversation import ContextManager

# Load environment
load_dotenv()

# Hotel credentials
PMS_TYPE = "minihotel"
PMS_USERNAME = os.getenv("MINIHOTEL_USERNAME", "visitguide")
PMS_PASSWORD = os.getenv("MINIHOTEL_PASSWORD", "visg#!71R")
HOTEL_ID = "Oreldi71"
URL_CODE = "oreldirot"
USE_SANDBOX = False


async def test_guest_lookup():
    """Test guest lookup scenarios"""
    print("=" * 70)
    print("🧪 Testing Guest Information Lookup")
    print("=" * 70)
    print()

    orchestrator = Orchestrator.create_default()
    context_manager = ContextManager.create(
        session_id="test_guest_lookup",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    # Test scenarios
    scenarios = [
        # Scenario 1: Guest currently in-house
        "My email is john@example.com",

        # Scenario 2: Guest with past reservations only
        "I'm Sarah Cohen, email sarah@example.com",

        # Scenario 3: New guest (not found)
        "My email is newguest@example.com",

        # Scenario 4: Lookup by phone
        "My phone number is 052-123-4567",
    ]

    for i, message in enumerate(scenarios, 1):
        print(f"\n{'=' * 70}")
        print(f"SCENARIO {i}: {message}")
        print(f"{'=' * 70}")

        try:
            result = await orchestrator.process_message(
                message=message,
                pms_type=PMS_TYPE,
                pms_username=PMS_USERNAME,
                pms_password=PMS_PASSWORD,
                hotel_id=HOTEL_ID,
                pms_use_sandbox=USE_SANDBOX,
                pms_url_code=URL_CODE,
                context_manager=context_manager,
                debug=False
            )

            print(f"\n✓ Action: {result['action']}")
            print(f"✓ Tools: {', '.join(result['tools'])}")

            # Show guest lookup results
            for tool_id, tool_result in result['results'].items():
                if 'guest' in tool_id.lower():
                    print(f"\n{'─' * 70}")
                    print("GUEST INFO RESULT:")
                    print(f"{'─' * 70}")
                    if isinstance(tool_result, str):
                        print(tool_result)
                    else:
                        print(tool_result)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 70}")
    print("✓ Guest lookup test complete!")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(test_guest_lookup())
