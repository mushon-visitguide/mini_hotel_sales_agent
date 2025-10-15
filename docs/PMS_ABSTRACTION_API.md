# PMS Abstraction Layer API Documentation

This document describes the abstract interface that all Property Management System (PMS) integrations must implement.

## Overview

The `PMSClient` abstract base class (`src/pms/base.py`) defines a standard interface for interacting with any hotel PMS. Different PMS systems (MiniHotel, ezGo, Opera, etc.) implement this interface with their own specific API calls.

---

## Constructor

### `__init__(username: str, password: str, hotel_id: str, cache_ttl_seconds: int = 300)`

Initialize the PMS client with authentication credentials and caching configuration.

**Parameters:**
- `username` (str): Authentication username for PMS API
- `password` (str): Authentication password for PMS API
- `hotel_id` (str): Unique identifier for the hotel in the PMS system
- `cache_ttl_seconds` (int, optional): Cache time-to-live in seconds for availability queries (default: 300 = 5 minutes)

**Returns:** None

**Example:**
```python
# Default cache TTL (5 minutes)
client = MiniHotelClient(
    username="myuser",
    password="mypass",
    hotel_id="hotel123"
)

# Custom cache TTL (10 minutes)
client = MiniHotelClient(
    username="myuser",
    password="mypass",
    hotel_id="hotel123",
    cache_ttl_seconds=600
)
```

---

## Abstract Methods

These methods **must** be implemented by all PMS integrations.

### 1. `get_room_types() -> List[RoomType]`

Retrieve all room types available in the hotel.

**Parameters:** None

**Returns:** `List[RoomType]`
- List of room type objects, each containing:
  - `code` (str): Room type code (e.g., "DBL", "SUITE")
  - `description` (str): Human-readable name (e.g., "Double Room")
  - `image_url` (Optional[str]): URL to room type image

**Raises:**
- `PMSConnectionError`: Unable to connect to PMS
- `PMSAuthenticationError`: Authentication failed
- `PMSDataError`: Invalid response from PMS

**Notes:**
- This is **static data** that can be cached
- Some PMS systems may only provide this in sandbox/test mode
- In production, room types may need to be extracted from availability responses

**Example:**
```python
room_types = client.get_room_types()
for rt in room_types:
    print(f"{rt.code}: {rt.description}")
# Output:
# DBL: Double Room
# SUITE: Executive Suite
```

---

### 2. `get_rooms(room_number: Optional[str] = None) -> List[Room]`

Retrieve detailed information about physical rooms, including occupancy limits and attributes.

**Parameters:**
- `room_number` (Optional[str]): Specific room number to retrieve. If `None`, returns all rooms.

**Returns:** `List[Room]`
- List of room objects, each containing:
  - `room_number` (str): Physical room number (e.g., "101", "205")
  - `room_type` (str): Room type code this room belongs to
  - `serial` (Optional[str]): Internal serial number
  - `status` (Optional[str]): Cleaning status ("C"=Clean, "D"=Dirty)
  - `wing` (Optional[str]): Building wing/section code
  - `color` (Optional[str]): Color coding for the room
  - `is_dorm` (bool): Whether the unit is a dormitory
  - `is_bed` (bool): Whether the unit is a single bed
  - `occupancy_limits` (Optional[List[GuestOccupancy]]): Max guests by type
    - Each `GuestOccupancy` contains:
      - `guest_type` (str): "A"=Adult, "C"=Child, "B"=Baby
      - `max_count` (int): Maximum number of this guest type
  - `attributes` (Optional[List[RoomAttribute]]): Room features/amenities
    - Each `RoomAttribute` contains:
      - `code` (str): Attribute code
      - `description` (str): Human-readable description (e.g., "Ocean View", "Balcony")
  - `image_url` (Optional[str]): URL to room image

**Raises:**
- `PMSConnectionError`: Unable to connect to PMS
- `PMSAuthenticationError`: Authentication failed
- `PMSDataError`: Invalid response from PMS

**Notes:**
- This is **static data** that can be cached
- Contains physical room details, not availability
- Occupancy limits can be derived per room type from this data

**Example:**
```python
# Get all rooms
all_rooms = client.get_rooms()

# Get specific room
room_101 = client.get_rooms(room_number="101")

# Check occupancy limits
for room in all_rooms:
    if room.occupancy_limits:
        for occ in room.occupancy_limits:
            print(f"Room {room.room_number} - {occ.guest_type}: max {occ.max_count}")
# Output:
# Room 101 - A: max 2
# Room 101 - C: max 1
# Room 101 - B: max 0
```

---

### 3. `get_availability(...) -> AvailabilityResponse`

Get real-time availability and pricing for specified dates and guest counts.

**AUTOMATIC CACHING:** This method automatically caches responses based on query parameters. Identical queries within the cache TTL window will return cached data instead of making new API calls. This improves performance and reduces API load.

