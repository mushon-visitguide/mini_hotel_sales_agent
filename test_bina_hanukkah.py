#!/usr/bin/env python3
"""
Test conversation: Ask for BINA room first, then add Hanukkah dates
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


async def test_bina_hanukkah_conversation():
    """Test: Ask for BINA room first, then Hanukkah dates"""
    print("=" * 70)
    print("🧪 Testing: BINA Room → Hanukkah Dates Conversation")
    print("=" * 70)
    print()

    orchestrator = Orchestrator.create_default()
    context_manager = ContextManager.create(
        session_id="test_bina_hanukkah",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    # Conversation flow
    conversation = [
        "I want to book a room named BINA",
        "For Hanukkah",
    ]

    for turn, message in enumerate(conversation, 1):
        print(f"\n{'=' * 70}")
        print(f"TURN {turn}")
        print(f"{'=' * 70}")
        print(f"User: {message}")
        print()

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

            # Show what happened
            print(f"Action: {result['action']}")
            print(f"Tools: {', '.join(result['tools']) if result['tools'] else 'none'}")
            print(f"Slots extracted: {result['slots']}")

            # Show booking context after this turn
            booking_status = context_manager.get_booking_status()
            booking_context = booking_status['booking_context']

            print(f"\n📊 Booking Context After Turn {turn}:")
            print(f"  check_in: {booking_context.get('check_in')}")
            print(f"  check_out: {booking_context.get('check_out')}")
            print(f"  adults: {booking_context.get('adults')}")
            print(f"  selected_room_code: {booking_context.get('selected_room_code')}")
            print(f"  guest_email: {booking_context.get('guest_email')}")

            print(f"\n✅ Ready to book: {booking_status['ready_for_booking']}")
            if booking_status['missing_info']:
                print(f"⚠️  Missing: {', '.join(booking_status['missing_info'])}")

            # Show context being sent to planner
            if turn == len(conversation):
                print(f"\n{'=' * 70}")
                print("📝 FINAL CONTEXT SENT TO PLANNER:")
                print(f"{'=' * 70}")
                context_prompt = context_manager.build_context_for_planner()
                print(context_prompt)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 70}")
    print("✓ Test complete!")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(test_bina_hanukkah_conversation())
