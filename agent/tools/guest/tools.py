"""Guest Information Tools - Look up guest details and reservation history from PMS"""
from datetime import date, datetime
from typing import Optional
from agent.tools.registry import registry


# Hardcoded guest database (will be replaced with real PMS integration)
# Today's date for reference: 2025-10-26
GUEST_DATABASE = {
    "john@example.com": {
        "name": "John Smith",
        "email": "john@example.com",
        "phone": "+972-52-123-4567",
        "loyalty_status": "Gold Member",
        "vip": True,
        "preferences": {
            "room_type": "Suite with balcony",
            "floor": "High floor",
            "bed": "King bed",
            "pillow": "Soft pillow"
        },
        "special_notes": "Prefers quiet rooms, allergic to feather pillows",

        # Past reservations (historical stays)
        "past_reservations": [
            {
                "confirmation": "RES-2024-001",
                "check_in": "2024-08-10",
                "check_out": "2024-08-15",
                "nights": 5,
                "room_type": "228A",
                "adults": 2,
                "children": 0,
                "total_price": "4050 ILS",
                "status": "Completed"
            },
            {
                "confirmation": "RES-2024-015",
                "check_in": "2024-05-20",
                "check_out": "2024-05-23",
                "nights": 3,
                "room_type": "1102",
                "adults": 2,
                "children": 1,
                "total_price": "2400 ILS",
                "status": "Completed"
            }
        ],

        # In-house reservations (currently staying - today is 2025-10-26)
        "inhouse_reservations": [
            {
                "confirmation": "RES-2025-088",
                "check_in": "2025-10-24",
                "check_out": "2025-10-28",
                "nights": 4,
                "room_number": "228A",
                "room_type": "228A - Deluxe Suite",
                "adults": 2,
                "children": 0,
                "board": "Breakfast included",
                "total_price": "3240 ILS",
                "balance_due": "0 ILS (Paid)",
                "status": "In-House"
            }
        ],

        # Future reservations (upcoming stays)
        "future_reservations": [
            {
                "confirmation": "RES-2025-120",
                "check_in": "2025-12-25",
                "check_out": "2025-12-30",
                "nights": 5,
                "room_type": "228A",
                "adults": 2,
                "children": 0,
                "board": "Breakfast included",
                "total_price": "4500 ILS",
                "balance_due": "4500 ILS (Not paid)",
                "status": "Confirmed"
            }
        ]
    },

    "052-123-4567": {
        # Same as john@example.com (lookup by phone)
        "name": "John Smith",
        "email": "john@example.com",
        "phone": "+972-52-123-4567",
        "loyalty_status": "Gold Member",
        "vip": True,
        "preferences": {
            "room_type": "Suite with balcony",
            "floor": "High floor",
            "bed": "King bed",
            "pillow": "Soft pillow"
        },
        "special_notes": "Prefers quiet rooms, allergic to feather pillows",
        "past_reservations": [
            {
                "confirmation": "RES-2024-001",
                "check_in": "2024-08-10",
                "check_out": "2024-08-15",
                "nights": 5,
                "room_type": "228A",
                "adults": 2,
                "children": 0,
                "total_price": "4050 ILS",
                "status": "Completed"
            },
            {
                "confirmation": "RES-2024-015",
                "check_in": "2024-05-20",
                "check_out": "2024-05-23",
                "nights": 3,
                "room_type": "1102",
                "adults": 2,
                "children": 1,
                "total_price": "2400 ILS",
                "status": "Completed"
            }
        ],
        "inhouse_reservations": [
            {
                "confirmation": "RES-2025-088",
                "check_in": "2025-10-24",
                "check_out": "2025-10-28",
                "nights": 4,
                "room_number": "228A",
                "room_type": "228A - Deluxe Suite",
                "adults": 2,
                "children": 0,
                "board": "Breakfast included",
                "total_price": "3240 ILS",
                "balance_due": "0 ILS (Paid)",
                "status": "In-House"
            }
        ],
        "future_reservations": [
            {
                "confirmation": "RES-2025-120",
                "check_in": "2025-12-25",
                "check_out": "2025-12-30",
                "nights": 5,
                "room_type": "228A",
                "adults": 2,
                "children": 0,
                "board": "Breakfast included",
                "total_price": "4500 ILS",
                "balance_due": "4500 ILS (Not paid)",
                "status": "Confirmed"
            }
        ]
    },

    "sarah@example.com": {
        "name": "Sarah Cohen",
        "email": "sarah@example.com",
        "phone": "+972-54-987-6543",
        "loyalty_status": "Silver Member",
        "vip": False,
        "preferences": {
            "room_type": "Family suite",
            "floor": "Ground floor",
            "bed": "Twin beds"
        },
        "special_notes": "Traveling with small children, needs crib",
        "past_reservations": [
            {
                "confirmation": "RES-2024-078",
                "check_in": "2024-12-20",
                "check_out": "2024-12-23",
                "nights": 3,
                "room_type": "1106",
                "adults": 2,
                "children": 2,
                "total_price": "2700 ILS",
                "status": "Completed"
            }
        ],
        "inhouse_reservations": [],
        "future_reservations": []
    },

    "david@example.com": {
        "name": "David Levy",
        "email": "david@example.com",
        "phone": "+972-50-555-1234",
        "loyalty_status": "New Guest",
        "vip": False,
        "preferences": {},
        "special_notes": "",
        "past_reservations": [],
        "inhouse_reservations": [],
        "future_reservations": []
    }
}