**Parameters:**
- `check_in` (date): Check-in date
- `check_out` (date): Check-out date
- `adults` (int): Number of adults (must be ≥ 1)
- `children` (int, default=0): Number of children
- `babies` (int, default=0): Number of babies/infants
- `rate_code` (str, default="USD"): Rate code determining currency and pricing tier
- `room_type_filter` (str, default="*ALL*"):
  - `"*ALL*"` - All room types
  - `"*MIN*"` - Only cheapest room type
  - Specific code (e.g., `"DBL"`) - Filter for one type
- `board_filter` (str, default="*ALL*"):
  - `"*ALL*"` - All meal plans
  - `"*MIN*"` - Cheapest meal plan per room type
  - Specific code (e.g., `"BB"`) - Filter for one board type

**Returns:** `AvailabilityResponse`
- `hotel_id` (str): Hotel identifier
- `hotel_name` (str): Hotel name
- `currency` (str): Currency code for prices (e.g., "USD", "EUR")
- `check_in` (date): Requested check-in date
- `check_out` (date): Requested check-out date
- `adults` (int): Number of adults from request
- `children` (int): Number of children from request
- `babies` (int): Number of babies from request
- `room_types` (Optional[List[RoomTypeAvailability]]): Available room types
  - Each `RoomTypeAvailability` contains:
    - `room_type_code` (str): Room type code
    - `room_type_name` (str): Display name
    - `room_type_name_local` (Optional[str]): Local language name
    - `inventory` (Optional[Inventory]): Availability info
      - `allocation` (int): Number of rooms available
      - `max_available` (int): Total rooms of this type
    - `prices` (Optional[List[BoardPrice]]): Prices by meal plan
      - Each `BoardPrice` contains:
        - `board_code` (str): Meal plan code (e.g., "BB", "HB")
        - `board_description` (str): Meal plan name (e.g., "Bed & Breakfast")
        - `price` (float): **Total price for entire stay** (NOT per night)
        - `price_non_refundable` (Optional[float]): Non-refundable rate (if available)
    - **Enhanced fields (optional - depends on PMS):**
      - `max_adults` (Optional[int]): Maximum adults this room type can accommodate
      - `max_children` (Optional[int]): Maximum children this room type can accommodate
      - `max_babies` (Optional[int]): Maximum babies this room type can accommodate
      - `bed_configuration` (Optional[str]): Bed setup (e.g., "1 King", "2 Queens")
      - `size_sqm` (Optional[float]): Room size in square meters
      - `features` (Optional[List[str]]): Room features (e.g., ["Ocean View", "Balcony"])

**Raises:**
- `PMSConnectionError`: Unable to connect to PMS
- `PMSAuthenticationError`: Authentication failed
- `PMSValidationError`: Invalid parameters (dates, guest counts)
- `PMSDataError`: Invalid response from PMS

**Notes:**
- This is **dynamic data** with automatic caching (default TTL: 5 minutes)
- **CRITICAL:** Prices must come from PMS API - never hallucinated
- Cache key includes all query parameters (dates, guests, rate code, filters)
- Repeated identical queries return cached data without API calls
- Use `clear_availability_cache()` to force fresh data if needed
- `get_min_price()` method available on `RoomTypeAvailability` to find cheapest board option
- `get_max_occupancy()` method calculates total capacity (adults + children + babies)
- `get_available_rooms()` method on response filters only rooms with availability

**Example:**
```python
from datetime import date, timedelta

check_in = date.today() + timedelta(days=30)
check_out = check_in + timedelta(days=3)

response = client.get_availability(
    check_in=check_in,
    check_out=check_out,
    adults=2,
    children=1,
    rate_code="USD",
    board_filter="BB"  # Bed & Breakfast only
)

print(f"Hotel: {response.hotel_name}")
print(f"Currency: {response.currency}")
print(f"Available rooms: {len(response.get_available_rooms())}")

for room_type in response.get_available_rooms():
    print(f"\n{room_type.room_type_name}")
    print(f"  Available: {room_type.inventory.allocation} rooms")
    print(f"  Min price: ${room_type.get_min_price():.2f} (total for {(check_out - check_in).days} nights)")

    # Enhanced fields (if available)
    if room_type.max_adults:
        print(f"  Max occupancy: {room_type.get_max_occupancy()} guests")
    if room_type.features:
        print(f"  Features: {', '.join(room_type.features)}")
```

---

### 4. `generate_booking_link(...) -> str`

Generate a direct booking URL with pre-filled parameters.

