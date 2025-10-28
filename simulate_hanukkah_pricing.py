#!/usr/bin/env python3
"""
Simulate the Hanukkah pricing issue scenario:
1. Ask about rooms for 2 adults and 3 kids for Hanukkah
2. Ask about amenities (informative)
3. Ask about breakfast options (informative)
4. Ask about check-in time (informative)
5. Ask what if we remove a child, what is the best room?
6. Ask for the price
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

async def simulate_conversation():
    """Simulate the Hanukkah pricing scenario"""

    orchestrator = Orchestrator.create_default()
    context = ContextManager.create(
        session_id="hanukkah_pricing_test",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    print("=" * 70)
    print("SIMULATING HANUKKAH PRICING SCENARIO")
    print("=" * 70)
    print()

    questions = [
        "Do you have rooms for 2 adults and 3 kids for Hanukkah?",
        "What amenities are included?",
        "Do you have breakfast options?",
        "What's the check-in time?",
        "What if we remove a child, what is the best room?",
        "What's the price?"
    ]

    for i, question in enumerate(questions, 1):
        print(f"TURN {i}: {question}")
        print("-" * 70)

        result = await orchestrator.process_message(
            message=question,
            pms_type=PMS_TYPE,
            pms_username=PMS_USERNAME,
            pms_password=PMS_PASSWORD,
            hotel_id=HOTEL_ID,
            pms_use_sandbox=False,
            pms_url_code=URL_CODE,
            context_manager=context,
            debug=False
        )

        response = result.get('response', 'NO RESPONSE')
        print(f"User: {question}")
        print(f"Assistant: {response}")
        print()

    print("=" * 70)
    print("ISSUE CHECK - Turn 6 (Price question):")
    print("Does the final response mention actual prices?")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(simulate_conversation())
