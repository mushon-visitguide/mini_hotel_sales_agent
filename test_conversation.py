#!/usr/bin/env python3
"""
Test multi-turn conversation with stateful system
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


async def test_conversation():
    """Test a multi-turn booking conversation"""
    print("=" * 70)
    print("🧪 Testing Multi-Turn Conversation with State Management")
    print("=" * 70)
    print()

    # Create orchestrator
    orchestrator = Orchestrator.create_default()

    # Create conversation state
    session_id = "test_session_001"
    context_manager = ContextManager.create(
        session_id=session_id,
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    print(f"✓ Session initialized: {session_id}\n")

    # Simulate multi-turn conversation from docs
    conversation = [
        "I want to book a room for tomorrow night, 2 adults",
        "What rooms do you have available?",
        "Tell me more about apartment 228A",
        "What's the price for that room?",
        "Can I get breakfast included?",
    ]

    for turn, message in enumerate(conversation, 1):
        print(f"\n{'=' * 70}")
        print(f"TURN {turn}: {message}")
        print("=" * 70)

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
                debug=False  # Set to True for detailed output
            )

            # Show summary
            print(f"\n✓ Action: {result['action']}")
            print(f"✓ Tools executed: {', '.join(result['tools'])}")

            # Show slots extracted
            if result['slots']:
                print(f"✓ Slots extracted: {result['slots']}")

            # Show booking status
            booking_status = context_manager.get_booking_status()
            print(f"\n📊 Booking Status:")
            print(f"  - Ready: {booking_status['ready_for_booking']}")
            if booking_status['missing_info']:
                print(f"  - Missing: {', '.join(booking_status['missing_info'])}")

            # Show conversation stats
            stats = context_manager.get_context_stats()
            print(f"\n📈 Context Stats:")
            print(f"  - Total turns: {stats['total_turns']}")
            print(f"  - Tool executions: {stats['total_tool_executions']}")
            print(f"  - Context size: {stats['context_prompt_length']} chars")
            print(f"  - Has summary: {stats['has_summary']}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # Final summary
    print(f"\n{'=' * 70}")
    print("📋 FINAL CONVERSATION SUMMARY")
    print("=" * 70)

    final_status = context_manager.get_booking_status()
    print(f"\nBooking Context:")
    print(f"  - Check-in: {final_status['booking_context'].get('check_in')}")
    print(f"  - Check-out: {final_status['booking_context'].get('check_out')}")
    print(f"  - Adults: {final_status['booking_context'].get('adults')}")
    print(f"  - Selected room: {final_status['booking_context'].get('selected_room_code')}")
    print(f"  - Board preference: {final_status['booking_context'].get('board_preference')}")
    print(f"\nReady to book: {final_status['ready_for_booking']}")

    if final_status['missing_info']:
        print(f"Missing info: {', '.join(final_status['missing_info'])}")

    # Show context being sent to LLM
    print(f"\n{'=' * 70}")
    print("📝 CONTEXT SENT TO PLANNER (last turn)")
    print("=" * 70)
    context_prompt = context_manager.build_context_for_planner()
    print(context_prompt)

    print("\n✓ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_conversation())
