"""PMS Tools - Wrap existing PMS client methods as tools"""
import asyncio
from datetime import date
from typing import Optional
from agent.tools.registry import registry
from src.faq.faq_client import FAQClient
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
    room_type_filter: str = "*ALL*",
    board_filter: str = "*ALL*",
    # Optional PMS config
    pms_use_sandbox: bool = False,
    pms_url_code: Optional[str] = None,
    pms_agency_channel_id: Optional[int] = None
) -> dict:
    """
    Get availability from PMS system.

    Returns dict with structure:
    {
        "hotel_id": str,
        "hotel_name": str,
        "currency": str,
        "check_in": date,
        "check_out": date,
        "room_types": [
            {
                "room_type_code": str,
                "room_type_name": str,
                "available": int,
                "prices": [
                    {
                        "board_code": str,
                        "board_description": str,
                        "price": float
                    }
                ]
            }
        ]
    }
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

    # Call PMS availability and FAQ rooms info in parallel
    loop = asyncio.get_event_loop()

    pms_task = loop.run_in_executor(
        None,
        lambda: client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            babies=babies,
            rate_code=rate_code,
            room_type_filter=room_type_filter,
            board_filter=board_filter
        )
    )

    faq_task = loop.run_in_executor(
        None,
        lambda: FAQClient().get_rooms_and_pricing_info()
    )

    # Wait for both to complete
    response, faq_rooms_info = await asyncio.gather(pms_task, faq_task)

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

    # Return enriched availability data
    return {
        "hotel_id": response.hotel_id,
        "hotel_name": response.hotel_name,
        "currency": response.currency,
        "check_in": response.check_in,
        "check_out": response.check_out,
        "adults": response.adults,
        "children": response.children,
        "babies": response.babies,
        "room_types": enriched_rooms,
        "rooms_info": faq_rooms_info  # FAQ room details for additional context
    }


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
