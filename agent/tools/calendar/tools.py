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
        Dict with check_in and check_out as date objects, plus description for natural language response
    """
    resolver = get_resolver()
    result = await resolver.resolve(
        date_hint=date_hint,
        current_date=current_date,
        timezone=timezone,
        default_nights=default_nights
    )

    # Convert to natural language for description
    from datetime import datetime
    check_in_dt = datetime.strptime(result.check_in, "%Y-%m-%d")
    check_out_dt = datetime.strptime(result.check_out, "%Y-%m-%d")

    check_in_formatted = check_in_dt.strftime("%B %d, %Y")
    check_out_formatted = check_out_dt.strftime("%B %d, %Y")

    if result.nights == 1:
        description = f"{date_hint.capitalize()} is {check_in_formatted} (1 night stay, checking out {check_out_formatted})"
    else:
        description = f"{date_hint.capitalize()} is from {check_in_formatted} to {check_out_formatted} ({result.nights} nights)"

    # Return structured data with date objects for other tools to use
    return {
        "check_in": result.get_check_in_date(),
        "check_out": result.get_check_out_date(),
        "nights": result.nights,
        "description": description
    }


@registry.tool(
    name="calendar.check_is_weekend",
    description="Check if a specific date falls on a weekend (Israeli: Thu-Sat or Western: Sat-Sun)"
)
async def check_is_weekend(
    date: str,
    weekend_type: Optional[str] = "israeli"
) -> str:
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
        Natural language description of whether the date is a weekend
    """
    checker = get_weekend_checker()
    result = await checker.check(check_date=date, weekend_type=weekend_type)

    # Convert to natural language
    from datetime import datetime
    dt = datetime.strptime(result.date, "%Y-%m-%d")
    date_formatted = dt.strftime("%B %d, %Y")

    weekend_desc = {
        "israeli": "Israeli weekend (Thursday-Saturday)",
        "western": "Western weekend (Saturday-Sunday)",
        "friday_saturday": "Friday-Saturday weekend",
        "saturday_sunday": "Saturday-Sunday weekend"
    }.get(result.weekend_type, result.weekend_type)

    if result.is_weekend:
        return f"{result.day_name}, {date_formatted} is a {weekend_desc}"
    else:
        return f"{result.day_name}, {date_formatted} is not a {weekend_desc}"
