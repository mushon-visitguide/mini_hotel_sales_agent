"""Data Models for PMS Responses"""
from .room import RoomType, Room, GuestOccupancy, RoomAttribute
from .availability import (
    BoardPrice,
    Inventory,
    RoomTypeAvailability,
    AvailabilityResponse,
)

__all__ = [
    "RoomType",
    "Room",
    "GuestOccupancy",
    "RoomAttribute",
    "BoardPrice",
    "Inventory",
    "RoomTypeAvailability",
    "AvailabilityResponse",
]
