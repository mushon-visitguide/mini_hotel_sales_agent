"""Abstract base class for Property Management System integrations"""
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from ..models.room import RoomType, Room
from ..models.availability import AvailabilityResponse


class PMSClient(ABC):
    """
    Abstract base class for PMS (Property Management System) integrations.

    This class defines the interface that all PMS implementations must follow.
    Different PMS systems (MiniHotel, ezGo, etc.) will have their own capabilities
    and limitations, which should be documented in their specific implementations.
    """

    def __init__(self, username: str, password: str, hotel_id: str):
        """
        Initialize the PMS client.

        Args:
            username: Authentication username
            password: Authentication password
            hotel_id: Unique identifier for the hotel in the PMS
        """
        self.username = username
        self.password = password
        self.hotel_id = hotel_id

    @abstractmethod
    def get_room_types(self) -> List[RoomType]:
        """
        Retrieve all room types available in the hotel.

        This is typically static data that can be cached.

        Returns:
            List of RoomType objects

        Raises:
            PMSConnectionError: If unable to connect to PMS
            PMSAuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    def get_rooms(self, room_number: Optional[str] = None) -> List[Room]:
        """
        Retrieve room information including occupancy limits and attributes.

        This is typically static data that can be cached.

        Args:
            room_number: Optional room number to get specific room info.
                        If None, returns all rooms.

        Returns:
            List of Room objects

        Raises:
            PMSConnectionError: If unable to connect to PMS
            PMSAuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
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
        """
        Get real-time availability and pricing for specified dates and guests.

        This is dynamic data that must be fetched fresh each time.
        CRITICAL: Prices must come from the PMS API - never hallucinated.

        Args:
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            children: Number of children (default: 0)
            babies: Number of babies (default: 0)
            rate_code: Rate code (e.g., "USD", "EUR", "STD") - determines currency
            room_type_filter: "*ALL*", "*MIN*", or specific room type code
            board_filter: "*ALL*", "*MIN*", or specific board code (e.g., "BB", "HB")

        Returns:
            AvailabilityResponse with pricing and availability data

        Raises:
            PMSConnectionError: If unable to connect to PMS
            PMSAuthenticationError: If authentication fails
            PMSValidationError: If parameters are invalid

        Notes:
            - Different PMS systems may have different capabilities
            - Some systems may not support guest count filtering
            - Rate codes and board codes are PMS-specific
        """
        pass

    @property
    @abstractmethod
    def supports_guest_count(self) -> bool:
        """
        Indicates whether this PMS supports filtering by number of guests.

        Returns:
            True if the PMS can filter availability by guest count,
            False otherwise (agent should only ask for number of rooms)
        """
        pass

    @property
    @abstractmethod
    def supports_children_breakdown(self) -> bool:
        """
        Indicates whether this PMS distinguishes between children and babies.

        Returns:
            True if PMS tracks children and babies separately,
            False if it only tracks adults vs total guests
        """
        pass

    @abstractmethod
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
        """
        Generate a booking link for the hotel's booking system.

        This link should direct guests to the booking page with pre-filled
        parameters based on their requirements.

        Args:
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            children: Number of children (default: 0)
            babies: Number of babies (default: 0)
            room_type_code: Optional specific room type code
            rate_code: Optional rate code
            board_code: Optional board/meal plan code
            **kwargs: Additional PMS-specific parameters

        Returns:
            Complete booking URL as string

        Raises:
            PMSValidationError: If parameters are invalid
        """
        pass

    def validate_dates(self, check_in: date, check_out: date) -> None:
        """
        Validate that dates are logical.

        Args:
            check_in: Check-in date
            check_out: Check-out date

        Raises:
            PMSValidationError: If dates are invalid
        """
        from .exceptions import PMSValidationError

        if check_in >= check_out:
            raise PMSValidationError("Check-out date must be after check-in date")

        if check_in < date.today():
            raise PMSValidationError("Check-in date cannot be in the past")


class PMSClientFactory:
    """Factory for creating PMS client instances"""

    _clients = {}

    @classmethod
    def register(cls, pms_type: str, client_class):
        """Register a PMS client implementation"""
        cls._clients[pms_type.lower()] = client_class

    @classmethod
    def create(cls, pms_type: str, username: str, password: str, hotel_id: str) -> PMSClient:
        """
        Create a PMS client instance.

        Args:
            pms_type: Type of PMS (e.g., "minihotel", "ezgo")
            username: Authentication username
            password: Authentication password
            hotel_id: Hotel identifier

        Returns:
            PMSClient instance

        Raises:
            ValueError: If PMS type is not registered
        """
        client_class = cls._clients.get(pms_type.lower())
        if not client_class:
            available = ", ".join(cls._clients.keys())
            raise ValueError(
                f"Unknown PMS type: {pms_type}. Available types: {available}"
            )
        return client_class(username, password, hotel_id)
