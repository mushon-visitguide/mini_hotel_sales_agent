"""Test Eve holiday resolution"""
import asyncio
from agent.tools.calendar.holiday_resolver import get_holiday_resolver
from datetime import datetime, date


async def test():
    print("Testing Eve Holiday Resolution")
    print("=" * 70)
    print(f"Current date: {date.today()}")
    print()

    resolver = get_holiday_resolver()

    # Test Jewish Eve holidays
    test_cases = [
        ("Sukkot Eve", 2026),
        ("Erev Sukkot", 2026),
        ("Passover Eve", 2026),
        ("Erev Pesach", 2026),
        ("Rosh Hashanah Eve", 2026),
        ("Yom Kippur Eve", 2026),
        ("Christmas Eve", 2025),
        ("New Year's Eve", 2025),
    ]

    for holiday_name, year in test_cases:
        print(f"Testing: {holiday_name} {year}")
        result = await resolver.resolve(holiday_name, year)

        if result:
            print(f"  ✅ Found!")
            print(f"     Date: {result.start_date}")
            print(f"     Type: {result.holiday_type}")

            # Verify it's one day before the main holiday
            # Get main holiday for comparison
            main_name = holiday_name.replace(" Eve", "").replace("Erev ", "").replace("ערב ", "")
            main_result = await resolver.resolve(main_name, year)
            if main_result:
                eve_date = datetime.strptime(result.start_date, "%Y-%m-%d").date()
                main_date = datetime.strptime(main_result.start_date, "%Y-%m-%d").date()
                diff = (main_date - eve_date).days

                if diff == 1:
                    print(f"     ✅ Correctly returns 1 day before {main_name} ({main_result.start_date})")
                else:
                    print(f"     ❌ ERROR: Eve date is {diff} days before main holiday!")
        else:
            print(f"  ❌ Not found!")

        print()

    # Test auto-advance for past dates
    print("=" * 70)
    print("Testing auto-advance for Sukkot Eve (2025 already passed):")
    result_2025 = await resolver.resolve("Sukkot Eve", 2025)
    if result_2025:
        eve_date = datetime.strptime(result_2025.start_date, "%Y-%m-%d").date()
        if eve_date < date.today():
            print(f"  ⚠️  Sukkot Eve 2025 ({result_2025.start_date}) has passed")
            print(f"     NOTE: The tool should auto-advance to 2026")
        else:
            print(f"  ✅ Sukkot Eve 2025: {result_2025.start_date}")


if __name__ == "__main__":
    asyncio.run(test())