**Parameters:**
- `check_in` (date): Check-in date
- `check_out` (date): Check-out date
- `adults` (int): Number of adults (must be ≥ 1)
- `children` (int, default=0): Number of children
- `babies` (int, default=0): Number of babies
- `room_type_code` (Optional[str]): Pre-select specific room type
- `rate_code` (Optional[str]): Pre-select rate code
- `board_code` (Optional[str]): Pre-select meal plan
- `**kwargs`: Additional PMS-specific parameters (e.g., `language`, `currency`)

**Returns:** `str`
- Complete booking URL as string

**Raises:**
- `PMSValidationError`: Invalid parameters

**Notes:**
- URL should direct to hotel's booking engine
- Parameters should be pre-filled based on arguments
- Each PMS may have different URL format
- Additional kwargs allow PMS-specific customization

**Example:**
```python
from datetime import date, timedelta

check_in = date.today() + timedelta(days=30)
check_out = check_in + timedelta(days=2)

link = client.generate_booking_link(
    check_in=check_in,
    check_out=check_out,
    adults=2,
    children=1,
    room_type_code="DELUXE-KING",
    language="en",
    currency="USD"
)

print(link)
# Output: https://booking.hotel.com/...?checkin=2025-11-14&checkout=2025-11-16&adults=2&children=1&room=DELUXE-KING
```

---

## Abstract Properties

These properties **must** be implemented by all PMS integrations.

### 5. `supports_guest_count -> bool`

Indicates whether this PMS supports filtering availability by number of guests.

**Parameters:** None

**Returns:** `bool`
- `True`: PMS can filter by adults/children/babies counts
- `False`: PMS only supports filtering by number of rooms

**Notes:**
- If `False`, agent should ask for number of rooms instead of guest counts
- Affects how the AI agent asks questions to guests

**Example:**
```python
if client.supports_guest_count:
    # Ask: "How many adults and children?"
    response = client.get_availability(..., adults=2, children=1)
else:
    # Ask: "How many rooms do you need?"
    # Guest count filtering not available
```

---

### 6. `supports_children_breakdown -> bool`

Indicates whether this PMS distinguishes between children and babies.

**Parameters:** None

**Returns:** `bool`
- `True`: PMS tracks children and babies separately
- `False`: PMS only tracks adults vs. total guests

**Notes:**
- If `False`, treat all non-adults as "children"
- Affects whether to ask specifically about babies/infants

**Example:**
```python
if client.supports_children_breakdown:
    # Ask: "How many children and babies?"
    response = client.get_availability(..., children=2, babies=1)
else:
    # Combine all into children parameter
    response = client.get_availability(..., children=3)
```

---

## Concrete Methods

These methods are already implemented in the base class.

### 7. `validate_dates(check_in: date, check_out: date) -> None`

Validate that dates are logical and acceptable.

**Parameters:**
- `check_in` (date): Check-in date
- `check_out` (date): Check-out date

**Returns:** None

**Raises:**
- `PMSValidationError`: If validation fails:
  - Check-out must be after check-in
  - Check-in cannot be in the past

**Notes:**
- Called automatically by `get_availability()` and `generate_booking_link()`
- Can be called manually for early validation

**Example:**
```python
from datetime import date, timedelta
from src.pms.exceptions import PMSValidationError

try:
    client.validate_dates(
        check_in=date.today() + timedelta(days=30),
        check_out=date.today() + timedelta(days=32)
    )
    print("Dates are valid")
except PMSValidationError as e:
    print(f"Invalid dates: {e}")
```

---

### 8. `clear_availability_cache() -> None`

Clear all cached availability data.

**Parameters:** None

**Returns:** None

**Notes:**
- Clears all cached availability responses
- Forces next `get_availability()` call to make fresh API request
- Useful when you know data has changed or need real-time updates
- Cache is automatically managed by TTL, manual clearing rarely needed

**Example:**
```python
# Normal usage - cache works automatically
response1 = client.get_availability(check_in, check_out, adults=2)  # API call
response2 = client.get_availability(check_in, check_out, adults=2)  # Cache hit (same params)

# Force fresh data
client.clear_availability_cache()
response3 = client.get_availability(check_in, check_out, adults=2)  # API call (cache cleared)
```

---

## Factory Pattern

### `PMSClientFactory.create(pms_type: str, ...) -> PMSClient`

Create a PMS client instance using the factory pattern.

**Parameters:**
- `pms_type` (str): Type of PMS ("minihotel", "ezgo", etc.)
- `username` (str): API username
- `password` (str): API password
- `hotel_id` (str): Hotel identifier

**Returns:** `PMSClient`
- Instance of the appropriate PMS client class

**Raises:**
- `ValueError`: Unknown PMS type

**Example:**
```python
from src.pms import PMSClientFactory

# Create MiniHotel client
client = PMSClientFactory.create(
    pms_type="minihotel",
    username="myuser",
    password="mypass",
    hotel_id="hotel123"
)

# Factory handles instantiation of correct class
assert isinstance(client, MiniHotelClient)
```

---

