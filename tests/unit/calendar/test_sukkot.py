"""Test Sukkot dates"""
import asyncio
from agent.tools.calendar.holiday_resolver import get_holiday_resolver
from datetime import datetime, date


async def test():
    print("Testing Sukkot resolution...")
    print(f"Current date: {date.today()}")
    print()

    resolver = get_holiday_resolver()

    # Test Sukkot 2025
    result_2025 = await resolver.resolve("Sukkot", 2025)
    if result_2025:
        print("Sukkot 2025:")
        print(f"  Start Date: {result_2025.start_date}")
        print(f"  End Date: {result_2025.end_date}")
        print(f"  Duration: {result_2025.duration_days} days")

        # Check if it's in the past
        holiday_end = datetime.strptime(result_2025.end_date, "%Y-%m-%d").date()
        today = date.today()
        if holiday_end < today:
            print(f"  ⚠️  This date has PASSED (ended {holiday_end})")
        else:
            print(f"  ✅ This date is UPCOMING")
        print()

    # Test Sukkot 2026
    result_2026 = await resolver.resolve("Sukkot", 2026)
    if result_2026:
        print("Sukkot 2026:")
        print(f"  Start Date: {result_2026.start_date}")
        print(f"  End Date: {result_2026.end_date}")
        print(f"  Duration: {result_2026.duration_days} days")
        print()

    # Test with auto-advance logic
    print("Testing 'next Sukkot' with auto-advance:")
    year = datetime.now().year
    result = await resolver.resolve("Sukkot", year)

    if result:
        holiday_end = datetime.strptime(result.end_date, "%Y-%m-%d").date()
        if holiday_end < date.today():
            print(f"  Sukkot {year} has passed, getting {year + 1}...")
            result = await resolver.resolve("Sukkot", year + 1)

        print(f"  📅 Next Sukkot (Year {result.year}):")
        print(f"    Start: {result.start_date}")
        print(f"    End: {result.end_date}")
        print(f"    Duration: {result.duration_days} days")


if __name__ == "__main__":
    asyncio.run(test())
