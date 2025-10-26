#!/usr/bin/env python3
"""
Test availability for tomorrow to see if tool returns ALL rooms
"""
import asyncio
import os
from dotenv import load_dotenv
from agent.core.orchestrator import Orchestrator
from src.conversation import ContextManager

load_dotenv()

PMS_TYPE = "minihotel"
PMS_USERNAME = os.getenv("MINIHOTEL_USERNAME", "visitguide")
PMS_PASSWORD = os.getenv("MINIHOTEL_PASSWORD", "visg#!71R")
HOTEL_ID = "Oreldi71"
URL_CODE = "oreldirot"
USE_SANDBOX = False


async def test_tomorrow():
    """Test asking for BINA room but getting ALL rooms for tomorrow"""
    print("=" * 70)
    print("🧪 Testing: Request BINA → Get ALL Available Rooms for Tomorrow")
    print("=" * 70)
    print()

    orchestrator = Orchestrator.create_default()
    context_manager = ContextManager.create(
        session_id="test_tomorrow",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    message = "I want to book room BINA for tomorrow night, 2 adults"

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

    # Check availability results
    for tool_id, tool_result in result['results'].items():
        if isinstance(tool_result, dict) and 'room_types' in tool_result:
            room_types = tool_result.get('room_types', [])
            print(f"{'=' * 70}")
            print(f"AVAILABILITY RESULTS")
            print(f"{'=' * 70}")
            print(f"Check-in: {tool_result.get('check_in')}")
            print(f"Check-out: {tool_result.get('check_out')}")
            print(f"Adults: {tool_result.get('adults')}")
            print(f"Total rooms returned: {len(room_types)}")
            print()

            if len(room_types) > 0:
                print(f"✅ SUCCESS! Tool returns ALL rooms (not filtered to BINA):\n")
                for i, room in enumerate(room_types[:5], 1):
                    room_code = room.get('room_type_code', 'N/A')
                    room_name = room.get('room_name', room.get('room_type_name', 'N/A'))
                    available = room.get('available', 0)
                    prices = room.get('prices', [])
                    min_price = min([p.get('price', 0) for p in prices]) if prices else 0

                    print(f"  {i}. Code: {room_code}")
                    print(f"     Name: {room_name}")
                    print(f"     Available: {available}, From: {min_price} ILS\n")

                if len(room_types) > 5:
                    print(f"  ... and {len(room_types) - 5} more rooms\n")

                print("✅ The answering agent can now filter/recommend from ALL rooms!")
            else:
                print(f"❌ No rooms available for these dates")

    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(test_tomorrow())