## Response Structures & Examples

This section shows what responses look like at different stages: from raw PMS API data to final Python objects.

### Response Flow Overview

```
┌─────────────────┐
│  PMS API Call   │  get_availability()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Raw XML/JSON  │  MiniHotel returns XML response
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parse & Build  │  Extract data, create Python objects
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Python Objects  │  AvailabilityResponse with nested data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AI Agent Use  │  Query availability, prices, features
└─────────────────┘
```

---

### Example 1: Availability Response

#### Raw XML from MiniHotel API

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AvailRaters>
    <Hotel id="wayinn" Name_e="WayInn Hotel" Name_h="מלון ווייאין" Currency="ILS">
        <DateRange from="2025-11-14" to="2025-11-16"/>
        <Guests adults="2" child="0" babies="0"/>

        <!-- Room Type 1: Available with multiple meal plans -->
        <RoomType id="DELUXE-KING" Name_e="Deluxe King Room" Name_h="חדר דלוקס קינג">
            <Inventory Allocation="3" maxavail="5"/>
            <price board="BB" boardDesc="Bed &amp; Breakfast" value="420.00" value_nrf="380.00"/>
            <price board="HB" boardDesc="Half Board" value="520.00"/>
        </RoomType>

        <!-- Room Type 2: Limited availability -->
        <RoomType id="SUITE" Name_e="Executive Suite" Name_h="סוויטה מנהלים">
            <Inventory Allocation="1" maxavail="2"/>
            <price board="BB" boardDesc="Bed &amp; Breakfast" value="650.00"/>
            <price board="FB" boardDesc="Full Board" value="850.00"/>
        </RoomType>

        <!-- Room Type 3: Sold out (no prices) -->
        <RoomType id="STANDARD" Name_e="Standard Room" Name_h="חדר סטנדרטי">
            <Inventory Allocation="0" maxavail="8"/>
        </RoomType>
    </Hotel>
</AvailRaters>
```

#### Parsed Python Object

```python
AvailabilityResponse(
    hotel_id="wayinn",
    hotel_name="WayInn Hotel",
    currency="ILS",
    check_in=date(2025, 11, 14),
    check_out=date(2025, 11, 16),
    adults=2,
    children=0,
    babies=0,
    room_types=[
        # Available room with multiple meal options
        RoomTypeAvailability(
            room_type_code="DELUXE-KING",
            room_type_name="Deluxe King Room",
            room_type_name_local="חדר דלוקס קינג",
            inventory=Inventory(
                allocation=3,      # 3 rooms available
                max_available=5    # Out of 5 total rooms
            ),
            prices=[
                BoardPrice(
                    board_code="BB",
                    board_description="Bed & Breakfast",
                    price=420.00,  # ⚠️ TOTAL for 2 nights, NOT per night!
                    price_non_refundable=380.00
                ),
                BoardPrice(
                    board_code="HB",
                    board_description="Half Board",
                    price=520.00,
                    price_non_refundable=None
                )
            ],
            # Enhanced fields (populated if cache built)
            max_adults=2,
            max_children=1,
            max_babies=0,
            bed_configuration="1 King",
            size_sqm=None,
            features=["Ocean View", "Balcony"]
        ),

        # Limited availability
        RoomTypeAvailability(
            room_type_code="SUITE",
            room_type_name="Executive Suite",
            room_type_name_local="סוויטה מנהלים",
            inventory=Inventory(allocation=1, max_available=2),
            prices=[
                BoardPrice("BB", "Bed & Breakfast", 650.00, None),
                BoardPrice("FB", "Full Board", 850.00, None)
            ],
            max_adults=2,
            max_children=2,
            max_babies=1,
            bed_configuration=None,
            size_sqm=45.0,
            features=["Living Area", "Mini Bar", "City View"]
        ),

        # Sold out room (allocation = 0, no prices)
        RoomTypeAvailability(
            room_type_code="STANDARD",
            room_type_name="Standard Room",
            room_type_name_local="חדר סטנדרטי",
            inventory=Inventory(allocation=0, max_available=8),
            prices=None,  # No prices when sold out
            max_adults=2,
            max_children=0,
            max_babies=0,
            bed_configuration=None,
            size_sqm=None,
            features=None
        )
    ]
)
```

#### Practical Usage Example

```python
from datetime import date, timedelta

# Make API call
check_in = date(2025, 11, 14)
check_out = date(2025, 11, 16)
response = client.get_availability(
    check_in=check_in,
    check_out=check_out,
    adults=2,
    rate_code="WEB"
)

# Basic information
print(f"Hotel: {response.hotel_name}")
print(f"Currency: {response.currency}")
print(f"Stay: {response.check_in} to {response.check_out}")
nights = (response.check_out - response.check_in).days
print(f"Nights: {nights}")
print()

