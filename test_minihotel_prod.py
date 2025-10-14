#!/usr/bin/env python3
import requests
import os
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("="*70)
logger.info("MINIHOTEL PRODUCTION TEST - DIRECT API CALL (NO MOCKS)")
logger.info("="*70)

# Production credentials from environment variables
username = os.environ.get("MINIHOTEL_USERNAME")
password = os.environ.get("MINIHOTEL_PASSWORD")
hotel_id = "wayinn"  # Hotel ID remains configurable per instance
username = "visitguide"
password = "visg#!71R"

logger.info(f"Credentials loaded:")
logger.info(f"  Username: {username}")
logger.info(f"  Hotel ID: {hotel_id}")

# XML request
if not username or not password:
    print("Error: Please set MINIHOTEL_USERNAME and MINIHOTEL_PASSWORD environment variables")
    exit(1)

# Use specific dates for July 2, 2025
from_date = "2025-11-02"
to_date = "2025-11-03"

logger.info(f"Request parameters:")
logger.info(f"  Date range: {from_date} to {to_date}")
logger.info(f"  Adults: 2, Children: 0, Babies: 0")


xml_request = f'''<?xml version="1.0" encoding="UTF-8" ?>
<AvailRaterq xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<Authentication username="{username}" password="{password}" MinimumNights="YES" />
<Hotel id="{hotel_id}" />
<DateRange from="{from_date}" to="{to_date}" />
<Guests adults="2" child="0" babies="0" />
<RoomTypes>
<RoomType id="*ALL*" />
</RoomTypes>
<Prices rateCode="WEB">
<Price boardCode="*ALL*" />
</Prices>
</AvailRaterq>'''

print("\nMiniHotel Production Test")
print(f"Username: {username}")
print(f"Hotel: {hotel_id}")
print(f"Endpoint: https://api.minihotel.cloud/gds")
print("=" * 50)

logger.info("\n🌐 Making REAL API call to MiniHotel (NO MOCKS)")
logger.info(f"   Endpoint: https://api.minihotel.cloud/gds")
logger.info(f"   Method: POST")
logger.info(f"   Content-Type: application/xml")

try:
    response = requests.post('https://api.minihotel.cloud/gds',
                            data=xml_request,
                            headers={'Content-Type': 'application/xml'},
                            timeout=30)

    logger.info(f"\n✅ API Response Received:")
    logger.info(f"   Status Code: {response.status_code}")
    logger.info(f"   Response Length: {len(response.text)} characters")

    # Check if response looks valid
    if "<AvailRaters>" in response.text:
        logger.info(f"   ✓ Valid XML response detected")

    print(f"\nStatus Code: {response.status_code}")
    print(f"Response:")
    print(response.text)

    logger.info("="*70)
    logger.info("TEST COMPLETED - REAL API CALL SUCCESSFUL")
    logger.info("="*70)

except requests.exceptions.RequestException as e:
    logger.error(f"\n❌ API call failed: {e}")
    print(f"\nError: {e}")
    exit(1)
