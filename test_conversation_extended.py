#!/usr/bin/env python3
"""
Test extended multi-turn conversation to see summarization in action
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


async def test_extended_conversation():
    """Test conversation with 10+ turns to see summarization"""
    print("=" * 70)
    print("🧪 Testing Extended Conversation (10 turns)")
    print("=" * 70)
    print()

    orchestrator = Orchestrator.create_default()
    context_manager = ContextManager.create(
        session_id="test_session_extended",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    # Extended conversation
    conversation = [
        "I want to book a room for tomorrow night, 2 adults",
        "What rooms do you have available?",
        "Tell me about apartment 228A",
        "What's the price?",
        "Can I get breakfast included?",
        # Continue after first summarization (should happen after turn 5)
        "What about room 228B? Is it cheaper?",
        "What's the difference between 228A and 228B?",
        "Ok I'll take 228A with breakfast",
        "My name is John Smith",
        "My email is john@example.com",
    ]

    for turn, message in enumerate(conversation, 1):
        print(f"\n{'─' * 70}")
        print(f"TURN {turn}: {message}")
        print(f"{'─' * 70}")

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

            print(f"Action: {result['action']}")
            print(f"Tools: {', '.join(result['tools']) if result['tools'] else 'none'}")

            # Show booking status
            booking_status = context_manager.get_booking_status()
            stats = context_manager.get_context_stats()

            print(f"\nBooking Ready: {booking_status['ready_for_booking']} | "
                  f"Turn: {stats['total_turns']} | "
                  f"Tools: {stats['total_tool_executions']} | "
                  f"Context: {stats['context_prompt_length']} chars | "
                  f"Summarized: {stats['has_summary']}")

            if booking_status['missing_info']:
                print(f"Missing: {', '.join(booking_status['missing_info'])}")

            # Show when summarization happens
            if stats['has_summary'] and turn == 5:
                print(f"\n🔄 SUMMARIZATION TRIGGERED!")

            if stats['has_summary'] and stats['summary_version'] > 1:
                print(f"\n🔄 RE-SUMMARIZATION! (version {stats['summary_version']})")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # Final summary
    print(f"\n{'═' * 70}")
    print("📋 FINAL STATE")
    print(f"{'═' * 70}")

    final_status = context_manager.get_booking_status()
    final_stats = context_manager.get_context_stats()

    print(f"\n📊 Stats:")
    print(f"  Turns: {final_stats['total_turns']}")
    print(f"  Tools executed: {final_stats['total_tool_executions']}")
    print(f"  Context size: {final_stats['context_prompt_length']} chars")
    print(f"  Summary version: {final_stats['summary_version']}")
    print(f"  Last summarized at turn: {final_stats['last_summarized_turn']}")

    print(f"\n🎫 Booking Context:")
    bc = final_status['booking_context']
    print(f"  Check-in: {bc.get('check_in')}")
    print(f"  Check-out: {bc.get('check_out')}")
    print(f"  Guests: {bc.get('adults')} adults")
    print(f"  Room: {bc.get('selected_room_code')}")
    print(f"  Board: {bc.get('board_preference')}")
    print(f"  Guest: {bc.get('guest_name')}")
    print(f"  Email: {bc.get('guest_email')}")

    print(f"\n✅ Ready to book: {final_status['ready_for_booking']}")
    if final_status['missing_info']:
        print(f"⚠️  Still missing: {', '.join(final_status['missing_info'])}")

    # Show final context
    print(f"\n{'═' * 70}")
    print("📝 CONTEXT SENT TO PLANNER (final)")
    print(f"{'═' * 70}")
    context = context_manager.build_context_for_planner()
    print(context)

    print("\n✓ Extended test complete!")


if __name__ == "__main__":
    asyncio.run(test_extended_conversation())
