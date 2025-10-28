#!/usr/bin/env python3
"""
Test pms.get_availability_and_pricing tool to see what it returns
"""
import asyncio
import os
from datetime import date, timedelta
from dotenv import load_dotenv
from agent.tools.pms.tools import get_availability

load_dotenv()

async def test_availability():
    """Call the availability tool and display output"""
    print("=" * 70)
    print("Testing: pms.get_availability_and_pricing")
    print("=" * 70)
    print()

    check_in = date(2025, 10, 28)
    check_out = date(2025, 10, 29)

    print(f"Check-in: {check_in}")
    print(f"Check-out: {check_out}")
    print(f"Adults: 2")
    print(f"Children: 0")
    print()

    result = await get_availability(
        pms_type="minihotel",
        pms_username=os.getenv("MINIHOTEL_USERNAME"),
        pms_password=os.getenv("MINIHOTEL_PASSWORD"),
        hotel_id="wayinn",
        pms_url_code="thewayinn",
        pms_use_sandbox=False,
        check_in=check_in,
        check_out=check_out,
        adults=2,
        children=0,
        babies=0,
        rate_code="WEB",
        board_filter="*ALL*"
    )

    print("OUTPUT:")
    print("-" * 70)
    print(result)
    print("-" * 70)
    print()
    print(f"Output type: {type(result)}")
    if isinstance(result, dict):
        print(f"Number of rooms: {len(result.get('room_types', []))}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_availability())