# Filter only available rooms (allocation > 0)
available_rooms = response.get_available_rooms()
print(f"Available room types: {len(available_rooms)}")
print()

# Iterate through available options
for room_type in available_rooms:
    print(f"{'=' * 60}")
    print(f"{room_type.room_type_name} ({room_type.room_type_code})")
    print(f"{'=' * 60}")

    # Availability info
    if room_type.inventory:
        print(f"Available: {room_type.inventory.allocation} / {room_type.inventory.max_available} rooms")
        print(f"Status: {'✓ Available' if room_type.inventory.is_available else '✗ Sold Out'}")

    # Price information
    if room_type.prices:
        min_price = room_type.get_min_price()
        print(f"\nStarting from: {response.currency} {min_price:.2f} (total for {nights} nights)")
        print(f"Per night: {response.currency} {min_price / nights:.2f}")

        print(f"\nMeal plan options:")
        for price in room_type.prices:
            print(f"  • {price.board_description}: {response.currency} {price.price:.2f}")
            if price.price_non_refundable:
                savings = price.price - price.price_non_refundable
                print(f"    Non-refundable: {response.currency} {price.price_non_refundable:.2f} (save {response.currency} {savings:.2f})")

    # Enhanced room specifications (if available)
    if room_type.max_adults:
        total = room_type.get_max_occupancy()
        print(f"\nMax occupancy: {total} guests")
        print(f"  ({room_type.max_adults} adults + {room_type.max_children} children + {room_type.max_babies} babies)")

    if room_type.bed_configuration:
        print(f"Bed configuration: {room_type.bed_configuration}")

    if room_type.size_sqm:
        print(f"Room size: {room_type.size_sqm} sqm")

    if room_type.features:
        print(f"Features: {', '.join(room_type.features)}")

    print()
```

**Output:**
```
Hotel: WayInn Hotel
Currency: ILS
Stay: 2025-11-14 to 2025-11-16
Nights: 2

Available room types: 2

============================================================
Deluxe King Room (DELUXE-KING)
============================================================
Available: 3 / 5 rooms
Status: ✓ Available

Starting from: ILS 420.00 (total for 2 nights)
Per night: ILS 210.00

Meal plan options:
  • Bed & Breakfast: ILS 420.00
    Non-refundable: ILS 380.00 (save ILS 40.00)
  • Half Board: ILS 520.00

Max occupancy: 3 guests
  (2 adults + 1 children + 0 babies)
Bed configuration: 1 King
Features: Ocean View, Balcony

============================================================
Executive Suite (SUITE)
============================================================
Available: 1 / 2 rooms
Status: ✓ Available

Starting from: ILS 650.00 (total for 2 nights)
Per night: ILS 325.00

Meal plan options:
  • Bed & Breakfast: ILS 650.00
  • Full Board: ILS 850.00

Max occupancy: 5 guests
  (2 adults + 2 children + 1 babies)
Room size: 45.0 sqm
Features: Living Area, Mini Bar, City View
```

---

### Example 2: Room Types Response

#### Python Object

```python
room_types = client.get_room_types()
# Returns:
[
    RoomType(
        code="DBL",
        description="Double Room",
        image_url="https://hotel.com/images/double.jpg"
    ),
    RoomType(
        code="SUITE",
        description="Executive Suite",
        image_url="https://hotel.com/images/suite.jpg"
    ),
    RoomType(
        code="FAMILY",
        description="Family Room",
        image_url=None  # No image available
    )
]
```

#### Usage

```python
room_types = client.get_room_types()

print("Available room types:")
for rt in room_types:
    print(f"  • {rt.code}: {rt.description}")
    if rt.image_url:
        print(f"    Image: {rt.image_url}")
```

**Output:**
```
Available room types:
  • DBL: Double Room
    Image: https://hotel.com/images/double.jpg
  • SUITE: Executive Suite
    Image: https://hotel.com/images/suite.jpg
  • FAMILY: Family Room
```

---

### Example 3: Rooms Response

#### Python Object

```python
rooms = client.get_rooms()
# Returns:
[
    Room(
        room_number="101",
        room_type="DBL",
        serial="R001",
        status="C",  # Clean
        wing="A",
        color="blue",
        is_dorm=False,
        is_bed=False,
        occupancy_limits=[
            GuestOccupancy(guest_type="A", max_count=2),  # Max 2 adults
            GuestOccupancy(guest_type="C", max_count=1),  # Max 1 child
            GuestOccupancy(guest_type="B", max_count=0)   # No babies
        ],
        attributes=[
            RoomAttribute(code="OV", description="Ocean View"),
            RoomAttribute(code="BAL", description="Balcony")
        ],
        image_url="https://hotel.com/images/room101.jpg"
    ),
    Room(
        room_number="201",
        room_type="SUITE",
        serial="R045",
        status="C",
        wing="B",
        color="gold",
        is_dorm=False,
        is_bed=False,
        occupancy_limits=[
            GuestOccupancy(guest_type="A", max_count=2),
            GuestOccupancy(guest_type="C", max_count=2),
            GuestOccupancy(guest_type="B", max_count=1)
        ],
        attributes=[
            RoomAttribute(code="LIV", description="Living Area"),
            RoomAttribute(code="MB", description="Mini Bar"),
            RoomAttribute(code="CV", description="City View")
        ],
        image_url="https://hotel.com/images/room201.jpg"
    )
]
```

#### Usage

```python
rooms = client.get_rooms()

