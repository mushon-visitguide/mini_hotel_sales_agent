"""Final comprehensive test for Eve holidays with auto-advance"""
import asyncio
from agent.tools.calendar.holiday_resolver import get_holiday_resolver
from datetime import datetime, date


async def test():
    print("=" * 70)
    print("COMPREHENSIVE EVE HOLIDAY TEST WITH AUTO-ADVANCE")
    print("=" * 70)
    print(f"Today: {date.today()}")
    print()

    resolver = get_holiday_resolver()

    # Helper function to check and auto-advance
    async def get_next_occurrence(holiday_name):
        year = datetime.now().year
        result = await resolver.resolve(holiday_name, year)
        if result:
            holiday_end = datetime.strptime(result.end_date, "%Y-%m-%d").date()
            if holiday_end < date.today():
                # Get next year
                result = await resolver.resolve(holiday_name, year + 1)
        return result

    # Test 1: Sukkot Eve (should auto-advance from 2025 to 2026)
    print("Test 1: Sukkot Eve (no year specified, should return 2026)")
    print("-" * 70)
    result = await get_next_occurrence("Sukkot Eve")
    if result is None:
        print(f"  ❌ Error: Holiday not found")
    else:
        print(f"  ✅ {result.holiday_name}")
        print(f"     Date: {result.start_date}")
        print(f"     Year: {result.year}")
        print(f"     Expected: 2026-09-25 (1 day before Sukkot 2026-09-26)")
    print()

    # Test 2: Erev Sukkot with Hebrew
    print("Test 2: Erev Sukkot (Hebrew transliteration)")
    print("-" * 70)
    result = await get_next_occurrence("Erev Sukkot")
    if result is None:
        print(f"  ❌ Error: Holiday not found")
    else:
        print(f"  ✅ {result.holiday_name}")
        print(f"     Date: {result.start_date}")
        print(f"     Year: {result.year}")
    print()

    # Test 3: Christmas Eve (upcoming)
    print("Test 3: Christmas Eve 2025 (upcoming)")
    print("-" * 70)
    result = await get_next_occurrence("Christmas Eve")
    if result is None:
        print(f"  ❌ Error: Holiday not found")
    else:
        print(f"  ✅ {result.holiday_name}")
        print(f"     Date: {result.start_date}")
        print(f"     Expected: 2025-12-24")
    print()

    # Test 4: Rosh Hashanah Eve
    print("Test 4: Rosh Hashanah Eve (should auto-advance to 2026)")
    print("-" * 70)
    result = await get_next_occurrence("Rosh Hashanah Eve")
    if result is None:
        print(f"  ❌ Error: Holiday not found")
    else:
        print(f"  ✅ {result.holiday_name}")
        print(f"     Date: {result.start_date}")
        print(f"     Year: {result.year}")
        print(f"     Expected: 2026-09-11 (1 day before RH 2026-09-12)")
    print()

    # Test 5: Passover Eve
    print("Test 5: Passover Eve / Erev Pesach (should return 2026)")
    print("-" * 70)
    result = await get_next_occurrence("Erev Pesach")
    if result is None:
        print(f"  ❌ Error: Holiday not found")
    else:
        print(f"  ✅ {result.holiday_name}")
        print(f"     Date: {result.start_date}")
        print(f"     Year: {result.year}")
        print(f"     Expected: 2026-04-01 (1 day before Passover 2026-04-02)")
    print()

    # Test 6: New Year's Eve (pre-defined)
    print("Test 6: New Year's Eve (pre-defined holiday)")
    print("-" * 70)
    result = await get_next_occurrence("New Year's Eve")
    if result is None:
        print(f"  ❌ Error: Holiday not found")
    else:
        print(f"  ✅ {result.holiday_name}")
        print(f"     Date: {result.start_date}")
        print(f"     Expected: 2025-12-31")
    print()

    print("=" * 70)
    print("ALL TESTS COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test())
