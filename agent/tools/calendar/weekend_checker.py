"""
Weekend checker tool - Determines if dates fall on weekends.

Supports different weekend definitions:
- Israeli weekend: Thursday evening through Saturday (Thu-Sat)
- Western weekend: Saturday-Sunday
- Custom weekend definitions
"""
from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, Field


class WeekendCheckResult(BaseModel):
    """Result of weekend check"""
    date: str = Field(description="Date that was checked in YYYY-MM-DD format")
    is_weekend: bool = Field(description="Whether the date is a weekend")
    day_name: str = Field(description="Name of the day (Monday, Tuesday, etc.)")
    day_of_week: int = Field(description="Day of week (0=Monday, 6=Sunday)")
    weekend_type: str = Field(description="Type of weekend definition used")


WeekendType = Literal["israeli", "western", "friday_saturday", "saturday_sunday"]


class WeekendChecker:
    """
    Checks if dates fall on weekends according to different cultural definitions.
    """

    def __init__(self, default_weekend_type: WeekendType = "israeli"):
        """
        Initialize weekend checker.

        Args:
            default_weekend_type: Default weekend definition to use
                - israeli: Thursday-Saturday (weekday 3, 4, 5)
                - western: Saturday-Sunday (weekday 5, 6)
                - friday_saturday: Friday-Saturday (weekday 4, 5)
                - saturday_sunday: Saturday-Sunday (weekday 5, 6) - same as western
        """
        self.default_weekend_type = default_weekend_type

    def is_weekend(
        self,
        check_date: str | date | datetime,
        weekend_type: Optional[WeekendType] = None
    ) -> bool:
        """
        Check if a date is a weekend.

        Args:
            check_date: Date to check (YYYY-MM-DD string, date, or datetime)
            weekend_type: Type of weekend to check against (uses default if not provided)

        Returns:
            True if the date is a weekend, False otherwise
        """
        # Parse date
        if isinstance(check_date, str):
            dt = datetime.strptime(check_date, '%Y-%m-%d')
        elif isinstance(check_date, datetime):
            dt = check_date
        elif isinstance(check_date, date):
            dt = datetime.combine(check_date, datetime.min.time())
        else:
            raise ValueError(f"Invalid date type: {type(check_date)}")

        # Use default weekend type if not specified
        wtype = weekend_type or self.default_weekend_type

        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = dt.weekday()

        # Check based on weekend type
        if wtype == "israeli":
            # Thursday (3), Friday (4), Saturday (5)
            return day_of_week in [3, 4, 5]
        elif wtype in ["western", "saturday_sunday"]:
            # Saturday (5), Sunday (6)
            return day_of_week in [5, 6]
        elif wtype == "friday_saturday":
            # Friday (4), Saturday (5)
            return day_of_week in [4, 5]
        else:
            raise ValueError(f"Unknown weekend type: {wtype}")

    async def check(
        self,
        check_date: str,
        weekend_type: Optional[WeekendType] = None
    ) -> WeekendCheckResult:
        """
        Check if a date is a weekend and return detailed information.

        Args:
            check_date: Date to check in YYYY-MM-DD format
            weekend_type: Type of weekend to check against (uses default if not provided)

        Returns:
            WeekendCheckResult with detailed information
        """
        # Parse date
        dt = datetime.strptime(check_date, '%Y-%m-%d')

        # Use default weekend type if not specified
        wtype = weekend_type or self.default_weekend_type

        # Check if weekend
        is_wknd = self.is_weekend(dt, wtype)

        # Get day information
        day_name = dt.strftime('%A')
        day_of_week = dt.weekday()

        return WeekendCheckResult(
            date=check_date,
            is_weekend=is_wknd,
            day_name=day_name,
            day_of_week=day_of_week,
            weekend_type=wtype
        )


# Singleton instance
_weekend_checker_instance = None


def get_weekend_checker() -> WeekendChecker:
    """Get or create singleton WeekendChecker instance"""
    global _weekend_checker_instance
    if _weekend_checker_instance is None:
        _weekend_checker_instance = WeekendChecker()
    return _weekend_checker_instance