@registry.tool(
    name="guest.get_guest_info",
    description="Get complete guest information including past, current, and future reservations"
)
async def get_guest_info(
    # PMS credentials (passed automatically from orchestrator)
    pms_type: str,
    pms_username: str,
    pms_password: str,
    hotel_id: str,
    pms_use_sandbox: bool = False,
    pms_url_code: Optional[str] = None,
    pms_agency_channel_id: Optional[int] = None,
    # Optional contact override (usually not needed - uses booking context)
    guest_name: Optional[str] = None,
    guest_email: Optional[str] = None,
    guest_phone: Optional[str] = None
) -> str:
    """
    Look up complete guest information from PMS including:
    - Guest profile (name, contact, loyalty status, preferences)
    - Past reservations (historical stays)
    - In-house reservations (currently staying)
    - Future reservations (upcoming bookings)

    This tool should be called when you need guest/reservation info to better serve the request.
    It will use the guest information already collected in the conversation (name, email, phone).

    Args:
        pms_type: PMS type (minihotel, ezgo)
        pms_username: PMS username
        pms_password: PMS password
        hotel_id: Hotel ID
        pms_use_sandbox: Use sandbox mode
        pms_url_code: URL code
        pms_agency_channel_id: Agency channel ID
        guest_name: Guest name (from booking context)
        guest_email: Guest email (from booking context)
        guest_phone: Guest phone (from booking context)

    Returns:
        String with complete guest profile and reservation history
    """
    # Determine which contact info to use for lookup
    contact = None
    if guest_email:
        contact = guest_email
    elif guest_phone:
        contact = guest_phone
    elif guest_name:
        contact = guest_name

    if not contact:
        return """
╔════════════════════════════════════════════════════════════════╗
║                    GUEST INFORMATION LOOKUP                     ║
╚════════════════════════════════════════════════════════════════╝

⚠️  NO GUEST CONTACT INFO PROVIDED

Please ask the guest for their:
  • Email address (preferred), OR
  • Phone number, OR
  • Full name

Once collected, I can look up their reservation history and preferences.
"""

    # Normalize contact
    contact_normalized = contact.strip().lower()

    # Try exact match
    guest = None
    if contact_normalized in GUEST_DATABASE:
        guest = GUEST_DATABASE[contact_normalized]
    else:
        # Try phone number variants
        contact_clean = contact_normalized.replace("-", "").replace("+972", "").replace(" ", "")
        for key, g in GUEST_DATABASE.items():
            key_clean = key.replace("-", "").replace("+972", "").replace(" ", "")
            if contact_clean == key_clean:
                guest = g
                break

        # Try name match
        if not guest:
            for g in GUEST_DATABASE.values():
                if g["name"].lower() == contact_normalized:
                    guest = g
                    break

    if not guest:
        return _format_guest_not_found(contact)

    return _format_guest_info(guest)


