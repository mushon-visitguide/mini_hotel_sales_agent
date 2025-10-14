# FAQ Module - The Way Inn Hotel

## Overview

The FAQ module provides 5 comprehensive FAQ sections for The Way Inn boutique hotel in Tzfat (Safed), Israel. Each section is implemented as an independent method that returns static, detailed string responses.

This module is **AI agent agnostic** - each method can be called independently as a tool by any conversational AI system.

## Structure

```
src/faq/
├── __init__.py           # Module initialization
├── faq_client.py         # Main FAQClient class with 5 methods
├── example_usage.py      # Usage examples and AI agent integration demo
└── README.md            # This file
```

## Installation

The FAQ module is located in `src/faq/` and can be imported like this:

```python
from src.faq import FAQClient

# Or if you're in the src directory:
from faq import FAQClient
```

## The 5 FAQ Sections

### 1. Rooms & Pricing (`get_rooms_and_pricing_info()`)

**What it covers:**
- 10 unique suite types (named after Kabbalistic Sefirot)
- Room sizes (25-75 sqm)
- Bed configurations and capacity
- Standard amenities in all rooms
- Specific amenities per suite
- Pricing information and payment methods
- Special offers and partnerships

**Use when guests ask about:**
- "What room types do you have?"
- "How much does a room cost?"
- "What's included in the room?"
- "Can you accommodate a family of 5?"
- "Do you have rooms with terraces?"

### 2. Policies & Procedures (`get_policies_and_procedures_info()`)

**What it covers:**
- Office hours
- Check-in/check-out times
- Cancellation policies (standard and holiday periods)
- Payment methods
- Children and age policies
- Pet policy
- Accessibility information
- Kosher policies and Shabbat-friendly features
- Holiday-specific policies (Passover, Sukkot)

**Use when guests ask about:**
- "What time is check-in?"
- "What's your cancellation policy?"
- "Are you kosher?"
- "Do you accept pets?"
- "Is the property wheelchair accessible?"

### 3. Facilities & Services (`get_facilities_and_services_info()`)

**What it covers:**
- Location and directions (GPS, parking, bus)
- Property facilities (rooftop terrace, courtyards, WiFi)
- Hammam (Turkish bath) and spa services
- Full massage treatment menu with prices
- Dining options (on-site for groups, nearby restaurants)
- Private events and workshops
- Activities and experiences
- Nearby attractions and services
- Gallery recommendations

**Use when guests ask about:**
- "Where are you located?"
- "Do you have a spa?"
- "What activities are nearby?"
- "Can you host our event?"
- "What restaurants are close by?"

### 4. My Reservations (`get_my_reservations_info(guest_name)`)

**What it covers:**
- Guest's upcoming reservations
- Past reservation history
- Quick actions: modify, cancel, extend, change dates
- Cancellation policy reminder
- Booking new stay information
- Contact information for reservation changes

**Note:** This is a template response. In a live system, this would query actual reservation data from a database.

**Use when guests ask about:**
- "Show me my reservations"
- "What are my upcoming bookings?"
- "I want to cancel my reservation"
- "Can I change my dates?"

### 5. My Stay Guide (`get_my_stay_guide_info()`)

**What it covers:**
- Entry gate code (c1627)
- WiFi password (12345678)
- Lost key procedure (spare key locations and codes)
- Detailed directions to each suite
- Service closet location
- Troubleshooting guides:
  - No hot water (heater locations per suite)
  - Coffee machine usage
  - No electricity (Shabbat timer reset)
- Emergency contacts
- Check-out reminders

**Use when guests ask about:**
- "What's the WiFi password?"
- "How do I get to my room?"
- "The hot water isn't working"
- "How do I use the coffee machine?"
- "I lost my key"

## Usage Examples

### Basic Usage

```python
from faq import FAQClient

# Initialize the client
faq = FAQClient()

# Get rooms and pricing information
rooms_info = faq.get_rooms_and_pricing_info()
print(rooms_info)

# Get policies and procedures
policies = faq.get_policies_and_procedures_info()
print(policies)

# Get facilities and services
facilities = faq.get_facilities_and_services_info()
print(facilities)

# Get personalized reservation info
reservations = faq.get_my_reservations_info(guest_name="Sarah Cohen")
print(reservations)

# Get stay guide
guide = faq.get_my_stay_guide_info()
print(guide)
```

### AI Agent Tool Integration

Each method can be registered as an independent tool for AI agents:

