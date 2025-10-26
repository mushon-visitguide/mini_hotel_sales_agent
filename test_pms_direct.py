#!/usr/bin/env python3
"""
Test PMS directly to see if rooms are available for Hanukkah dates
"""
import os
from datetime import date
from dotenv import load_dotenv
from src.pms.minihotel import MiniHotelClient

load_dotenv()

# Credentials
USERNAME = os.getenv("MINIHOTEL_USERNAME", "visitguide")
PASSWORD = os.getenv("MINIHOTEL_PASSWORD", "visg#!71R")
HOTEL_ID = "Oreldi71"

# Create client
client = MiniHotelClient(
    username=USERNAME,
    password=PASSWORD,
    hotel_id=HOTEL_ID,
    use_sandbox=False,
    url_code="oreldirot"
)

# Test availability for Hanukkah dates
check_in = date(2025, 12, 14)
check_out = date(2025, 12, 16)

print("=" * 70)
print("Testing Direct PMS Call")
print("=" * 70)
print(f"Hotel: {HOTEL_ID}")
print(f"Check-in: {check_in}")
print(f"Check-out: {check_out}")
print(f"Adults: 2")
print()

try:
    response = client.get_availability(
        check_in=check_in,
        check_out=check_out,
        adults=2,
        children=0,
        babies=0,
        rate_code="WEB",
        room_type_filter="*ALL*",
        board_filter="*ALL*"
    )

    print(f"✓ Response received!")
    print(f"Hotel: {response.hotel_id}")
    print(f"Currency: {response.currency}")
    print(f"Room types count: {len(response.room_types)}")
    print()

    if response.room_types:
        print("Available Rooms:")
        for i, rt in enumerate(response.room_types[:10], 1):
            print(f"\n{i}. {rt.room_type_code} - {rt.room_type_name}")
            print(f"   Available: {rt.inventory.allocation if rt.inventory else 0}")
            if rt.prices:
                min_price = min([p.price for p in rt.prices if p.price])
                print(f"   From: {min_price} {response.currency}")
    else:
        print("❌ No rooms returned from PMS!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
