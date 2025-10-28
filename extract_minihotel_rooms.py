#!/usr/bin/env python3
"""
MiniHotel Room Type Extractor
------------------------------
Extracts complete room type information from MiniHotel PMS API.
Outputs a clean text file with room codes, names, and descriptions.

Usage:
    python extract_minihotel_rooms.py

Output:
    Creates: {hotel_id}_room_types_info.txt
"""

import sys
import requests
import xml.etree.ElementTree as ET
from datetime import date, timedelta


def extract_minihotel_rooms(username, password, hotel_id):
    """
    Extract all room type information from MiniHotel API.

    Args:
        username: MiniHotel API username
        password: MiniHotel API password
        hotel_id: Hotel identifier

    Returns:
        List of room type dictionaries
    """

    print("=" * 80)
    print("MiniHotel Room Type Extractor")
    print("=" * 80)
    print(f"Hotel ID: {hotel_id}")
    print()

    # Step 1: Get complete room types list
    print("Step 1: Fetching room types list...")
    room_types = get_room_types_list(username, password, hotel_id)
    print(f"✓ Found {len(room_types)} room types")
    print()

    # Step 2: Enrich with English/Hebrew names
    print("Step 2: Enriching with detailed names...")
    enrich_room_names(room_types, username, password, hotel_id)
    print()

    # Step 3: Generate output file
    print("Step 3: Generating output file...")
    output_file = f"{hotel_id}_room_types_info.txt"
    generate_output_file(room_types, hotel_id, output_file)
    print(f"✓ File created: {output_file}")
    print()

    print("=" * 80)
    print("Extraction Complete!")
    print("=" * 80)

    return room_types


def get_room_types_list(username, password, hotel_id):
    """Get the complete list of room types from status inquiry."""

    today = date.today()
    tomorrow = today + timedelta(days=1)
    from_date = today.strftime("%Y-%m-%d")
    to_date = tomorrow.strftime("%Y-%m-%d")

    xml_request = f'''<?xml version="1.0" encoding="UTF-8" ?>
<AvailRaters xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<Authentication username="{username}" password="{password}" ResponseType="03" />
<Hotel id="{hotel_id}" />
<DateRange from="{from_date}" to="{to_date}" />
</AvailRaters>'''

    endpoint = "https://api.minihotel.cloud/gds"

    try:
        response = requests.post(
            endpoint,
            data=xml_request,
            headers={"Content-Type": "application/xml"},
            timeout=30,
        )
        response.raise_for_status()

        root = ET.fromstring(response.text)
        room_types_elem = root.find(".//RoomsTypes")

        room_types = []
        if room_types_elem:
            for rt_elem in room_types_elem.findall("RoomType"):
                code = rt_elem.get("Code", "")
                description = rt_elem.get("Description", "")
                if code:
                    room_types.append({
                        "code": code,
                        "description": description,
                        "name_english": None,
                        "name_hebrew": None,
                    })

        return room_types

    except Exception as e:
        print(f"✗ Error getting room types: {e}")
        return []


def enrich_room_names(room_types, username, password, hotel_id):
    """Enrich room types with English and Hebrew names from availability API."""

    # Use a date far in the future to try to get all room types
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=1)
    check_in_str = check_in.strftime("%Y-%m-%d")
    check_out_str = check_out.strftime("%Y-%m-%d")

    xml_request = f'''<?xml version="1.0" encoding="UTF-8" ?>
<AvailRaterq xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<Authentication username="{username}" password="{password}" />
<Hotel id="{hotel_id}" />
<DateRange from="{check_in_str}" to="{check_out_str}" />
<Guests adults="2" child="0" babies="0" />
<RoomTypes>
<RoomType id="*ALL*" />
</RoomTypes>
<Prices rateCode="WEB">
<Price boardCode="*MIN*" />
</Prices>
</AvailRaterq>'''

    endpoint = "https://api.minihotel.cloud/gds"

    try:
        response = requests.post(
            endpoint,
            data=xml_request,
            headers={"Content-Type": "application/xml"},
            timeout=30,
        )
        response.raise_for_status()

        root = ET.fromstring(response.text)

        # Create mapping
        name_map = {}
        for rt_elem in root.findall(".//RoomType"):
            code = rt_elem.get("id", "")
            name_e = rt_elem.get("Name_e", "")
            name_h = rt_elem.get("Name_h", "")

            if code:
                name_map[code] = {
                    "name_english": name_e if name_e else None,
                    "name_hebrew": name_h if name_h else None,
                }

        # Apply enrichment
        enriched_count = 0
        for room_type in room_types:
            code = room_type["code"]
            if code in name_map:
                room_type["name_english"] = name_map[code]["name_english"]
                room_type["name_hebrew"] = name_map[code]["name_hebrew"]
                enriched_count += 1

        print(f"✓ Enriched {enriched_count}/{len(room_types)} room types with names")

    except Exception as e:
        print(f"⚠ Warning: Could not enrich names: {e}")


