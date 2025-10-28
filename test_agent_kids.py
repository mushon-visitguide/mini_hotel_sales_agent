#!/usr/bin/env python3
"""Test full agent with 2 adults and 3 kids query"""
import asyncio
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from agent.core.orchestrator import Orchestrator
from src.conversation import ContextManager

load_dotenv()

async def test_agent():
    """Run agent with kids query"""

    # Initialize orchestrator
    orchestrator = Orchestrator.create_default()

    # Initialize conversation context
    session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    context_manager = ContextManager.create(
        session_id=session_id,
        hotel_id="wayinn",
        pms_type="minihotel"
    )

    print("=" * 70)
    print("TESTING: Full agent with 2 adults and 3 kids")
    print("=" * 70)
    print()

    # Test query
    user_message = "Do you have rooms for 2 adults and 3 kids for 3 nights starting in Hanukkah?"

    print(f"User: {user_message}")
    print()
    print("-" * 70)
    print("Agent Response:")
    print("-" * 70)

    # Process message
    result = await orchestrator.process_message(
        message=user_message,
        pms_type="minihotel",
        pms_username=os.getenv("MINIHOTEL_USERNAME"),
        pms_password=os.getenv("MINIHOTEL_PASSWORD"),
        hotel_id="wayinn",
        pms_use_sandbox=False,
        pms_url_code="thewayinn",
        context_manager=context_manager,
        debug=True
    )

    print(result['response'])
    print()
    print("=" * 70)
    print(f"Tools called: {result.get('tools_called', [])}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_agent())
