"""Quick test to verify Rosh Hashanah next occurrence logic"""
import asyncio
from agent.tools.calendar.holiday_resolver import get_holiday_resolver
from datetime import datetime, date


async def test():
    print("Testing Rosh Hashanah resolution with current date consideration...")
    print(f"Current date: {date.today()}")
    print()

    resolver = get_holiday_resolver()

    # Test 1: Get Rosh Hashanah 2025
    result_2025 = await resolver.resolve("Rosh Hashanah", 2025)
    if result_2025:
        print("Rosh Hashanah 2025:")
        print(f"  Start Date: {result_2025.start_date}")
        print(f"  End Date: {result_2025.end_date}")
        print(f"  Duration: {result_2025.duration_days} days")

        # Check if it's in the past
        holiday_end = datetime.strptime(result_2025.end_date, "%Y-%m-%d").date()
        today = date.today()
        if holiday_end < today:
            print(f"  ⚠️  This date has PASSED (ended {holiday_end})")
        print()

    # Test 2: Get Rosh Hashanah 2026
    result_2026 = await resolver.resolve("Rosh Hashanah", 2026)
    if result_2026:
        print("Rosh Hashanah 2026:")
        print(f"  Start Date: {result_2026.start_date}")
        print(f"  End Date: {result_2026.end_date}")
        print(f"  Duration: {result_2026.duration_days} days")
        print()

    # Test 3: Request current year (should auto-detect if passed)
    print("Testing with auto-advance logic:")
    year = datetime.now().year
    result = await resolver.resolve("Rosh Hashanah", year)

    if result:
        holiday_end = datetime.strptime(result.end_date, "%Y-%m-%d").date()
        if holiday_end < date.today():
            print(f"  2025 has passed, getting 2026...")
            result = await resolver.resolve("Rosh Hashanah", year + 1)

        print(f"  Final Result (Year {result.year}):")
        print(f"    Start: {result.start_date}")
        print(f"    End: {result.end_date}")


if __name__ == "__main__":
    asyncio.run(test())
