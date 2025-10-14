#!/usr/bin/env python3
import requests
import os
from datetime import datetime, timedelta

# Production credentials from environment variables
username = os.environ.get("MINIHOTEL_USERNAME")
password = os.environ.get("MINIHOTEL_PASSWORD")
hotel_id = "wayinn"  # Hotel ID remains configurable per instance
username = "visitguide"
password = "visg#!71R"
# XML request
if not username or not password:
    print("Error: Please set MINIHOTEL_USERNAME and MINIHOTEL_PASSWORD environment variables")
    exit(1)

# Use specific dates for July 2, 2025
from_date = "2025-11-02"
to_date = "2025-11-03"


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

print("MiniHotel Production Test")
print(f"Username: {username}")
print(f"Hotel: {hotel_id}")
print(f"Endpoint: https://api.minihotel.cloud/gds")
print("=" * 50)

response = requests.post('https://api.minihotel.cloud/gds', 
                        data=xml_request, 
                        headers={'Content-Type': 'application/xml'}, 
                        timeout=30)

print(f"Status Code: {response.status_code}")
print(f"Response:")
print(response.text)
