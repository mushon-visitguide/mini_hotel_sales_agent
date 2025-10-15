"""Calendar tools registration for the agent tool registry"""
from typing import Optional
from agent.tools.registry import registry
from .date_resolver import get_resolver
from .holiday_resolver import get_holiday_resolver
from .weekend_checker import get_weekend_checker


@registry.tool(
    name="calendar.resolve_date_hint",
    description="Resolve fuzzy date hints like 'next weekend', 'first of October', 'tomorrow' to concrete dates"
)
async def resolve_date_hint(
    date_hint: str,
    current_date: Optional[str] = None,
    timezone: str = "Asia/Jerusalem",
    default_nights: int = 1
) -> dict:
    """
    Resolve fuzzy date hint to concrete dates.

    Args:
        date_hint: Natural language date (e.g., "next weekend", "Oct 1st", "tomorrow")
        current_date: Current date YYYY-MM-DD (defaults to today)
        timezone: Timezone for interpretation (default: Asia/Jerusalem)
        default_nights: Default stay length (default: 1 night)

    Returns:
        {
            "check_in": "YYYY-MM-DD",
            "check_out": "YYYY-MM-DD",
            "nights": int,
            "days": int,
            "reasoning": str
        }
    """
    resolver = get_resolver()
    result = await resolver.resolve(
        date_hint=date_hint,
        current_date=current_date,
        timezone=timezone,
        default_nights=default_nights
    )
    return result.dict()


@registry.tool(
    name="calendar.resolve_holiday",
    description="Resolve holiday names (Jewish, Christian) to date ranges. Examples: 'Hanukkah', 'Christmas', 'Passover', 'Easter'"
)
async def resolve_holiday(
    holiday_name: str,
    year: Optional[int] = None
) -> dict:
    """
    Resolve holiday name to date range.

    Automatically returns the NEXT occurrence if the holiday has already passed.

    Supports:
    - Jewish holidays: Hanukkah, Passover, Rosh Hashanah, Yom Kippur, Purim, Sukkot, etc.
    - Christian holidays: Christmas, Easter, Good Friday, Thanksgiving, etc.

    Args:
        holiday_name: Name of the holiday (e.g., "Hanukkah", "Christmas", "Passover")
        year: Year to resolve for (defaults to current year, auto-advances if date passed)

    Returns:
        {
            "holiday_name": str,
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "duration_days": int,
            "year": int,
            "holiday_type": str  # "jewish", "christian", or "muslim"
        }
        or {"error": "Holiday not found"} if holiday is not recognized
    """
    from datetime import datetime, date

    resolver = get_holiday_resolver()

    # If no year specified, start with current year
    if year is None:
        year = datetime.now().year

    # Try to get the holiday for the specified year
    result = await resolver.resolve(holiday_name=holiday_name, year=year)

    if result is None:
        return {"error": f"Holiday '{holiday_name}' not found for year {year}"}

    # Check if the holiday end date has already passed
    today = date.today()
    holiday_end = datetime.strptime(result.end_date, "%Y-%m-%d").date()

    # If holiday has passed, get next year's date
    if holiday_end < today:
        next_year_result = await resolver.resolve(holiday_name=holiday_name, year=year + 1)
        if next_year_result:
            # Double-check the next year's date hasn't also passed (edge case)
            next_holiday_end = datetime.strptime(next_year_result.end_date, "%Y-%m-%d").date()
            if next_holiday_end >= today:
                return next_year_result.dict()

    return result.dict()


