"""Availability and pricing data models"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import date


@dataclass
class BoardPrice:
    """Price for a specific board/meal arrangement"""
    board_code: str
    board_description: str
    price: float
    price_non_refundable: Optional[float] = None

    def __str__(self) -> str:
        return f"{self.board_description}: ${self.price:.2f}"


@dataclass
class Inventory:
    """Room availability inventory"""
    allocation: int  # Number of available rooms
    max_available: int  # Total number of rooms

    @property
    def is_available(self) -> bool:
        return self.allocation > 0


@dataclass
class RoomTypeAvailability:
    """Availability and pricing for a specific room type"""
    room_type_code: str
    room_type_name: str
    room_type_name_local: Optional[str] = None
    inventory: Optional[Inventory] = None
    prices: Optional[List[BoardPrice]] = None
    # Room specifications (optional - depends on PMS capabilities)
    max_adults: Optional[int] = None
    max_children: Optional[int] = None
    max_babies: Optional[int] = None
    bed_configuration: Optional[str] = None  # e.g., "1 King", "2 Queens"
    size_sqm: Optional[float] = None
    features: Optional[List[str]] = None  # e.g., ["Ocean View", "Balcony", "Connecting"]

    def __str__(self) -> str:
        avail_str = f"{self.inventory.allocation} available" if self.inventory else "unknown"
        return f"{self.room_type_name} ({self.room_type_code}) - {avail_str}"

    def get_min_price(self) -> Optional[float]:
        """Get the minimum price across all board types"""
        if not self.prices:
            return None
        return min(p.price for p in self.prices)

    def get_max_occupancy(self) -> Optional[int]:
        """Get total maximum occupancy (adults + children + babies)"""
        if self.max_adults is None:
            return None
        total = self.max_adults
        if self.max_children:
            total += self.max_children
        if self.max_babies:
            total += self.max_babies
        return total


@dataclass
class AvailabilityResponse:
    """Complete availability response for a date range"""
    hotel_id: str
    hotel_name: str
    currency: str
    check_in: date
    check_out: date
    adults: int
    children: int = 0
    babies: int = 0
    room_types: Optional[List[RoomTypeAvailability]] = None

    def __str__(self) -> str:
        nights = (self.check_out - self.check_in).days
        return f"{self.hotel_name} ({self.check_in} to {self.check_out}, {nights} nights)"

    def get_available_rooms(self) -> List[RoomTypeAvailability]:
        """Get only room types that have availability"""
        if not self.room_types:
            return []
        return [rt for rt in self.room_types if rt.inventory and rt.inventory.is_available]
