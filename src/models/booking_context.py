"""Booking context model - tracks booking state across conversation"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import date


@dataclass
class BookingContext:
    """
    Tracks the current booking state across multi-turn conversation.

    This maintains all booking-related information extracted from the conversation,
    including dates, guests, room preferences, and guest contact information.
    """

    # Dates
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    nights: Optional[int] = None

    # Party composition
    adults: int = 2
    children: List[int] = field(default_factory=list)  # Ages of children
    babies: int = 0

    # Room preferences
    num_rooms: int = 1
    selected_room_code: Optional[str] = None
    room_preferences: List[str] = field(default_factory=list)  # e.g., ["king bed", "ocean view"]
    board_preference: Optional[str] = None  # e.g., "breakfast", "half board"
    budget_max_per_night: Optional[float] = None

    # Guest information
    guest_first_name: Optional[str] = None
    guest_last_name: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_email: Optional[str] = None

    # Additional context
    special_requests: List[str] = field(default_factory=list)

    def update_from_slots(self, slots: Dict[str, Any]) -> None:
        """
        Update booking context from extracted slots.
        Only updates fields that are present in slots and not None.

        Args:
            slots: Dictionary of extracted slots from planner
        """
        # Dates
        if slots.get("check_in"):
            if isinstance(slots["check_in"], str):
                self.check_in = date.fromisoformat(slots["check_in"])
            elif isinstance(slots["check_in"], date):
                self.check_in = slots["check_in"]

        if slots.get("check_out"):
            if isinstance(slots["check_out"], str):
                self.check_out = date.fromisoformat(slots["check_out"])
            elif isinstance(slots["check_out"], date):
                self.check_out = slots["check_out"]

        # Calculate nights if both dates present
        if self.check_in and self.check_out:
            self.nights = (self.check_out - self.check_in).days

        # Party composition
        if slots.get("adults") is not None:
            self.adults = slots["adults"]
        if slots.get("children") is not None:
            self.children = slots["children"]
        if slots.get("babies") is not None:
            self.babies = slots["babies"]

        # Preferences
        if slots.get("selected_room_code"):
            self.selected_room_code = slots["selected_room_code"]
        if slots.get("board_preference"):
            self.board_preference = slots["board_preference"]
        if slots.get("bed_preference") and slots["bed_preference"] not in self.room_preferences:
            self.room_preferences.append(slots["bed_preference"])

        # Guest info
        if slots.get("guest_first_name"):
            self.guest_first_name = slots["guest_first_name"]
        if slots.get("guest_last_name"):
            self.guest_last_name = slots["guest_last_name"]
        if slots.get("guest_name"):
            # Support old format: split into first/last name
            parts = slots["guest_name"].split(None, 1)
            if len(parts) >= 1 and not self.guest_first_name:
                self.guest_first_name = parts[0]
            if len(parts) >= 2 and not self.guest_last_name:
                self.guest_last_name = parts[1]
        if slots.get("guest_phone"):
            self.guest_phone = slots["guest_phone"]
        if slots.get("guest_email"):
            self.guest_email = slots["guest_email"]

    def has_dates(self) -> bool:
        """Check if booking has check-in and check-out dates"""
        return self.check_in is not None and self.check_out is not None

    def has_guest_info(self) -> bool:
        """Check if we have complete guest contact information"""
        return (
            self.guest_first_name is not None and
            self.guest_last_name is not None and
            (self.guest_phone is not None or self.guest_email is not None)
        )

    def is_ready_for_booking(self) -> bool:
        """Check if we have all required information for booking"""
        return (
            self.has_dates() and
            self.selected_room_code is not None and
            self.has_guest_info()
        )

    def missing_info(self) -> List[str]:
        """Return list of missing required information"""
        missing = []

        if not self.has_dates():
            missing.append("dates")
        if self.selected_room_code is None:
            missing.append("room selection")
        if self.guest_first_name is None:
            missing.append("guest first name")
        if self.guest_last_name is None:
            missing.append("guest last name")
        if self.guest_phone is None and self.guest_email is None:
            missing.append("contact info (phone or email)")

        return missing

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert date objects to strings
        if self.check_in:
            data["check_in"] = self.check_in.isoformat()
        if self.check_out:
            data["check_out"] = self.check_out.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BookingContext":
        """Create BookingContext from dictionary"""
        # Convert date strings to date objects
        if data.get("check_in") and isinstance(data["check_in"], str):
            data["check_in"] = date.fromisoformat(data["check_in"])
        if data.get("check_out") and isinstance(data["check_out"], str):
            data["check_out"] = date.fromisoformat(data["check_out"])

        return cls(**data)

    def __str__(self) -> str:
        """Human-readable representation"""
        parts = []

        if self.has_dates():
            parts.append(f"{self.check_in} to {self.check_out} ({self.nights} nights)")

        guest_info = []
        if self.adults > 0:
            guest_info.append(f"{self.adults} adults")
        if self.children:
            guest_info.append(f"{len(self.children)} children (ages {', '.join(map(str, self.children))})")
        if self.babies > 0:
            guest_info.append(f"{self.babies} babies")

        if guest_info:
            parts.append(", ".join(guest_info))

        if self.num_rooms > 1:
            parts.append(f"{self.num_rooms} rooms")

        if self.selected_room_code:
            parts.append(f"Room: {self.selected_room_code}")

        if self.guest_first_name or self.guest_last_name:
            name_parts = [self.guest_first_name or "", self.guest_last_name or ""]
            guest_name = " ".join(p for p in name_parts if p)
            parts.append(f"Guest: {guest_name}")

        return " | ".join(parts) if parts else "No booking info"