```python
from faq import FAQClient

faq = FAQClient()

# Define tools for AI agent
tools = [
    {
        "name": "get_rooms_and_pricing_info",
        "description": "Get information about room types, bed configurations, amenities, and pricing",
        "function": faq.get_rooms_and_pricing_info,
    },
    {
        "name": "get_policies_and_procedures_info",
        "description": "Get check-in/out times, cancellation policy, payment methods, kosher info",
        "function": faq.get_policies_and_procedures_info,
    },
    {
        "name": "get_facilities_and_services_info",
        "description": "Get info about spa, hammam, location, activities, and nearby attractions",
        "function": faq.get_facilities_and_services_info,
    },
    {
        "name": "get_my_reservations_info",
        "description": "Get guest's past and upcoming reservations with quick actions",
        "function": faq.get_my_reservations_info,
    },
    {
        "name": "get_my_stay_guide_info",
        "description": "Get door codes, WiFi, directions to suite, and troubleshooting help",
        "function": faq.get_my_stay_guide_info,
    },
]

# AI agent can now select appropriate tool based on user query
# Example: User asks "What time is check-in?"
# Agent selects: get_policies_and_procedures_info()
response = faq.get_policies_and_procedures_info()
```

### OpenAI Function Calling Example

```python
from faq import FAQClient
import openai

faq = FAQClient()

# Define functions for OpenAI
functions = [
    {
        "name": "get_rooms_and_pricing_info",
        "description": "Get comprehensive information about hotel room types, configurations, amenities, and pricing",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_policies_and_procedures_info",
        "description": "Get hotel policies including check-in/out, cancellation, payment, kosher policies",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_facilities_and_services_info",
        "description": "Get information about hotel location, facilities, spa, activities, and nearby attractions",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_my_reservations_info",
        "description": "Get guest's reservation information and quick action options",
        "parameters": {
            "type": "object",
            "properties": {
                "guest_name": {"type": "string", "description": "Name of the guest"}
            },
            "required": ["guest_name"],
        },
    },
    {
        "name": "get_my_stay_guide_info",
        "description": "Get essential stay information including codes, WiFi, directions, and troubleshooting",
        "parameters": {"type": "object", "properties": {}},
    },
]

# Function mapping
function_map = {
    "get_rooms_and_pricing_info": faq.get_rooms_and_pricing_info,
    "get_policies_and_procedures_info": faq.get_policies_and_procedures_info,
    "get_facilities_and_services_info": faq.get_facilities_and_services_info,
    "get_my_reservations_info": faq.get_my_reservations_info,
    "get_my_stay_guide_info": faq.get_my_stay_guide_info,
}

# Use in OpenAI chat completion with function calling
# (implementation details depend on your OpenAI integration)
```

## Method Details

### `get_rooms_and_pricing_info() -> str`

Returns ~5,800 characters of detailed room information.

**Parameters:** None

**Returns:** String with comprehensive room and pricing details

---

### `get_policies_and_procedures_info() -> str`

Returns ~4,200 characters of policy information.

**Parameters:** None

**Returns:** String with all hotel policies and procedures

---

### `get_facilities_and_services_info() -> str`

Returns ~10,500 characters of facilities information.

**Parameters:** None

**Returns:** String with location, facilities, services, and activities

---

### `get_my_reservations_info(guest_name: str = "Guest") -> str`

Returns ~2,500 characters of reservation information.

**Parameters:**
- `guest_name` (str, optional): Name of the guest. Default: "Guest"

**Returns:** String with personalized reservation information

**Note:** This is a template. In production, integrate with actual reservation database.

---

### `get_my_stay_guide_info() -> str`

Returns ~6,800 characters of stay guide information.

**Parameters:** None

**Returns:** String with essential stay information and troubleshooting

## Integration with Existing Hotel System

The FAQ module is designed to work alongside the PMS (Property Management System) module:

- **PMS Module** (`src/pms/`): Handles real-time data (availability, pricing, bookings)
- **FAQ Module** (`src/faq/`): Handles static information (policies, facilities, guides)

Together, they provide a complete information system for hotel AI agents.

## Testing

Run the example usage file to test all methods:

```bash
cd src/faq
python3 example_usage.py
```

Or run a quick test:

```bash
python3 -c "from faq import FAQClient; faq = FAQClient(); print(faq.get_rooms_and_pricing_info()[:500])"
```

## Future Enhancements

Potential improvements for production use:

1. **Section 4 (My Reservations)**: Integrate with actual reservation database
2. **Multilanguage Support**: Add Hebrew, French, Russian translations
3. **Dynamic Content**: Pull some information from CMS or database
4. **Caching**: Add caching layer for frequently accessed sections
5. **Analytics**: Track which sections are most frequently requested
6. **Personalization**: Customize responses based on guest preferences or history

## Contact Information

For questions about this module or The Way Inn:

- **Phone:** 052-6881116
- **Email:** info@thewayinn.co.il
- **Website:** www.thewayinn.co.il

## License

This module contains proprietary information about The Way Inn boutique hotel.
