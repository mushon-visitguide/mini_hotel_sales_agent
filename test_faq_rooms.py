#!/usr/bin/env python3
"""
Test faq.get_rooms_info tool to see what it returns
"""
import asyncio
from agent.tools.faq.tools import get_rooms_info

async def test_faq_rooms():
    """Call the faq.get_rooms_info tool and display output"""
    print("=" * 70)
    print("Testing: faq.get_rooms_info")
    print("=" * 70)
    print()

    result = await get_rooms_info()

    print("OUTPUT:")
    print("-" * 70)
    print(result)
    print("-" * 70)
    print()
    print(f"Output length: {len(result)} characters")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_faq_rooms())