for room in rooms:
    print(f"\nRoom {room.room_number} ({room.room_type})")
    print(f"  Status: {room.status}")
    print(f"  Wing: {room.wing}")

    if room.occupancy_limits:
        print(f"  Occupancy:")
        for occ in room.occupancy_limits:
            guest_label = {"A": "Adults", "C": "Children", "B": "Babies"}
            print(f"    • Max {occ.max_count} {guest_label.get(occ.guest_type, 'guests')}")

    if room.attributes:
        features = [attr.description for attr in room.attributes]
        print(f"  Features: {', '.join(features)}")
```

**Output:**
```
Room 101 (DBL)
  Status: C
  Wing: A
  Occupancy:
    • Max 2 Adults
    • Max 1 Children
    • Max 0 Babies
  Features: Ocean View, Balcony

Room 201 (SUITE)
  Status: C
  Wing: B
  Occupancy:
    • Max 2 Adults
    • Max 2 Children
    • Max 1 Babies
  Features: Living Area, Mini Bar, City View
```

---

### Example 4: Booking Link Response

#### Python Object

```python
link = client.generate_booking_link(
    check_in=date(2025, 11, 14),
    check_out=date(2025, 11, 16),
    adults=2,
    children=1,
    room_type_code="DELUXE-KING",
    language="en",
    currency="USD"
)

# Returns string:
"https://api.minihotel.cloud/gds/?hotel=wayinn&checkin=2025-11-14&checkout=2025-11-16&adults=2&children=1&room=DELUXE-KING"
```

#### Usage

```python
# Generate booking link
link = client.generate_booking_link(
    check_in=date(2025, 11, 14),
    check_out=date(2025, 11, 16),
    adults=2,
    children=1,
    room_type_code="DELUXE-KING"
)

print(f"Book now: {link}")

# In AI agent conversation:
agent_response = f"""
Great! I found the perfect room for you.

Deluxe King Room
• Price: $420 for 2 nights
• Occupancy: Up to 3 guests
• Features: King bed, Ocean view, Balcony

Ready to book? Click here:
{link}
"""
```

---

### Important Response Characteristics

#### 1. **Prices are TOTAL for Stay, NOT Per-Night**

⚠️ **CRITICAL:** Prices returned in `BoardPrice.price` are the **total cost for the entire stay**, not per night!

```python
response = client.get_availability(
    check_in=date(2025, 11, 14),
    check_out=date(2025, 11, 16),  # 2 nights
    adults=2
)

for room in response.get_available_rooms():
    total_price = room.get_min_price()  # e.g., 420.00
    nights = (response.check_out - response.check_in).days
    per_night = total_price / nights

    print(f"{room.room_type_name}")
    print(f"  Total: ${total_price:.2f} for {nights} nights")
    print(f"  Per night: ${per_night:.2f}")
```

**Output:**
```
Deluxe King Room
  Total: $420.00 for 2 nights
  Per night: $210.00
```

#### 2. **Optional Fields Can Be None**

Many fields are optional and may be `None`:

```python
# Room types might be None if no availability
if response.room_types:
    for room_type in response.room_types:
        # Prices are None for sold-out rooms
        if room_type.prices:
            print(f"Starting from: ${room_type.get_min_price()}")
        else:
            print("Sold out")

        # Enhanced fields might not be available
        if room_type.features:
            print(f"Features: {', '.join(room_type.features)}")
        else:
            print("Features not available")
```

#### 3. **Bilingual Support**

MiniHotel provides English and local language names:

```python
for room_type in response.room_types:
    print(f"English: {room_type.room_type_name}")
    if room_type.room_type_name_local:
        print(f"Local: {room_type.room_type_name_local}")
```

**Output:**
```
English: Deluxe King Room
Local: חדר דלוקס קינג
```

#### 4. **Helper Methods**

Response objects have convenient helper methods:

```python
# Get only available rooms (allocation > 0)
available = response.get_available_rooms()

# Get cheapest meal plan for a room
min_price = room_type.get_min_price()

# Calculate total capacity
total_guests = room_type.get_max_occupancy()  # adults + children + babies

