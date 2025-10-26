#!/usr/bin/env python3
"""
Test that availability tool now returns ALL rooms (not filtered by room name)
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


async def test_all_rooms_returned():
    """Test that we get ALL rooms even when user mentions specific room"""
    print("=" * 70)
    print("🧪 Testing: ALL Rooms Returned (No Filtering)")
    print("=" * 70)
    print()

    orchestrator = Orchestrator.create_default()
    context_manager = ContextManager.create(
        session_id="test_all_rooms",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    message = "I want to book room BINA for 2 nights Hanukkah"

    print(f"User: {message}\n")

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

    print(f"Action: {result['action']}\n")
    print(f"Tools: {', '.join(result['tools'])}\n")

    # Check the availability results
    for tool_id, tool_result in result['results'].items():
        if 'availability' in tool_id or 'check' in tool_id:
            if isinstance(tool_result, dict):
                room_types = tool_result.get('room_types', [])
                print(f"{'=' * 70}")
                print(f"AVAILABILITY RESULTS from {tool_id}")
                print(f"{'=' * 70}")
                print(f"Total rooms returned: {len(room_types)}")

                if len(room_types) > 0:
                    print(f"\n✅ SUCCESS! Returning ALL available rooms:")
                    for i, room in enumerate(room_types[:5], 1):  # Show first 5
                        room_code = room.get('room_type_code', 'N/A')
                        room_name = room.get('room_name', room.get('room_type_name', 'N/A'))
                        available = room.get('available', 0)
                        prices = room.get('prices', [])
                        min_price = min([p.get('price', 0) for p in prices]) if prices else 0

                        print(f"  {i}. {room_code} ({room_name})")
                        print(f"     Available: {available}, From: {min_price} ILS")

                    if len(room_types) > 5:
                        print(f"  ... and {len(room_types) - 5} more rooms")
                else:
                    print(f"\n❌ PROBLEM: No rooms returned!")
                    print(f"Check-in: {tool_result.get('check_in')}")
                    print(f"Check-out: {tool_result.get('check_out')}")
                    print(f"Adults: {tool_result.get('adults')}")

    print(f"\n{'=' * 70}")
    print("Test complete!")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(test_all_rooms_returned())
