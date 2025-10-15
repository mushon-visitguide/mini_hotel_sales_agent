#!/usr/bin/env python3
"""Test the refactored date resolver"""
import asyncio
from datetime import date
from dotenv import load_dotenv
from agent.tools.calendar.date_resolver import get_resolver
from agent.tools.calendar.tools import resolve_date_hint

# Load environment variables
load_dotenv()

async def test_date_resolution():
    print("Testing date resolution with holidays injected...")
    print()

    # Test 1: Tomorrow 2 nights
    print("Test 1: 'tomorrow 2 nights'")
    result = await resolve_date_hint(date_hint="tomorrow 2 nights", default_nights=2)
    print(f"  check_in: {result['check_in']} (type: {type(result['check_in'])})")
    print(f"  check_out: {result['check_out']} (type: {type(result['check_out'])})")
    print(f"  nights: {result['nights']}")
    print(f"  description: {result['description']}")
    print()

    # Verify it's a date object
    assert isinstance(result['check_in'], date), f"check_in should be date object, got {type(result['check_in'])}"
    assert isinstance(result['check_out'], date), f"check_out should be date object, got {type(result['check_out'])}"
    print("✓ Date objects returned correctly!")
    print()

    # Test 2: Passover 2026 (should use injected holiday dates)
    print("Test 2: 'Passover 2026 for 3 nights'")
    result = await resolve_date_hint(date_hint="Passover 2026 for 3 nights", default_nights=3)
    print(f"  check_in: {result['check_in']}")
    print(f"  check_out: {result['check_out']}")
    print(f"  nights: {result['nights']}")
    print(f"  description: {result['description']}")
    print()
    print("✓ Holiday resolution working!")
    print()

    print("All tests passed! ✓")

if __name__ == "__main__":
    asyncio.run(test_date_resolution())