# Check if room is available
is_available = room_type.inventory.is_available  # True if allocation > 0
```

#### 5. **Enhanced Fields Require Cache**

Enhanced fields (`max_adults`, `features`, `bed_configuration`, etc.) are only available if room specs cache is built:

```python
# In sandbox mode, build cache first
client.build_room_specs_cache()

# Now availability responses include enhanced fields
response = client.get_availability(check_in, check_out, adults=2)

for room_type in response.get_available_rooms():
    if room_type.max_adults:  # Only available if cache was built
        print(f"Max occupancy: {room_type.get_max_occupancy()} guests")
    if room_type.features:
        print(f"Features: {', '.join(room_type.features)}")
```

---

### AI Agent Response Formatting

Here's how an AI agent might format responses for natural conversation:

```python
def format_availability_for_guest(response: AvailabilityResponse) -> str:
    """Format availability response for guest conversation"""

    nights = (response.check_out - response.check_in).days
    available = response.get_available_rooms()

    if not available:
        return f"I'm sorry, we don't have any rooms available for {response.check_in} to {response.check_out}."

    message = f"Great news! We have {len(available)} room type(s) available for {nights} night(s):\n\n"

    for i, room in enumerate(available, 1):
        message += f"{i}. **{room.room_type_name}**\n"

        # Price
        min_price = room.get_min_price()
        if min_price:
            per_night = min_price / nights
            message += f"   💰 From {response.currency} {min_price:.2f} total ({per_night:.2f}/night)\n"

        # Availability
        if room.inventory:
            if room.inventory.allocation == 1:
                message += f"   ⚠️  Only 1 room left!\n"
            else:
                message += f"   ✓ {room.inventory.allocation} rooms available\n"

        # Occupancy
        if room.max_adults:
            message += f"   👥 Fits up to {room.get_max_occupancy()} guests\n"

        # Features
        if room.features:
            message += f"   ✨ {', '.join(room.features[:3])}\n"  # Show first 3 features

        # Meal options
        if room.prices and len(room.prices) > 1:
            message += f"   🍽️  {len(room.prices)} meal plan options\n"

        message += "\n"

    return message

# Usage in agent
response = client.get_availability(check_in, check_out, adults=2)
guest_message = format_availability_for_guest(response)
print(guest_message)
```

**Output:**
```
Great news! We have 2 room type(s) available for 2 night(s):

1. **Deluxe King Room**
   💰 From ILS 420.00 total (210.00/night)
   ✓ 3 rooms available
   👥 Fits up to 3 guests
   ✨ Ocean View, Balcony, King Bed
   🍽️  2 meal plan options

2. **Executive Suite**
   💰 From ILS 650.00 total (325.00/night)
   ⚠️  Only 1 room left!
   👥 Fits up to 5 guests
   ✨ Living Area, Mini Bar, City View
   🍽️  2 meal plan options
```

---

## Error Handling

All PMS implementations should raise these standard exceptions:

### Exception Types

1. **`PMSConnectionError`**
   - Cannot connect to PMS API
   - Network timeouts
   - HTTP errors

2. **`PMSAuthenticationError`**
   - Invalid credentials
   - Expired authentication tokens
   - Authorization failures

3. **`PMSValidationError`**
   - Invalid parameters provided
   - Date validation failures
   - Guest count validation failures

4. **`PMSDataError`**
   - Invalid response from PMS
   - XML/JSON parsing errors
   - Missing required fields in response

### Example Error Handling

```python
from src.pms.exceptions import (
    PMSConnectionError,
    PMSAuthenticationError,
    PMSValidationError,
    PMSDataError
)

try:
    response = client.get_availability(
        check_in=check_in,
        check_out=check_out,
        adults=2
    )
except PMSValidationError as e:
    print(f"Invalid request: {e}")
except PMSAuthenticationError as e:
    print(f"Authentication failed: {e}")
except PMSConnectionError as e:
    print(f"Connection error: {e}")
except PMSDataError as e:
    print(f"Data error: {e}")
```

---

## Implementation Example

Here's how to implement the PMS abstraction for a new PMS system:

```python
from src.pms.base import PMSClient, PMSClientFactory
from src.models.room import RoomType, Room
from src.models.availability import AvailabilityResponse
from datetime import date
from typing import List, Optional

