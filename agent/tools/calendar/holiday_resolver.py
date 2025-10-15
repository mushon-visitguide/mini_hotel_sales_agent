"""
Holiday resolver tool - Resolves holiday names to date ranges.

Supports:
- Jewish holidays via Hebcal API
- Christian holidays (fixed dates and calculated dates like Easter)
- Muslim holidays (future extension)
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import requests


class HolidayResolution(BaseModel):
    """Resolved holiday information"""
    holiday_name: str = Field(description="Name of the holiday")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    duration_days: int = Field(description="Number of days the holiday spans")
    year: int = Field(description="Year of the holiday")
    holiday_type: str = Field(description="Type of holiday: jewish, christian, muslim")


def calculate_easter(year: int) -> datetime:
    """
    Calculate Easter date using Computus algorithm for Western Christianity.

    Args:
        year: Year to calculate Easter for

    Returns:
        datetime object of Easter Sunday
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1

    return datetime(year, month, day)


def calculate_thanksgiving(year: int) -> datetime:
    """
    Calculate US Thanksgiving (4th Thursday of November).

    Args:
        year: Year to calculate Thanksgiving for

    Returns:
        datetime object of Thanksgiving Day
    """
    november_first = datetime(year, 11, 1)
    # Find first Thursday
    days_until_thursday = (3 - november_first.weekday()) % 7
    first_thursday = november_first + timedelta(days=days_until_thursday)
    # Add 3 weeks to get 4th Thursday
    thanksgiving = first_thursday + timedelta(weeks=3)
    return thanksgiving


def get_christian_holiday_dates(holiday_name: str, year: int) -> Optional[Dict[str, Any]]:
    """
    Get Christian holiday dates for the given year.

    Args:
        holiday_name: Name of the Christian holiday
        year: Year to get holiday dates for

    Returns:
        Dictionary with holiday information or None if not found
    """
    # Fixed date holidays
    fixed_holidays = {
        "Christmas": {'date': f"{year}-12-25", 'duration': 2},  # Dec 24-25
        "Christmas Eve": {'date': f"{year}-12-24", 'duration': 1},
        "Christmas Day": {'date': f"{year}-12-25", 'duration': 1},
        "New Year": {'date': f"{year}-01-01", 'duration': 1},
        "New Year's Day": {'date': f"{year}-01-01", 'duration': 1},
        "New Year's Eve": {'date': f"{year}-12-31", 'duration': 1},
        "Epiphany": {'date': f"{year}-01-06", 'duration': 1},
        "Valentine's Day": {'date': f"{year}-02-14", 'duration': 1},
        "All Saints Day": {'date': f"{year}-11-01", 'duration': 1},
        "Thanksgiving": {'date': calculate_thanksgiving(year).strftime('%Y-%m-%d'), 'duration': 4},
    }

    # Check if it's a fixed date holiday
    if holiday_name in fixed_holidays:
        holiday_info = fixed_holidays[holiday_name]
        start = datetime.strptime(holiday_info['date'], '%Y-%m-%d')
        end = start + timedelta(days=holiday_info['duration'] - 1)
        return {
            'holiday_name': holiday_name,
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'duration_days': holiday_info['duration'],
            'year': year,
            'holiday_type': 'christian'
        }

    # Easter-based holidays
    easter_date = calculate_easter(year)

    easter_holidays = {
        "Easter": {'offset': 0, 'duration': 4},  # Good Friday to Easter Monday
        "Easter Sunday": {'offset': 0, 'duration': 1},
        "Good Friday": {'offset': -2, 'duration': 1},
        "Palm Sunday": {'offset': -7, 'duration': 1},
        "Ash Wednesday": {'offset': -46, 'duration': 1},
        "Pentecost": {'offset': 49, 'duration': 1},
        "Ascension Day": {'offset': 39, 'duration': 1},
        "Easter Monday": {'offset': 1, 'duration': 1},
    }

    if holiday_name in easter_holidays:
        holiday_info = easter_holidays[holiday_name]
        start = easter_date + timedelta(days=holiday_info['offset'])
        end = start + timedelta(days=holiday_info['duration'] - 1)
        return {
            'holiday_name': holiday_name,
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'duration_days': holiday_info['duration'],
            'year': year,
            'holiday_type': 'christian'
        }

    return None