def _format_guest_not_found(contact: str) -> str:
    """Format message for guest not found"""
    return f"""
╔════════════════════════════════════════════════════════════════╗
║                    GUEST INFORMATION LOOKUP                     ║
╚════════════════════════════════════════════════════════════════╝

❌ GUEST NOT FOUND

Contact/Name searched: {contact}

This appears to be a NEW GUEST. Please collect their information:
  • Full name
  • Email address
  • Phone number

You can proceed with the booking and create a new guest profile.
"""


def _format_guest_info(guest: dict) -> str:
    """Format complete guest information with reservation history"""

    lines = [
        "╔════════════════════════════════════════════════════════════════╗",
        "║                    GUEST INFORMATION LOOKUP                     ║",
        "╚════════════════════════════════════════════════════════════════╝",
        "",
        "✓ RETURNING GUEST FOUND!",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "GUEST PROFILE",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Name:           {guest['name']}",
        f"Email:          {guest['email']}",
        f"Phone:          {guest['phone']}",
        f"Loyalty Status: {guest['loyalty_status']}",
    ]

    if guest.get('vip'):
        lines.append("VIP Status:     ⭐ VIP GUEST")

    # Preferences
    if guest.get('preferences'):
        lines.append("")
        lines.append("Guest Preferences:")
        for key, value in guest['preferences'].items():
            if value:
                lines.append(f"  • {key.replace('_', ' ').title()}: {value}")

    # Special notes
    if guest.get('special_notes'):
        lines.append("")
        lines.append("⚠️  Special Notes:")
        lines.append(f"  {guest['special_notes']}")

    # In-house reservations (CURRENTLY STAYING)
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🏨 IN-HOUSE RESERVATIONS (Currently Staying)")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if guest.get('inhouse_reservations'):
        for res in guest['inhouse_reservations']:
            lines.append(f"")
            lines.append(f"📋 Confirmation: {res['confirmation']}")
            lines.append(f"   Room Number:  {res['room_number']}")
            lines.append(f"   Room Type:    {res['room_type']}")
            lines.append(f"   Check-in:     {res['check_in']}")
            lines.append(f"   Check-out:    {res['check_out']} ({res['nights']} nights)")
            lines.append(f"   Guests:       {res['adults']} adults" + (f", {res['children']} children" if res['children'] > 0 else ""))
            lines.append(f"   Board:        {res['board']}")
            lines.append(f"   Total:        {res['total_price']}")
            lines.append(f"   Balance:      {res['balance_due']}")
            lines.append(f"   Status:       ✅ {res['status']}")
    else:
        lines.append("No current in-house reservations")

    # Future reservations
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📅 FUTURE RESERVATIONS")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if guest.get('future_reservations'):
        for res in guest['future_reservations']:
            lines.append(f"")
            lines.append(f"📋 Confirmation: {res['confirmation']}")
            lines.append(f"   Room Type:    {res['room_type']}")
            lines.append(f"   Check-in:     {res['check_in']}")
            lines.append(f"   Check-out:    {res['check_out']} ({res['nights']} nights)")
            lines.append(f"   Guests:       {res['adults']} adults" + (f", {res['children']} children" if res['children'] > 0 else ""))
            lines.append(f"   Board:        {res.get('board', 'Room only')}")
            lines.append(f"   Total:        {res['total_price']}")
            lines.append(f"   Balance:      {res['balance_due']}")
            lines.append(f"   Status:       {res['status']}")
    else:
        lines.append("No upcoming reservations")

    # Past reservations
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📜 PAST RESERVATIONS ({len(guest.get('past_reservations', []))} completed stays)")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if guest.get('past_reservations'):
        for res in guest['past_reservations']:
            lines.append(f"")
            lines.append(f"📋 {res['confirmation']} | {res['check_in']} to {res['check_out']} ({res['nights']} nights)")
            lines.append(f"   Room: {res['room_type']} | Guests: {res['adults']} adults" + (f", {res['children']} children" if res['children'] > 0 else ""))
            lines.append(f"   Total: {res['total_price']} | Status: {res['status']}")
    else:
        lines.append("No past reservations")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 TIP: Use this information to personalize the guest experience!")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return "\n".join(lines)
