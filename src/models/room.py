"""Room-related data models"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class RoomType:
    """Represents a room type in the PMS"""
    code: str
    description: str
    image_url: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.code}: {self.description}"


@dataclass
class GuestOccupancy:
    """Guest occupancy limits for a room"""
    guest_type: str  # A=Adult, C=Child, B=Baby
    max_count: int


@dataclass
class RoomAttribute:
    """Room attribute (e.g., Garden view, Sea view)"""
    code: str
    description: str


@dataclass
class Room:
    """Represents a physical room in the hotel"""
    room_number: str
    room_type: str
    serial: Optional[str] = None
    status: Optional[str] = None  # C=Clean, D=Dirty
    wing: Optional[str] = None
    color: Optional[str] = None
    is_dorm: bool = False
    is_bed: bool = False
    occupancy_limits: Optional[List[GuestOccupancy]] = None
    attributes: Optional[List[RoomAttribute]] = None
    image_url: Optional[str] = None

    def __str__(self) -> str:
        return f"Room {self.room_number} ({self.room_type})"