@registry.tool(
    name="calendar.check_is_weekend",
    description="Check if a specific date falls on a weekend (Israeli: Thu-Sat or Western: Sat-Sun)"
)
async def check_is_weekend(
    date: str,
    weekend_type: Optional[str] = "israeli"
) -> dict:
    """
    Check if a date is a weekend.

    Args:
        date: Date to check in YYYY-MM-DD format
        weekend_type: Type of weekend definition:
            - "israeli": Thursday-Saturday (default)
            - "western": Saturday-Sunday
            - "friday_saturday": Friday-Saturday
            - "saturday_sunday": Same as western

    Returns:
        {
            "date": "YYYY-MM-DD",
            "is_weekend": bool,
            "day_name": str,  # "Monday", "Tuesday", etc.
            "day_of_week": int,  # 0=Monday, 6=Sunday
            "weekend_type": str
        }
    """
    checker = get_weekend_checker()
    result = await checker.check(check_date=date, weekend_type=weekend_type)
    return result.dict()


@registry.tool(
    name="calendar.resolve_date_with_context",
    description="Enhanced date resolution that handles fuzzy dates, holidays, and weekend detection in one call"
)
async def resolve_date_with_context(
    user_input: str,
    current_date: Optional[str] = None,
    timezone: str = "Asia/Jerusalem",
    default_nights: int = 1,
    check_holiday: bool = True,
    weekend_type: str = "israeli"
) -> dict:
    """
    Resolve dates with full context including holidays and weekend detection.

    This tool combines multiple calendar operations:
    1. Tries to detect if user mentions a holiday (e.g., "2 nights in Hanukkah")
    2. Falls back to fuzzy date resolution (e.g., "next weekend")
    3. Checks if resolved dates fall on weekends

    Args:
        user_input: Natural language date input (e.g., "2 nights in Hanukkah", "next weekend", "2 of Aug")
        current_date: Current date YYYY-MM-DD (defaults to today)
        timezone: Timezone for interpretation (default: Asia/Jerusalem)
        default_nights: Default stay length (default: 1 night)
        check_holiday: Whether to check for holiday mentions (default: True)
        weekend_type: Weekend definition to use (default: "israeli")

    Returns:
        {
            "check_in": "YYYY-MM-DD",
            "check_out": "YYYY-MM-DD",
            "nights": int,
            "reasoning": str,
            "is_holiday": bool,
            "holiday_info": {...} or null,
            "is_weekend": bool,
            "weekend_info": {...}
        }
    """
    from datetime import datetime

    result = {
        "is_holiday": False,
        "holiday_info": None,
        "is_weekend": False,
        "weekend_info": None
    }

    # Always use date resolver to handle duration properly
    # The date resolver can handle holidays AND respect user's duration requests
    date_resolver = get_resolver()
    date_result = await date_resolver.resolve(
        date_hint=user_input,
        current_date=current_date,
        timezone=timezone,
        default_nights=default_nights
    )
    result["check_in"] = date_result.check_in
    result["check_out"] = date_result.check_out
    result["nights"] = date_result.nights
    result["reasoning"] = date_result.reasoning

    # Check if it's a holiday period (for informational purposes)
    if check_holiday:
        holiday_keywords = [
            "hanukkah", "chanukah", "christmas", "easter", "passover", "pesach",
            "rosh hashanah", "yom kippur", "sukkot", "purim", "shavuot",
            "thanksgiving", "חנוכה", "פסח", "סוכות", "פורים", "שבועות"
        ]

        user_lower = user_input.lower()
        for keyword in holiday_keywords:
            if keyword in user_lower:
                from datetime import date as date_type
                year = datetime.now().year if current_date is None else datetime.fromisoformat(current_date).year
                holiday_resolver = get_holiday_resolver()
                holiday_result = await holiday_resolver.resolve(holiday_name=keyword.title(), year=year, current_date=current_date)

                if holiday_result:
                    result["is_holiday"] = True
                    result["holiday_info"] = holiday_result.dict()
                    break

    # Check if check-in date is a weekend
    weekend_checker = get_weekend_checker()
    weekend_result = await weekend_checker.check(
        check_date=result["check_in"],
        weekend_type=weekend_type
    )
    result["is_weekend"] = weekend_result.is_weekend
    result["weekend_info"] = weekend_result.dict()

    return result
