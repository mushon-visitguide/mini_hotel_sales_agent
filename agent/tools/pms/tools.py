"""PMS Tools - Wrap existing PMS client methods as tools"""
import asyncio
from datetime import date
from typing import Optional
from agent.tools.registry import registry
from agent.tools.pms.enrichment import enrich_room_types


def create_pms_client(
    pms_type: str,
    pms_username: str,
    pms_password: str,
    hotel_id: str,
    pms_use_sandbox: bool = False,
    pms_url_code: Optional[str] = None,
    pms_agency_channel_id: Optional[int] = None
):
    """
    Factory to create PMS client based on type.

    Args:
        pms_type: "minihotel" or "ezgo"
        pms_username: PMS API username
        pms_password: PMS API password
        hotel_id: Hotel ID in PMS system
        pms_use_sandbox: Use sandbox mode (default: False)
        pms_url_code: URL code for MiniHotel booking links
        pms_agency_channel_id: Agency channel ID for EzGo

    Returns:
        PMSClient instance
    """
    if pms_type == "minihotel":
        from src.pms.minihotel import MiniHotelClient
        return MiniHotelClient(
            username=pms_username,
            password=pms_password,
            hotel_id=hotel_id,
            use_sandbox=pms_use_sandbox,
            url_code=pms_url_code
        )
    elif pms_type == "ezgo":
        from src.pms.ezgo import EzGoClient
        return EzGoClient(
            username=pms_username,
            password=pms_password,
            hotel_id=hotel_id,
            agency_channel_id=pms_agency_channel_id or 0
        )
    else:
        raise ValueError(f"Unknown PMS type: {pms_type}. Supported: minihotel, ezgo")


@registry.tool(
    name="pms.get_availability_and_pricing",
    description="Get real-time room availability and pricing from PMS with enriched room details",
    redact=["pms_username", "pms_password"]
)
async def get_availability(
    # PMS credentials
    pms_type: str,
    pms_username: str,
    pms_password: str,
    hotel_id: str,
    # Search parameters
    check_in: date,
    check_out: date,
    adults: int = 2,
    children: int = 0,
    babies: int = 0,
    rate_code: str = "WEB",
    board_filter: str = "*ALL*",
    # Optional PMS config
    pms_use_sandbox: bool = False,
    pms_url_code: Optional[str] = None,
    pms_agency_channel_id: Optional[int] = None
) -> str:
    """
    Get availability from PMS system.

    Returns human-readable formatted text with availability and pricing information.
    """
    # Create PMS client
    client = create_pms_client(
        pms_type=pms_type,
        pms_username=pms_username,
        pms_password=pms_password,
        hotel_id=hotel_id,
        pms_use_sandbox=pms_use_sandbox,
        pms_url_code=pms_url_code,
        pms_agency_channel_id=pms_agency_channel_id
    )

    # Call PMS availability
    loop = asyncio.get_event_loop()

    response = await loop.run_in_executor(
        None,
        lambda: client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            babies=babies,
            rate_code=rate_code,
            room_type_filter="*ALL*",  # Always get all rooms - answering agent will filter
            board_filter=board_filter
        )
    )

    # Convert ALL room types to dict format (use response.room_types directly)
    room_types = [
        {
            "room_type_code": rt.room_type_code,
            "room_type_name": rt.room_type_name,
            "available": rt.inventory.allocation if rt.inventory else 0,
            "prices": [
                {
                    "board_code": p.board_code,
                    "board_description": p.board_description,
                    "price": p.price,
                    "price_non_refundable": p.price_non_refundable
                }
                for p in (rt.prices or [])
            ],
            "max_adults": rt.max_adults,
            "max_children": rt.max_children,
            "max_babies": rt.max_babies
        }
        for rt in (response.room_types or [])
    ]

    # Enrich rooms with mapping data (adds room_name and room_desc)
    enriched_rooms = enrich_room_types(room_types, hotel_id)

    # Calculate number of nights
    nights = (response.check_out - response.check_in).days

    # Format guest info
    guest_info = f"{response.adults} adult{'s' if response.adults != 1 else ''}"
    if response.children > 0:
        guest_info += f", {response.children} child{'ren' if response.children != 1 else ''}"
    if response.babies > 0:
        guest_info += f", {response.babies} baby/babies"

    # Build formatted text output
    output_lines = [
        f"=== AVAILABILITY FOR {response.hotel_name.upper()} ===",
        "",
        f"Check-in: {response.check_in.strftime('%B %d, %Y')}",
        f"Check-out: {response.check_out.strftime('%B %d, %Y')}",
        f"Number of nights: {nights}",
        f"Guests: {guest_info}",
        "",
        f"I have found the following {len(enriched_rooms)} available room(s):",
        ""
    ]

    # Add each room
    for i, room in enumerate(enriched_rooms, 1):
        output_lines.append(f"{i}. {room.get('room_name', 'Unknown Room')}")
        output_lines.append(f"   Available: {room['available']} room(s)")

        # Add pricing options
        if room.get('prices'):
            output_lines.append("   Pricing:")
            for price_option in room['prices']:
                board_desc = price_option['board_description']
                price_val = price_option['price']
                output_lines.append(f"      - {board_desc}: {price_val} {response.currency}")

        # Add room description
        if room.get('room_desc'):
            output_lines.append(f"   Description: {room['room_desc']}")

        output_lines.append("")  # Blank line between rooms

    return "\n".join(output_lines)


@registry.tool(
    name="pms.generate_booking_link",
    description="Generate booking link with pre-filled parameters",
    redact=["pms_username", "pms_password"]
)
async def generate_booking_link(
    # PMS credentials
    pms_type: str,
    pms_username: str,
    pms_password: str,
    hotel_id: str,
    # Booking parameters
    check_in: date,
    check_out: date,
    adults: int,
    children: int = 0,
    babies: int = 0,
    room_type_code: Optional[str] = None,
    # Optional PMS config
    pms_use_sandbox: bool = False,
    pms_url_code: Optional[str] = None,
    pms_agency_channel_id: Optional[int] = None,
    # Optional URL parameters
    language: str = "en",
    currency: str = "ILS"
) -> str:
    """
    Generate booking link.

    Returns:
        str: Natural language message with the booking link
    """
    # Create PMS client
    client = create_pms_client(
        pms_type=pms_type,
        pms_username=pms_username,
        pms_password=pms_password,
        hotel_id=hotel_id,
        pms_use_sandbox=pms_use_sandbox,
        pms_url_code=pms_url_code,
        pms_agency_channel_id=pms_agency_channel_id
    )

    # Generate link
    url = client.generate_booking_link(
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        children=children,
        babies=babies,
        room_type_code=room_type_code,
        language=language,
        currency=currency
    )

    return f"Here is your booking link: {url}"
