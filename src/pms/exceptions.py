"""PMS-related exceptions"""


class PMSException(Exception):
    """Base exception for all PMS-related errors"""
    pass


class PMSConnectionError(PMSException):
    """Raised when unable to connect to the PMS"""
    pass


class PMSAuthenticationError(PMSException):
    """Raised when authentication fails"""
    pass


class PMSValidationError(PMSException):
    """Raised when request parameters are invalid"""
    pass


class PMSDataError(PMSException):
    """Raised when PMS returns invalid or unexpected data"""
    pass
