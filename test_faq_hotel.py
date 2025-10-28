#!/usr/bin/env python3
"""
Test faq.get_hotel_all_info tool to see what it returns
"""
import asyncio
from agent.tools.faq.tools import get_hotel_info

async def test_faq_hotel():
    """Call the faq.get_hotel_all_info tool and display output"""
    print("=" * 70)
    print("Testing: faq.get_hotel_all_info")
    print("=" * 70)
    print()

    result = await get_hotel_info()

    print("OUTPUT:")
    print("-" * 70)
    print(result)
    print("-" * 70)
    print()
    print(f"Output length: {len(result)} characters")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_faq_hotel())
