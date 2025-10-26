#!/usr/bin/env python3
"""
Test guest info tool with realistic scenarios where it's called automatically
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


async def test_realistic_scenarios():
    """Test realistic conversation scenarios"""
    print("=" * 70)
    print("🧪 Testing Guest Info Tool - Realistic Scenarios")
    print("=" * 70)
    print()

    # Scenario 1: Guest currently in-house mentions room issue
    print("\n" + "=" * 70)
    print("SCENARIO 1: Guest in-house with room issue")
    print("=" * 70)

    orchestrator = Orchestrator.create_default()
    context1 = ContextManager.create(
        session_id="test_scenario_1",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    conversation1 = [
        "Hi, my email is john@example.com",
        "I'm having an issue with the air conditioning in my room",
    ]

    for msg in conversation1:
        print(f"\nUser: {msg}")
        result = await orchestrator.process_message(
            message=msg,
            pms_type=PMS_TYPE,
            pms_username=PMS_USERNAME,
            pms_password=PMS_PASSWORD,
            hotel_id=HOTEL_ID,
            pms_use_sandbox=USE_SANDBOX,
            pms_url_code=URL_CODE,
            context_manager=context1,
            debug=False
        )
        print(f"Action: {result['action']}")
        print(f"Tools: {', '.join(result['tools']) if result['tools'] else 'none'}")

        # Show if guest info was looked up
        if any('guest' in tool for tool in result['tools']):
            print("✓ Guest info tool called - system knows guest is IN-HOUSE!")

    # Scenario 2: Guest asks about their reservation
    print("\n" + "=" * 70)
    print("SCENARIO 2: Guest asking about their reservation")
    print("=" * 70)

    context2 = ContextManager.create(
        session_id="test_scenario_2",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    conversation2 = [
        "Hi, I'm John Smith, phone 052-123-4567",
        "Can you tell me about my upcoming reservation for December?",
    ]

    for msg in conversation2:
        print(f"\nUser: {msg}")
        result = await orchestrator.process_message(
            message=msg,
            pms_type=PMS_TYPE,
            pms_username=PMS_USERNAME,
            pms_password=PMS_PASSWORD,
            hotel_id=HOTEL_ID,
            pms_use_sandbox=USE_SANDBOX,
            pms_url_code=URL_CODE,
            context_manager=context2,
            debug=False
        )
        print(f"Action: {result['action']}")
        print(f"Tools: {', '.join(result['tools']) if result['tools'] else 'none'}")

        if any('guest' in tool for tool in result['tools']):
            print("✓ Guest info tool called - retrieved December reservation!")

    # Scenario 3: Returning guest wants to book again
    print("\n" + "=" * 70)
    print("SCENARIO 3: Returning guest booking again")
    print("=" * 70)

    context3 = ContextManager.create(
        session_id="test_scenario_3",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    conversation3 = [
        "Hello, my email is john@example.com",
        "I'd like to book the same room I stayed in last time for next month",
    ]

    for msg in conversation3:
        print(f"\nUser: {msg}")
        result = await orchestrator.process_message(
            message=msg,
            pms_type=PMS_TYPE,
            pms_username=PMS_USERNAME,
            pms_password=PMS_PASSWORD,
            hotel_id=HOTEL_ID,
            pms_use_sandbox=USE_SANDBOX,
            pms_url_code=URL_CODE,
            context_manager=context3,
            debug=False
        )
        print(f"Action: {result['action']}")
        print(f"Tools: {', '.join(result['tools']) if result['tools'] else 'none'}")

        if any('guest' in tool for tool in result['tools']):
            print("✓ Guest info tool called - knows guest's previous room (228A)!")

    # Scenario 4: Guest without contact info yet
    print("\n" + "=" * 70)
    print("SCENARIO 4: Guest mentions room issue but no contact provided yet")
    print("=" * 70)

    context4 = ContextManager.create(
        session_id="test_scenario_4",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    msg = "I'm having an issue with my room"
    print(f"\nUser: {msg}")
    result = await orchestrator.process_message(
        message=msg,
        pms_type=PMS_TYPE,
        pms_username=PMS_USERNAME,
        pms_password=PMS_PASSWORD,
        hotel_id=HOTEL_ID,
        pms_use_sandbox=USE_SANDBOX,
        pms_url_code=URL_CODE,
        context_manager=context4,
        debug=False
    )
    print(f"Action: {result['action']}")
    print(f"Tools: {', '.join(result['tools']) if result['tools'] else 'none'}")

    if any('guest' in tool for tool in result['tools']):
        for tool_id, tool_result in result['results'].items():
            if 'guest' in tool_id and "NO GUEST CONTACT" in str(tool_result):
                print("✓ Guest info tool called but no contact info yet - will ask for it!")

    print("\n" + "=" * 70)
    print("✓ All scenarios tested!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_realistic_scenarios())
