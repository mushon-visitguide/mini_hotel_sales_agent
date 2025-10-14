# Hotel Sales AI Agent - Source Code

This directory contains the core implementation of the Hotel Sales AI Agent.

## Structure

```
src/
├── models/          # Data models for PMS responses
│   ├── room.py           # Room-related models (RoomType, Room, etc.)
│   └── availability.py   # Availability and pricing models
├── pms/             # PMS abstraction layer
│   ├── base.py           # Abstract PMSClient base class
│   ├── exceptions.py     # PMS-specific exceptions
│   └── minihotel.py      # MiniHotel implementation
└── tests/           # Test files
    └── test_minihotel.py # MiniHotel integration tests
```

## PMS Abstraction Layer

### Design Principles

The PMS layer is designed to be **PMS-agnostic**, allowing easy integration with any Property Management System:

1. **Abstract Base Class**: `PMSClient` defines the interface all PMS implementations must follow
2. **Factory Pattern**: `PMSClientFactory` allows creating clients by name (e.g., "minihotel")
3. **Capability Flags**: Each PMS declares its capabilities (e.g., `supports_guest_count`)
4. **Data Models**: Standardized data structures ensure consistency across PMS systems

### Key Concepts

Different PMS systems have different capabilities:

- **MiniHotel**: Supports detailed guest count filtering (adults, children, babies)
- **ezGo** (future): May only support number of rooms, not guest counts
- **Other systems**: Each will have their own features and limitations

The abstraction layer handles these differences gracefully by:
- Using capability flags (`supports_guest_count`, `supports_children_breakdown`)
- Providing standard data models that work across all systems
- Allowing PMS-specific parameters while maintaining a consistent interface

## Data Models

### Room Models (`models/room.py`)

- **RoomType**: Basic room type information (code, description, image)
- **Room**: Physical room details with occupancy limits and attributes
- **GuestOccupancy**: Guest capacity by type (adult, child, baby)
- **RoomAttribute**: Room features (e.g., "Sea view", "Garden view")

### Availability Models (`models/availability.py`)

- **AvailabilityResponse**: Complete availability for a date range
- **RoomTypeAvailability**: Availability for a specific room type
- **Inventory**: Room availability counts (allocated vs max)
- **BoardPrice**: Pricing for meal arrangements (BB, HB, FB, RO)

## Usage Examples

### Create a PMS Client

```python
from src.pms import PMSClientFactory

# Using factory (recommended)
client = PMSClientFactory.create(
    "minihotel",
    username="your_username",
    password="your_password",
    hotel_id="your_hotel_id"
)

# Or directly
from src.pms import MiniHotelClient
client = MiniHotelClient(username, password, hotel_id)
```

### Get Availability

```python
from datetime import date, timedelta

# Get availability for next month
check_in = date.today() + timedelta(days=30)
check_out = check_in + timedelta(days=2)

response = client.get_availability(
    check_in=check_in,
    check_out=check_out,
    adults=2,
    children=1,
    babies=0,
    rate_code="WEB",  # PMS-specific rate code
)

# Examine results
print(f"Hotel: {response.hotel_name}")
print(f"Currency: {response.currency}")

for room_type in response.get_available_rooms():
    print(f"\n{room_type.room_type_name}")
    print(f"  Available: {room_type.inventory.allocation}")

    min_price = room_type.get_min_price()
    if min_price:
        print(f"  Starting at: {response.currency} {min_price:.2f}")

    if room_type.prices:
        for price in room_type.prices:
            print(f"    {price.board_description}: {price.price:.2f}")
```

### Check PMS Capabilities

```python
# Check what the PMS supports
if client.supports_guest_count:
    print("This PMS supports filtering by guest count")
    # Ask user for adults, children, babies
else:
    print("This PMS only supports number of rooms")
    # Only ask for number of rooms needed

if client.supports_children_breakdown:
    # Separate fields for children and babies
    pass
else:
    # Combined field for all non-adults
    pass
```

## MiniHotel-Specific Notes

### Endpoints

- **Production**: `https://api.minihotel.cloud/gds`
- **Sandbox**: `https://sandbox.minihotel.cloud/agents/ws/settings/rooms/RoomsMain.asmx`

### Production vs Sandbox

Some MiniHotel functions are **sandbox-only**:
- `get_room_types()` - only works in sandbox
- `get_rooms()` - only works in sandbox

For production, extract room type information from `get_availability()` responses.

### Rate Codes

Rate codes are PMS-specific and determine currency:
- Common examples: "USD", "EUR", "WEB", "STD"
- Must be configured in the hotel's PMS settings

### Board Codes

Board/meal arrangement codes:
- `BB` - Bed & Breakfast
- `HB` - Half Board
- `FB` - Full Board
- `RO` - Room Only
- Use `*ALL*` to get all available options
- Use `*MIN*` to get the cheapest option

## Running Tests

```bash
# Run all tests
python3 -m src.tests.test_minihotel

# Or with pytest (if installed)
pytest src/tests/
```

## Error Handling

The PMS layer uses specific exceptions:

- `PMSConnectionError`: Network or connection issues
- `PMSAuthenticationError`: Invalid credentials
- `PMSValidationError`: Invalid parameters (dates, guest counts)
- `PMSDataError`: Invalid or unexpected API response

```python
from src.pms.exceptions import PMSException, PMSAuthenticationError

try:
    response = client.get_availability(...)
except PMSAuthenticationError:
    print("Invalid credentials - check username/password")
except PMSException as e:
    print(f"PMS error: {e}")
```

## Next Steps

This basic API layer provides the foundation for:

1. **AI Agent Integration**: Use availability data in conversational flows
2. **Intent Detection**: Parse user requests and call appropriate PMS methods
3. **Booking Link Generation**: Use availability data to create booking URLs
4. **Additional PMS Systems**: Add more implementations following the same pattern
5. **Caching**: Cache static data (room types) to reduce API calls
6. **Rate Limiting**: Add request throttling for production use
