#!/usr/bin/env python3
"""
Interactive Hotel Sales AI Agent

Simple interface to test the LLM-based tool planning system.
"""
import asyncio
import os
from dotenv import load_dotenv
from agent.core.orchestrator import Orchestrator

# Load environment variables
load_dotenv()

# Hotel credentials
PMS_TYPE = "minihotel"
PMS_USERNAME = os.getenv("MINIHOTEL_USERNAME", "visitguide")
PMS_PASSWORD = os.getenv("MINIHOTEL_PASSWORD", "visg#!71R")
HOTEL_ID = "wayinn"
USE_SANDBOX = False


async def main():
    """Main interactive loop"""
    print("=" * 70)
    print("🏨 Hotel Sales AI Agent - Interactive Mode")
    print("=" * 70)
    print()
    print("Initializing orchestrator...")

    # Create orchestrator
    orchestrator = Orchestrator.create_default()

    print("✓ Orchestrator ready!")
    print()
    print("Type your message to see how the LLM plans tool execution.")
    print("Type 'quit' or 'exit' to stop.")
    print()
    print("-" * 70)
    print()

    while True:
        # Get user input
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! 👋")
            break

        if not message:
            continue

        if message.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye! 👋")
            break

        print()
        print("=" * 70)
        print("📋 PLANNING & EXECUTION")
        print("=" * 70)

        try:
            # Process message with debug output
            result = await orchestrator.process_message(
                message=message,
                pms_type=PMS_TYPE,
                pms_username=PMS_USERNAME,
                pms_password=PMS_PASSWORD,
                hotel_id=HOTEL_ID,
                pms_use_sandbox=USE_SANDBOX,
                debug=True
            )

            # Print summary
            print()
            print("=" * 70)
            print("📊 RESULT SUMMARY")
            print("=" * 70)
            print(f"\n🎯 Action: {result['action']}")
            print(f"\n💭 Reasoning: {result['reasoning']}")

            print(f"\n🔧 Tools Executed: {len(result['tools'])}")
            for tool_id in result['tools']:
                status = "✅" if tool_id in result['results'] else "❌"
                print(f"  {status} {tool_id}")

            print(f"\n📦 Slots Extracted:")
            for key, value in result['slots'].items():
                if value and value != [] and value != 2:  # Skip empty/default values
                    print(f"  - {key}: {value}")

            print(f"\n📋 Results:")
            for tool_id, tool_result in result['results'].items():
                if isinstance(tool_result, dict) and 'error' in tool_result:
                    print(f"  ❌ {tool_id}: {tool_result['error']}")
                else:
                    # Show truncated result
                    result_str = str(tool_result)
                    if len(result_str) > 200:
                        result_str = result_str[:200] + "..."
                    print(f"  ✅ {tool_id}: {result_str}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        print()
        print("-" * 70)
        print()


if __name__ == "__main__":
    print()
    asyncio.run(main())