def get_jewish_holiday_dates(holiday_name: str, year: int, current_date: Optional[str] = None, allow_past: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get Jewish holiday dates from Hebcal API.

    Queries both current year and next year, then returns the first occurrence
    that is on or after current_date (unless allow_past=True).

    Args:
        holiday_name: Name of the Jewish holiday
        year: Year to search in
        current_date: Current date in YYYY-MM-DD format (used for filtering unless allow_past=True)
        allow_past: If True, return holiday from requested year even if it passed

    Returns:
        Dictionary with holiday information or None if not found
    """
    if current_date is None:
        from datetime import date
        current_date = date.today().isoformat()

    # Query both this year and next year to catch holidays that may have passed
    start_date = f"{year}-01-01"
    end_date = f"{year + 1}-12-31" if not allow_past else f"{year}-12-31"

    # Hebcal API URL with start/end date range and all holiday types
    hebcal_url = f"https://www.hebcal.com/hebcal?v=1&cfg=json&start={start_date}&end={end_date}&maj=on&min=on&i=on&mod=on"

    try:
        response = requests.get(hebcal_url, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        items = data.get('items', [])

        # Map holiday names to Hebcal titles
        holiday_mappings = {
            "Rosh Hashanah": ["Rosh Hashana"],
            "Yom Kippur": ["Yom Kippur"],
            "Sukkot": ["Sukkot"],
            "Passover": ["Pesach", "Passover"],
            "Pesach": ["Pesach", "Passover"],
            "Hanukkah": ["Chanukah"],
            "Chanukah": ["Chanukah"],
            "Purim": ["Purim"],
            "Shavuot": ["Shavuot"],
            "Simchat Torah": ["Shmini Atzeret", "Simchat Torah"],
            "Shemini Atzeret": ["Shmini Atzeret"],
            "Tu BiShvat": ["Tu BiShvat"],
            "Tu B'Shvat": ["Tu BiShvat"],
            "Lag BaOmer": ["Lag BaOmer", "Lag B'Omer"],
            "Lag B'Omer": ["Lag BaOmer", "Lag B'Omer"],
            "Tisha B'Av": ["Tish'a B'Av"],
            "Yom HaAtzmaut": ["Yom HaAtzma'ut", "Yom HaAtzma"],
            "Yom HaZikaron": ["Yom HaZikaron"],
            "Yom HaShoah": ["Yom HaShoah"],
            "Yom Yerushalayim": ["Yom Yerushalayim"],
            "Tu B'Av": ["Tu B'Av"],
        }

        # Holiday durations (in nights for hotel bookings)
        # Note: For Passover, we start from Erev Pesach and add 8 days to get 8 nights
        holiday_durations = {
            "Rosh Hashanah": 2,
            "Yom Kippur": 1,
            "Sukkot": 7,
            "Passover": 8,  # Erev Pesach + 7 days of Pesach = 8 nights (Apr 1-9)
            "Pesach": 8,     # Erev Pesach + 7 days of Pesach = 8 nights (Apr 1-9)
            "Hanukkah": 8,
            "Chanukah": 8,
            "Purim": 1,
            "Shavuot": 2,
            "Simchat Torah": 1,
            "Shemini Atzeret": 1,
            "Tu BiShvat": 1,
            "Tu B'Shvat": 1,
            "Lag BaOmer": 1,
            "Lag B'Omer": 1,
            "Tisha B'Av": 1,
            "Yom HaAtzmaut": 1,
            "Yom HaZikaron": 1,
            "Yom HaShoah": 1,
            "Yom Yerushalayim": 1,
            "Tu B'Av": 1,
        }

        # Find the holiday dates
        holiday_dates = []
        search_terms = holiday_mappings.get(holiday_name, [holiday_name])

        # Special tracking for Hanukkah start date
        hanukkah_start_date = None

        # Special tracking for Passover - we want Erev Pesach as the start
        passover_erev_date = None

        for item in items:
            title = item.get('title', '')

            # For Passover/Pesach, capture Erev Pesach separately
            if holiday_name in ["Passover", "Pesach"] and "Erev Pesach" in title:
                passover_erev_date = item.get('date', '')

            # Skip eve/erev entries and variations that aren't the main holiday
            if any(skip in title for skip in ['Erev', 'Sheni', 'Shushan', 'Meshulash', 'LaBehemot']):
                continue

            for search_term in search_terms:
                # For Yom HaAtzmaut, be more flexible with the apostrophe
                if "HaAtzma" in search_term and "HaAtzma" in title:
                    title_check = True
                else:
                    title_check = search_term.lower() in title.lower()

                if title_check:
                    date_str = item.get('date', '')
                    if date_str:
                        # Special handling for Hanukkah - we ONLY want "1 Candle" as the start
                        if holiday_name in ["Hanukkah", "Chanukah"] and "Chanukah" in title:
                            if "1 Candle" in title:
                                holiday_dates.append(date_str)
                        else:
                            # For other holidays, skip days after the first
                            if not any(num in title for num in [' II', ' III', ' IV', ' V', ' VI', ' VII', ' VIII']):
                                holiday_dates.append(date_str)

        if holiday_dates:
            # Filter out dates that have passed (unless allow_past=True)
            if not allow_past:
                holiday_dates = [d for d in holiday_dates if d >= current_date]

            if not holiday_dates:
                return None

            # Get first date for holiday period
            holiday_dates.sort()
            start_date = holiday_dates[0]

            # Special handling for Passover - use Erev Pesach as start if available
            if holiday_name in ["Passover", "Pesach"] and passover_erev_date:
                # Use Erev Pesach as start date for hotel bookings
                start_date = passover_erev_date

            duration = holiday_durations.get(holiday_name, 1)

            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = start + timedelta(days=duration)

            return {
                'holiday_name': holiday_name,
                'start_date': start.strftime('%Y-%m-%d'),
                'end_date': end.strftime('%Y-%m-%d'),
                'duration_days': duration,
                'year': year,
                'holiday_type': 'jewish'
            }

    except Exception as e:
        print(f"Error fetching Jewish holiday dates: {e}")
        return None

    return None


class HolidayResolver:
    """
    Resolves holiday names to concrete date ranges.

    Supports Jewish holidays (via Hebcal API) and Christian holidays.
    """

    def __init__(self):
        """Initialize holiday resolver."""
        pass

    async def resolve(
        self,
        holiday_name: str,
        year: Optional[int] = None,
        current_date: Optional[str] = None,
        return_string: bool = False
    ) -> Optional[str | HolidayResolution]:
        """
        Resolve holiday name to date range.

        If year is not specified, automatically returns the next upcoming occurrence.
        If year IS specified, returns that year's holiday even if it passed.

        Handles "Eve" requests (e.g., "Christmas Eve", "Erev Sukkot", "ערב פסח")
        by finding the main holiday and returning the day before.

        Args:
            holiday_name: Name of the holiday (e.g., "Hanukkah", "Christmas", "Passover", "Sukkot Eve")
            year: Year to get holiday for (if specified, returns that year even if past)
            current_date: Current date in YYYY-MM-DD format (defaults to today)
            return_string: If True, return simple string "Holiday is from YYYY-MM-DD to YYYY-MM-DD", otherwise return HolidayResolution object

        Returns:
            String description or HolidayResolution with dates or None if holiday not found
        """
        year_was_specified = year is not None

        if year is None:
            year = datetime.now().year

        if current_date is None:
            from datetime import date
            current_date = date.today().isoformat()

        # First, check if this exact holiday name exists (e.g., "Christmas Eve", "New Year's Eve")
        # Try Christian holidays first for exact match
        christian_result = get_christian_holiday_dates(holiday_name, year)
        if christian_result and christian_result['start_date'] >= current_date:
            resolution = HolidayResolution(**christian_result)
            if return_string:
                return f"{resolution.holiday_name} is from {resolution.start_date} to {resolution.end_date}"
            return resolution

        # Check if this is an "Eve" request that needs to be calculated
        is_eve_request = False
        main_holiday_name = holiday_name

        # Detect Eve patterns (English, Hebrew, transliterated)
        eve_patterns = [
            (' Eve', ''),
            (' eve', ''),
            ('Erev ', ''),
            ('erev ', ''),
            ('ערב ', ''),
        ]

        for pattern, replacement in eve_patterns:
            if pattern in holiday_name:
                is_eve_request = True
                main_holiday_name = holiday_name.replace(pattern, replacement).strip()
                break

        # Try Jewish holidays (for main holiday)
        # If year was explicitly provided, return that year even if passed
        # Otherwise, filter out past holidays
        jewish_result = get_jewish_holiday_dates(main_holiday_name, year, current_date, allow_past=year_was_specified)
        if jewish_result:
            # If this is an Eve request, return the day before
            if is_eve_request:
                start_date = datetime.strptime(jewish_result['start_date'], '%Y-%m-%d')
                eve_date = start_date - timedelta(days=1)
                resolution = HolidayResolution(
                    holiday_name=f"{main_holiday_name} Eve",
                    start_date=eve_date.strftime('%Y-%m-%d'),
                    end_date=eve_date.strftime('%Y-%m-%d'),
                    duration_days=1,
                    year=year,
                    holiday_type='jewish'
                )
                if return_string:
                    return f"{resolution.holiday_name} is from {resolution.start_date} to {resolution.end_date}"
                return resolution
            resolution = HolidayResolution(**jewish_result)
            if return_string:
                return f"{resolution.holiday_name} is from {resolution.start_date} to {resolution.end_date}"
            return resolution

        # Try Christian holidays (for main holiday)
        christian_result = get_christian_holiday_dates(main_holiday_name, year)
        if christian_result:
            # If this is an Eve request, return the day before
            if is_eve_request:
                start_date = datetime.strptime(christian_result['start_date'], '%Y-%m-%d')
                eve_date = start_date - timedelta(days=1)
                resolution = HolidayResolution(
                    holiday_name=f"{main_holiday_name} Eve",
                    start_date=eve_date.strftime('%Y-%m-%d'),
                    end_date=eve_date.strftime('%Y-%m-%d'),
                    duration_days=1,
                    year=year,
                    holiday_type=christian_result['holiday_type']
                )
                if return_string:
                    return f"{resolution.holiday_name} is from {resolution.start_date} to {resolution.end_date}"
                return resolution
            resolution = HolidayResolution(**christian_result)
            if return_string:
                return f"{resolution.holiday_name} is from {resolution.start_date} to {resolution.end_date}"
            return resolution

        # Could add Muslim holidays here in the future

        return None


# Cache for holidays (in-memory with TTL)
_holidays_cache = {
    "data": None,
    "timestamp": None,
    "ttl_hours": 24
}


def get_all_holidays_cached(current_year: Optional[int] = None) -> str:
    """
    Get all Jewish and Christian holidays for current and next year in condensed format.

    Uses in-memory cache with 24-hour TTL to minimize API calls to Hebcal.

    This is meant to be injected into LLM prompts so the date resolver can understand
    holiday references without needing separate API calls.

    Args:
        current_year: Year to start from (defaults to current year)

    Returns:
        Condensed string with all holidays
    """
    if current_year is None:
        current_year = datetime.now().year

    # Check if cache is still valid
    if _holidays_cache["data"] is not None and _holidays_cache["timestamp"] is not None:
        cache_age_hours = (datetime.now() - _holidays_cache["timestamp"]).total_seconds() / 3600
        if cache_age_hours < _holidays_cache["ttl_hours"]:
            # Cache is still valid, return cached data
            return _holidays_cache["data"]

    # Cache expired or empty, fetch fresh data
    holidays = []

    # Get holidays for current year and next year
    for year in [current_year, current_year + 1]:
        # Christian holidays (fast, calculated)
        christian_names = [
            "Christmas", "Christmas Eve", "New Year's Day", "New Year's Eve",
            "Easter", "Good Friday", "Palm Sunday", "Thanksgiving"
        ]
        for name in christian_names:
            result = get_christian_holiday_dates(name, year)
            if result:
                holidays.append(f"{result['holiday_name']} {year}: {result['start_date']} to {result['end_date']}")

        # Jewish holidays (slow, API call to Hebcal)
        jewish_names = [
            "Rosh Hashanah", "Yom Kippur", "Sukkot", "Passover", "Hanukkah",
            "Purim", "Shavuot", "Tu BiShvat", "Lag BaOmer"
        ]
        for name in jewish_names:
            result = get_jewish_holiday_dates(name, year, allow_past=True)
            if result:
                holidays.append(f"{result['holiday_name']} {year}: {result['start_date']} to {result['end_date']}")

    result = "\n".join(holidays)

    # Update cache
    _holidays_cache["data"] = result
    _holidays_cache["timestamp"] = datetime.now()

    return result


# Singleton instance
_holiday_resolver_instance = None


def get_holiday_resolver() -> HolidayResolver:
    """Get or create singleton HolidayResolver instance"""
    global _holiday_resolver_instance
    if _holiday_resolver_instance is None:
        _holiday_resolver_instance = HolidayResolver()
    return _holiday_resolver_instance
