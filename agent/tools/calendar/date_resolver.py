"""
Date resolver tool - Converts fuzzy date hints to actual dates using LLM.

Examples:
  - "next weekend" → 2024-10-19 to 2024-10-20
  - "first week of October" → 2024-10-01 to 2024-10-07
  - "this Friday for 2 nights" → 2024-10-18 to 2024-10-20
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field
from agent.llm.client import LLMClient
from agent.tools.calendar.holiday_resolver import get_holiday_resolver, get_all_holidays_cached
import os


class DateResolution(BaseModel):
    """Resolved dates from fuzzy hint"""
    check_in: str = Field(description="Check-in date in YYYY-MM-DD format")
    check_out: str = Field(description="Check-out date in YYYY-MM-DD format")
    nights: int = Field(description="Number of nights")
    days: int = Field(description="Number of days (equals nights + 1)")
    reasoning: str = Field(description="Brief explanation of how the dates were resolved")

    def get_check_in_date(self) -> date:
        """Convert check_in string to date object"""
        return datetime.strptime(self.check_in, "%Y-%m-%d").date()

    def get_check_out_date(self) -> date:
        """Convert check_out string to date object"""
        return datetime.strptime(self.check_out, "%Y-%m-%d").date()


class DateResolver:
    """
    Resolves fuzzy date hints to concrete dates using LLM.

    Uses OpenAI Structured Outputs for reliable date parsing.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize date resolver.

        Args:
            llm_client: LLM client (creates default if not provided)
        """
        self.llm = llm_client or LLMClient(api_key=os.getenv("OPENAI_API_KEY"))

    async def resolve(
        self,
        date_hint: str,
        current_date: Optional[str] = None,
        timezone: str = "Asia/Jerusalem",
        default_nights: int = 1
    ) -> DateResolution:
        """
        Resolve fuzzy date hint to concrete check-in/check-out dates.

        Args:
            date_hint: Natural language date reference (e.g., "next weekend", "Oct 1st")
            current_date: Current date in YYYY-MM-DD (defaults to today)
            timezone: Timezone for date interpretation
            default_nights: Default number of nights if not specified in hint

        Returns:
            DateResolution with check_in, check_out, nights, and reasoning

        Examples:
            >>> await resolve("next weekend")
            DateResolution(check_in="2024-10-19", check_out="2024-10-20", nights=1, ...)

            >>> await resolve("first week of October for 3 nights")
            DateResolution(check_in="2024-10-01", check_out="2024-10-04", nights=3, ...)
        """
        # Get current date
        if current_date is None:
            current_date = date.today().isoformat()

        # Parse current date to get day of week
        current_dt = datetime.fromisoformat(current_date)
        day_name = current_dt.strftime("%A")

        # Get ALL holidays upfront (cached, fast)
        all_holidays = get_all_holidays_cached(current_year=current_dt.year)

        # Build prompt with all holidays included
        system_prompt = self._build_system_prompt(
            current_date=current_date,
            day_name=day_name,
            timezone=timezone,
            default_nights=default_nights,
            all_holidays=all_holidays
        )

        user_message = f"Resolve this date hint: '{date_hint}'"

        # Call LLM with structured output
        result = self.llm.structured_completion(
            system_prompt=system_prompt,
            user_message=user_message,
            response_schema=DateResolution,
            temperature=0.0
        )

        # Validate that check_in is not in the past
        check_in_date = datetime.fromisoformat(result.check_in).date()
        current_date_obj = datetime.fromisoformat(current_date).date()

        if check_in_date < current_date_obj:
            raise ValueError(
                f"LLM returned past check-in date {result.check_in} (today is {current_date}). "
                f"Reasoning: {result.reasoning}"
            )

        return result

    def _build_system_prompt(
        self,
        current_date: str,
        day_name: str,
        timezone: str,
        default_nights: int,
        all_holidays: str
    ) -> str:
        """Build system prompt for date resolution with all holidays injected"""
        return f"""You are a date resolver for a hotel booking system.

## CURRENT CONTEXT
**Today's exact date: {current_date} ({day_name})**
Timezone: {timezone}

## ALL UPCOMING HOLIDAYS
Here are all Jewish and Christian holidays for this year and next year.
Use these EXACT dates when the user mentions any holiday:

{all_holidays}

## YOUR TASK
Parse natural language date hints and return structured dates with check-in, check-out, nights, and days.

## CRITICAL RULES

1. **NEVER return check_in dates in the past - MANDATORY**
   - check_in MUST be >= {current_date}
   - If the start of any requested period has passed, advance to NEXT occurrence
   - Example: Today is 2025-10-15, user says "September" → return September 2026
   - Example: Today is 2025-10-15, user says "Sukkot" (Oct 13-19) → Since Oct 13 < Oct 15, return Sukkot 2026
   - Example: Today is 2025-10-15, user says "October 13" → return Oct 13, 2026

2. **Set duration based on user request**
   - If user specifies explicit duration ("3 nights", "for 5 days"), use that
   - If user mentions a time period ("week", "weekend"), infer the full duration:
     * "week" = 7 days = 6 nights
     * "weekend" = 2 days = 1-2 nights (Friday-Saturday OR Saturday-Sunday)
     * "first week of October" = October 1-7 = 7 days = 6 nights
     * "last week of September" = September 24-30 = 7 days = 6 nights
   - If no duration mentioned at all, use {default_nights} night(s)

3. **Calculate both nights and days**
   - nights = check_out date - check_in date (in days)
   - days = nights + 1
   - Example: Sept 24 to Sept 30 = 6 nights, 7 days

4. **Date format**
   - ALWAYS output dates as YYYY-MM-DD
   - Check-out must be AFTER check-in

## HOLIDAY NAMES

If the date hint mentions a holiday, you must use these EXACT names in your reasoning:

**Jewish Holidays (use these exact names):**
- Hanukkah (or Chanukah)
- Passover (or Pesach)
- Rosh Hashanah
- Yom Kippur
- Sukkot
- Purim
- Shavuot
- Simchat Torah
- Lag BaOmer
- Tisha B'Av
- Tu B'Shvat
- Tu B'Av
- Yom HaAtzmaut
- Yom HaZikaron
- Yom HaShoah
- Yom Yerushalayim

**Christian Holidays:**
- Christmas
- Easter
- Good Friday
- Thanksgiving
- New Year

## REMEMBER
- Today is **{current_date}** ({day_name})
- NEVER return past dates - advance to next year if needed
- Set duration based on what the user actually requested
- Use exact holiday names from the list above
"""


# Singleton instance for use in registry
_resolver_instance = None


def get_resolver() -> DateResolver:
    """Get or create singleton DateResolver instance"""
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = DateResolver()
    return _resolver_instance


# Tool function for registry
async def resolve_date_hint(
    date_hint: str,
    current_date: Optional[str] = None,
    timezone: str = "Asia/Jerusalem",
    default_nights: int = 1
) -> dict:
    """
    Resolve fuzzy date hint to concrete dates.

    Args:
        date_hint: Natural language date (e.g., "next weekend", "Oct 1st")
        current_date: Current date YYYY-MM-DD (defaults to today)
        timezone: Timezone for interpretation (default: Asia/Jerusalem)
        default_nights: Default stay length (default: 1 night)

    Returns:
        {
            "check_in": "YYYY-MM-DD",
            "check_out": "YYYY-MM-DD",
            "nights": int,
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
