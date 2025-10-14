"""PMS (Property Management System) Abstraction Layer"""
from .base import PMSClient, PMSClientFactory
from .minihotel import MiniHotelClient
from .ezgo import EzGoClient
from .exceptions import (
    PMSException,
    PMSConnectionError,
    PMSAuthenticationError,
    PMSValidationError,
    PMSDataError,
)

# Register PMS implementations
PMSClientFactory.register("minihotel", MiniHotelClient)
PMSClientFactory.register("ezgo", EzGoClient)

__all__ = [
    "PMSClient",
    "PMSClientFactory",
    "MiniHotelClient",
    "EzGoClient",
    "PMSException",
    "PMSConnectionError",
    "PMSAuthenticationError",
    "PMSValidationError",
    "PMSDataError",
]
