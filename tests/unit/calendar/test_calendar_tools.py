"""Test calendar tools"""
import asyncio
from agent.tools.calendar.holiday_resolver import get_holiday_resolver
from agent.tools.calendar.weekend_checker import get_weekend_checker
from agent.tools.calendar.date_resolver import get_resolver


async def test_holiday_resolver():
    """Test holiday resolution"""
    print("\n" + "="*70)
    print("Testing Holiday Resolver")
    print("="*70)

    resolver = get_holiday_resolver()

    # Test Jewish holidays
    print("\n--- Jewish Holidays ---")
    holidays = ["Hanukkah", "Passover", "Rosh Hashanah", "Yom Kippur"]
    for holiday in holidays:
        result = await resolver.resolve(holiday, 2024)
        if result:
            print(f"\n{holiday}:")
            print(f"  Start: {result.start_date}")
            print(f"  End: {result.end_date}")
            print(f"  Duration: {result.duration_days} days")
        else:
            print(f"\n{holiday}: Not found")

    # Test Christian holidays
    print("\n--- Christian Holidays ---")
    holidays = ["Christmas", "Easter", "Good Friday", "Thanksgiving"]
    for holiday in holidays:
        result = await resolver.resolve(holiday, 2024)
        if result:
            print(f"\n{holiday}:")
            print(f"  Start: {result.start_date}")
            print(f"  End: {result.end_date}")
            print(f"  Duration: {result.duration_days} days")
        else:
            print(f"\n{holiday}: Not found")


async def test_weekend_checker():
    """Test weekend checking"""
    print("\n" + "="*70)
    print("Testing Weekend Checker")
    print("="*70)

    checker = get_weekend_checker()

    test_dates = [
        "2024-10-17",  # Thursday
        "2024-10-18",  # Friday
        "2024-10-19",  # Saturday
        "2024-10-20",  # Sunday
        "2024-10-21",  # Monday
    ]

    print("\n--- Israeli Weekend (Thu-Sat) ---")
    for date in test_dates:
        result = await checker.check(date, "israeli")
        print(f"{date} ({result.day_name}): {'YES' if result.is_weekend else 'NO'}")

    print("\n--- Western Weekend (Sat-Sun) ---")
    for date in test_dates:
        result = await checker.check(date, "western")
        print(f"{date} ({result.day_name}): {'YES' if result.is_weekend else 'NO'}")


async def test_date_resolver():
    """Test date resolution"""
    print("\n" + "="*70)
    print("Testing Date Resolver")
    print("="*70)

    resolver = get_resolver()

    test_hints = [
        "tomorrow",
        "next weekend",
        "first of December",
        "in 3 days",
    ]

    for hint in test_hints:
        result = await resolver.resolve(hint, current_date="2024-10-15")
        print(f"\n'{hint}':")
        print(f"  Check-in: {result.check_in}")
        print(f"  Check-out: {result.check_out}")
        print(f"  Nights: {result.nights}")
        print(f"  Reasoning: {result.reasoning}")


async def main():
    """Run all tests"""
    await test_holiday_resolver()
    await test_weekend_checker()
    await test_date_resolver()

    print("\n" + "="*70)
    print("All tests completed!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