def categorize_room_type(description):
    """Categorize room type based on description."""

    desc_lower = description.lower()

    if "suite" in desc_lower:
        return "Suite"
    elif "family" in desc_lower:
        return "Family Room"
    elif "studio" in desc_lower:
        return "Studio"
    else:
        return "Standard Room"


def generate_output_file(room_types, hotel_id, output_file):
    """Generate formatted text output file."""

    # Sort by code
    room_types_sorted = sorted(room_types, key=lambda x: x["code"])

    # Categorize rooms
    suites = []
    family_rooms = []
    studios = []
    standard_rooms = []

    for rt in room_types_sorted:
        category = categorize_room_type(rt["description"])
        if category == "Suite":
            suites.append(rt)
        elif category == "Family Room":
            family_rooms.append(rt)
        elif category == "Studio":
            studios.append(rt)
        else:
            standard_rooms.append(rt)

    # Generate file content
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write(f"MINIHOTEL {hotel_id.upper()} - ROOM TYPES INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Hotel ID:         {hotel_id}\n")
        f.write(f"Total Room Types: {len(room_types_sorted)}\n")
        f.write(f"Generated:        {date.today().strftime('%Y-%m-%d')}\n\n")

        # All room types
        f.write("=" * 80 + "\n")
        f.write("ALL ROOM TYPES - DETAILED INFORMATION\n")
        f.write("=" * 80 + "\n\n")

        for idx, rt in enumerate(room_types_sorted, 1):
            f.write("-" * 79 + "\n")
            f.write(f"{idx}. ROOM CODE: {rt['code']}\n")
            f.write("-" * 79 + "\n")
            f.write(f"Description:        {rt['description']}\n")
            f.write(f"English Name:       {rt.get('name_english') or 'Not Available'}\n")
            f.write(f"Hebrew Name:        {rt.get('name_hebrew') or 'Not Available'}\n")

            category = categorize_room_type(rt['description'])
            if category != "Standard Room":
                f.write(f"Room Type:          {category}\n")

            f.write("\n")

        # Categories
        f.write("=" * 80 + "\n")
        f.write("ROOM TYPES BY CATEGORY\n")
        f.write("=" * 80 + "\n\n")

        if suites:
            f.write("SUITES:\n")
            for rt in suites:
                f.write(f"  - {rt['code']} ({rt['description']})\n")
            f.write("\n")

        if family_rooms:
            f.write("FAMILY ROOMS:\n")
            for rt in family_rooms:
                f.write(f"  - {rt['code']} ({rt['description']})\n")
            f.write("\n")

        if studios:
            f.write("STUDIO:\n")
            for rt in studios:
                f.write(f"  - {rt['code']} ({rt['description']})\n")
            f.write("\n")

        if standard_rooms:
            f.write("STANDARD ROOMS:\n")
            for rt in standard_rooms:
                f.write(f"  - {rt['code']} ({rt['description']})\n")
            f.write("\n")

        # Quick reference
        f.write("=" * 80 + "\n")
        f.write("ROOM CODES - QUICK REFERENCE LIST\n")
        f.write("=" * 80 + "\n\n")

        codes = [rt['code'] for rt in room_types_sorted]
        f.write(", ".join(codes) + "\n\n")

        # Notes
        f.write("=" * 80 + "\n")
        f.write("NOTES\n")
        f.write("=" * 80 + "\n\n")
        f.write("- Room codes and descriptions extracted from MiniHotel API\n")
        f.write("- English/Hebrew names may not be available for all room types\n")
        f.write("- Categories are inferred from room descriptions\n")
        f.write("- For detailed room features, amenities, and pricing, query the\n")
        f.write("  MiniHotel availability API with specific dates\n\n")

        f.write("=" * 80 + "\n")


def main():
    """Main entry point."""

    # Configuration - Update these values
    USERNAME = "visitguide"
    PASSWORD = "visg#!71R"
    HOTEL_ID = "wayinn"

    try:
        room_types = extract_minihotel_rooms(USERNAME, PASSWORD, HOTEL_ID)

        if room_types:
            print(f"\n✓ Successfully extracted {len(room_types)} room types")
            print(f"✓ Output file: {HOTEL_ID}_room_types_info.txt\n")
            return 0
        else:
            print("\n✗ No room types found\n")
            return 1

    except Exception as e:
        print(f"\n✗ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
