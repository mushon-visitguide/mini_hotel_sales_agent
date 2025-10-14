"""PMS (Property Management System) Abstraction Layer"""
from .base import PMSClient, PMSClientFactory
from .minihotel import MiniHotelClient
from .exceptions import (
    PMSException,
    PMSConnectionError,
    PMSAuthenticationError,
    PMSValidationError,
    PMSDataError,
)

# Register MiniHotel implementation
PMSClientFactory.register("minihotel", MiniHotelClient)

__all__ = [
    "PMSClient",
    "PMSClientFactory",
    "MiniHotelClient",
    "PMSException",
    "PMSConnectionError",
    "PMSAuthenticationError",
    "PMSValidationError",
    "PMSDataError",
]
