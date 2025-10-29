"""Calendar tools registration for the agent tool registry"""
from typing import Optional, List, Tuple
from datetime import datetime, date
from agent.tools.registry import registry
from .date_resolver import get_resolver
from .holiday_resolver import get_holiday_resolver, get_all_holidays_cached
from .weekend_checker import get_weekend_checker


def _find_overlapping_holidays_from_str(check_in_date: date, check_out_date: date, holidays_str: str) -> List[Tuple[str, str, str]]:
    """
    Find holidays that overlap with the given date range.

    Args:
        check_in_date: Check-in date
        check_out_date: Check-out date
        holidays_str: Pre-fetched holidays string from get_all_holidays_cached()

    Returns:
        List of tuples: (holiday_name, start_date, end_date)
    """
    overlapping = []

    for line in holidays_str.strip().split('\n'):
        if not line.strip():
            continue

        # Parse format: "Hanukkah 2025: 2025-12-25 to 2026-01-02"
        try:
            parts = line.split(': ')
            if len(parts) != 2:
                continue

            holiday_name_year = parts[0].strip()
            date_range = parts[1].strip()

            # Extract holiday name without year
            name_parts = holiday_name_year.rsplit(' ', 1)
            if len(name_parts) == 2:
                holiday_name = name_parts[0]
            else:
                holiday_name = holiday_name_year

            # Parse dates
            date_parts = date_range.split(' to ')
            if len(date_parts) != 2:
                continue

            holiday_start = datetime.strptime(date_parts[0].strip(), '%Y-%m-%d').date()
            holiday_end = datetime.strptime(date_parts[1].strip(), '%Y-%m-%d').date()

            # Check for overlap: ranges overlap if start1 <= end2 AND start2 <= end1
            if check_in_date <= holiday_end and holiday_start <= check_out_date:
                overlapping.append((
                    holiday_name,
                    holiday_start.strftime('%B %d, %Y'),
                    holiday_end.strftime('%B %d, %Y')
                ))
        except (ValueError, IndexError):
            continue

    return overlapping


@registry.tool(
    name="calendar.resolve_date_hint",
    description="Resolve fuzzy date hints like 'next weekend', 'first of October', 'tomorrow' to concrete dates"
)
async def resolve_date_hint(
    date_hint: str,
    current_date: Optional[str] = None,
    timezone: str = "Asia/Jerusalem",
    default_nights: int = 1
) -> str:
    """
    Resolve fuzzy date hint to concrete dates.

    Args:
        date_hint: Natural language date (e.g., "next weekend", "Oct 1st", "tomorrow")
        current_date: Current date YYYY-MM-DD (defaults to today)
        timezone: Timezone for interpretation (default: Asia/Jerusalem)
        default_nights: Default stay length (default: 1 night)

    Returns:
        Human-readable description of the resolved dates for the response generator
    """
    # Get current date for holiday fetching
    if current_date is None:
        from datetime import date as dt_date
        current_date = dt_date.today().isoformat()

    current_dt = datetime.strptime(current_date, "%Y-%m-%d")
    current_year = current_dt.year

    # OPTIMIZATION: Fetch holidays once upfront (will be cached and reused)
    # This happens in parallel conceptually with resolver setup
    import asyncio
    holidays_task = asyncio.create_task(asyncio.to_thread(get_all_holidays_cached, current_year))

    # Start date resolution (this also calls get_all_holidays_cached internally, but hits cache)
    resolver = get_resolver()
    result = await resolver.resolve(
        date_hint=date_hint,
        current_date=current_date,
        timezone=timezone,
        default_nights=default_nights
    )

    # Wait for holidays to be ready (usually instant due to cache)
    holidays_str = await holidays_task

    # Convert to natural language for description
    check_in_dt = datetime.strptime(result.check_in, "%Y-%m-%d")
    check_out_dt = datetime.strptime(result.check_out, "%Y-%m-%d")

    # Get day names
    check_in_day = check_in_dt.strftime("%A")  # e.g., "Wednesday"
    check_out_day = check_out_dt.strftime("%A")  # e.g., "Thursday"

    # Format checkout date
    check_out_formatted = check_out_dt.strftime("%A, %B %d, %Y")  # "Thursday, October 30, 2025"

    # Build description with new format:
    # "Check-in Wednesday, 1 night stay, checking out Thursday, October 30, 2025"
    nights = result.nights
    night_str = "1 night" if nights == 1 else f"{nights} nights"

    description = f"Check-in {check_in_day}, {night_str} stay, checking out {check_out_formatted}"

    # Check for holidays using pre-fetched data
    check_in_date = check_in_dt.date()
    check_out_date = check_out_dt.date()

    overlapping_holidays = _find_overlapping_holidays_from_str(
        check_in_date, check_out_date, holidays_str
    )

    if overlapping_holidays:
        # Add holiday information
        for holiday_name, holiday_start, holiday_end in overlapping_holidays:
            if holiday_start == holiday_end:
                description += f" (during {holiday_name} on {holiday_start})"
            else:
                description += f" (during {holiday_name} from {holiday_start} to {holiday_end})"

    # Return structured data for orchestrator AND readable text for response generator
    # The orchestrator extracts check_in/check_out, but __str__ will show description
    class DateResult(dict):
        def __str__(self):
            return self.get("__display__", dict.__repr__(self))
        def __repr__(self):
            return self.__str__()

    return DateResult({
        "check_in": result.get_check_in_date(),
        "check_out": result.get_check_out_date(),
        "nights": result.nights,
        "__display__": description
    })


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
