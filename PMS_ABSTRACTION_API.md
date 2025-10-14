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

