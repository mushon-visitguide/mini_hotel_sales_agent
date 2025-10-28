#!/usr/bin/env python3
"""
Test only Turn 1 to see what tool is called
"""
import asyncio
import os
from dotenv import load_dotenv
from agent.core.orchestrator import Orchestrator
from src.conversation import ContextManager

load_dotenv()

PMS_TYPE = "minihotel"
PMS_USERNAME = os.getenv("MINIHOTEL_USERNAME")
PMS_PASSWORD = os.getenv("MINIHOTEL_PASSWORD")
HOTEL_ID = "wayinn"
URL_CODE = "thewayinn"

async def test_turn1():
    """Test only the first question with debug enabled"""

    orchestrator = Orchestrator.create_default()
    context = ContextManager.create(
        session_id="turn1_test",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    print("=" * 70)
    print("TESTING TURN 1 ONLY")
    print("=" * 70)
    print()
    print("Question: Do you have rooms for 2 adults and 3 kids for Hanukkah?")
    print()
    print("=" * 70)
    print()

    result = await orchestrator.process_message(
        message="Do you have rooms for 2 adults and 3 kids for Hanukkah?",
        pms_type=PMS_TYPE,
        pms_username=PMS_USERNAME,
        pms_password=PMS_PASSWORD,
        hotel_id=HOTEL_ID,
        pms_use_sandbox=False,
        pms_url_code=URL_CODE,
        context_manager=context,
        debug=True  # Enable debug to see tool selection
    )

    print()
    print("=" * 70)
    print("ANALYSIS:")
    print("=" * 70)
    print(f"Action: {result['action']}")
    print(f"Tools called: {result['tools']}")
    print()
    print("Expected: Should call calendar.resolve_date_hint + pms.get_availability_and_pricing")
    print("Actual: See above")
    print()

if __name__ == "__main__":
    asyncio.run(test_turn1())