class MyPMSClient(PMSClient):
    """Custom PMS implementation"""

    def __init__(self, username: str, password: str, hotel_id: str, cache_ttl_seconds: int = 300):
        super().__init__(username, password, hotel_id, cache_ttl_seconds)
        # Add PMS-specific initialization

    @property
    def supports_guest_count(self) -> bool:
        return True  # This PMS supports guest count filtering

    @property
    def supports_children_breakdown(self) -> bool:
        return True  # This PMS distinguishes children and babies

    def get_room_types(self) -> List[RoomType]:
        # Implement API call to fetch room types
        # Parse response and return List[RoomType]
        pass

    def get_rooms(self, room_number: Optional[str] = None) -> List[Room]:
        # Implement API call to fetch rooms
        # Parse response and return List[Room]
        pass

    def get_availability(
        self,
        check_in: date,
        check_out: date,
        adults: int,
        children: int = 0,
        babies: int = 0,
        rate_code: str = "USD",
        room_type_filter: str = "*ALL*",
        board_filter: str = "*ALL*"
    ) -> AvailabilityResponse:
        # Validate dates
        self.validate_dates(check_in, check_out)

        # Check cache (automatic in base class if implemented)
        cache_key = self._get_cache_key(
            check_in, check_out, adults, children, babies,
            rate_code, room_type_filter, board_filter
        )

        if cache_key in self._availability_cache:
            cache_timestamp, cached_response = self._availability_cache[cache_key]
            if self._is_cache_valid(cache_timestamp):
                return cached_response

        # Implement API call to fetch availability
        # Parse response and create AvailabilityResponse
        response = AvailabilityResponse(...)

        # Store in cache
        from time import time
        self._availability_cache[cache_key] = (time(), response)

        return response

    def generate_booking_link(
        self,
        check_in: date,
        check_out: date,
        adults: int,
        children: int = 0,
        babies: int = 0,
        room_type_code: Optional[str] = None,
        rate_code: Optional[str] = None,
        board_code: Optional[str] = None,
        **kwargs
    ) -> str:
        # Validate dates
        self.validate_dates(check_in, check_out)

        # Build booking URL with parameters
        # Return complete URL
        pass

# Register with factory
PMSClientFactory.register("mypms", MyPMSClient)
```

---

## Data Models Reference

### RoomType
```python
@dataclass
class RoomType:
    code: str                      # Room type code
    description: str                # Display name
    image_url: Optional[str] = None # Image URL
```

### Room
```python
@dataclass
class Room:
    room_number: str                              # Physical room number
    room_type: str                                 # Room type code
    serial: Optional[str] = None                   # Serial number
    status: Optional[str] = None                   # Cleaning status
    wing: Optional[str] = None                     # Building wing
    color: Optional[str] = None                    # Color code
    is_dorm: bool = False                          # Is dormitory
    is_bed: bool = False                           # Is single bed
    occupancy_limits: Optional[List[GuestOccupancy]] = None  # Max guests by type
    attributes: Optional[List[RoomAttribute]] = None         # Features
    image_url: Optional[str] = None                # Image URL
```

### AvailabilityResponse
```python
@dataclass
class AvailabilityResponse:
    hotel_id: str
    hotel_name: str
    currency: str
    check_in: date
    check_out: date
    adults: int
    children: int = 0
    babies: int = 0
    room_types: Optional[List[RoomTypeAvailability]] = None

    # Helper methods
    def get_available_rooms(self) -> List[RoomTypeAvailability]
```

### RoomTypeAvailability
```python
@dataclass
class RoomTypeAvailability:
    room_type_code: str
    room_type_name: str
    room_type_name_local: Optional[str] = None
    inventory: Optional[Inventory] = None
    prices: Optional[List[BoardPrice]] = None
    # Enhanced fields (optional)
    max_adults: Optional[int] = None
    max_children: Optional[int] = None
    max_babies: Optional[int] = None
    bed_configuration: Optional[str] = None
    size_sqm: Optional[float] = None
    features: Optional[List[str]] = None

    # Helper methods
    def get_min_price(self) -> Optional[float]
    def get_max_occupancy(self) -> Optional[int]
```

---

## Best Practices

1. **Caching Strategy**
   - **Automatic caching:** `get_availability()` now caches responses automatically (default TTL: 5 minutes)
   - Cache static data: `get_room_types()`, `get_rooms()` (implementation-specific)
   - Configure cache TTL via constructor: `cache_ttl_seconds` parameter
   - Cache key includes all query parameters (dates, guests, rate code, filters)
   - Use `clear_availability_cache()` only when you need to force fresh data
   - Benefits: Reduced API load, faster responses, better user experience for repeated queries

2. **Error Handling**
   - Always raise specific exception types
   - Include helpful error messages
   - Log errors for debugging

3. **Date Handling**
   - Always use Python `date` objects (not strings or datetime)
   - Call `validate_dates()` before API calls
   - Handle timezone conversions within PMS implementation

4. **Guest Counts**
   - Check `supports_guest_count` before filtering by guests
   - Check `supports_children_breakdown` before separating children/babies
   - Validate at least 1 adult is present

5. **Pricing**
   - **Never** generate or hallucinate prices
   - Always return actual prices from PMS API
   - Document if prices are per-night or total stay
   - Include currency information

6. **Testing**
   - Test all abstract methods
   - Test error conditions
   - Test with real API in sandbox mode
   - Create conversation-based test scenarios

