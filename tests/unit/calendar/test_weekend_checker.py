"""
Comprehensive tests for Weekend Checker
Tests verified against actual calendar dates
"""
import pytest
import asyncio
from datetime import datetime, date
from agent.tools.calendar.weekend_checker import (
    get_weekend_checker,
    WeekendChecker
)


class TestWeekendCheckerIsraeli:
    """Test Israeli weekend (Thursday-Saturday)"""

    @pytest.mark.asyncio
    async def test_thursday_is_israeli_weekend(self):
        """
        Test Thursday, December 25, 2025 - Should be Israeli weekend
        Thursday = weekday 3
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-12-25", "israeli")

        assert result.date == "2025-12-25"
        assert result.is_weekend is True, "Thursday should be Israeli weekend"
        assert result.day_name == "Thursday"
        assert result.day_of_week == 3
        assert result.weekend_type == "israeli"

    @pytest.mark.asyncio
    async def test_friday_is_israeli_weekend(self):
        """
        Test Friday, December 26, 2025 - Should be Israeli weekend
        Friday = weekday 4
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-12-26", "israeli")

        assert result.date == "2025-12-26"
        assert result.is_weekend is True, "Friday should be Israeli weekend"
        assert result.day_name == "Friday"
        assert result.day_of_week == 4
        assert result.weekend_type == "israeli"

    @pytest.mark.asyncio
    async def test_saturday_is_israeli_weekend(self):
        """
        Test Saturday, December 27, 2025 - Should be Israeli weekend
        Saturday = weekday 5
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-12-27", "israeli")

        assert result.date == "2025-12-27"
        assert result.is_weekend is True, "Saturday should be Israeli weekend"
        assert result.day_name == "Saturday"
        assert result.day_of_week == 5
        assert result.weekend_type == "israeli"

    @pytest.mark.asyncio
    async def test_sunday_not_israeli_weekend(self):
        """
        Test Sunday, December 28, 2025 - Should NOT be Israeli weekend
        Sunday = weekday 6
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-12-28", "israeli")

        assert result.date == "2025-12-28"
        assert result.is_weekend is False, "Sunday should NOT be Israeli weekend"
        assert result.day_name == "Sunday"
        assert result.day_of_week == 6
        assert result.weekend_type == "israeli"

    @pytest.mark.asyncio
    async def test_monday_not_israeli_weekend(self):
        """
        Test Monday, December 29, 2025 - Should NOT be Israeli weekend
        Monday = weekday 0
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-12-29", "israeli")

        assert result.date == "2025-12-29"
        assert result.is_weekend is False, "Monday should NOT be Israeli weekend"
        assert result.day_name == "Monday"
        assert result.day_of_week == 0
        assert result.weekend_type == "israeli"


class TestWeekendCheckerWestern:
    """Test Western weekend (Saturday-Sunday)"""

    @pytest.mark.asyncio
    async def test_saturday_is_western_weekend(self):
        """
        Test Saturday, April 5, 2025 - Should be Western weekend
        Saturday = weekday 5
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-04-05", "western")

        assert result.date == "2025-04-05"
        assert result.is_weekend is True, "Saturday should be Western weekend"
        assert result.day_name == "Saturday"
        assert result.day_of_week == 5
        assert result.weekend_type == "western"

    @pytest.mark.asyncio
    async def test_sunday_is_western_weekend(self):
        """
        Test Sunday, April 20, 2025 (Easter) - Should be Western weekend
        Sunday = weekday 6
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-04-20", "western")

        assert result.date == "2025-04-20"
        assert result.is_weekend is True, "Sunday should be Western weekend"
        assert result.day_name == "Sunday"
        assert result.day_of_week == 6
        assert result.weekend_type == "western"

    @pytest.mark.asyncio
    async def test_friday_not_western_weekend(self):
        """
        Test Friday, November 28, 2025 - Should NOT be Western weekend
        Friday = weekday 4
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-11-28", "western")

        assert result.date == "2025-11-28"
        assert result.is_weekend is False, "Friday should NOT be Western weekend"
        assert result.day_name == "Friday"
        assert result.day_of_week == 4
        assert result.weekend_type == "western"

    @pytest.mark.asyncio
    async def test_thursday_not_western_weekend(self):
        """
        Test Thursday, November 27, 2025 (Thanksgiving) - Should NOT be Western weekend
        Thursday = weekday 3
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-11-27", "western")

        assert result.date == "2025-11-27"
        assert result.is_weekend is False, "Thursday should NOT be Western weekend"
        assert result.day_name == "Thursday"
        assert result.day_of_week == 3
        assert result.weekend_type == "western"

    @pytest.mark.asyncio
    async def test_monday_not_western_weekend(self):
        """
        Test Monday, January 1, 2026 (New Year) - Should NOT be Western weekend
        Monday = weekday 0
        """
        checker = get_weekend_checker()
        result = await checker.check("2026-01-01", "western")

        assert result.date == "2026-01-01"
        assert result.is_weekend is False, "Monday should NOT be Western weekend"
        assert result.day_name == "Thursday"  # Note: Jan 1, 2026 is actually Thursday
        assert result.day_of_week == 3
        assert result.weekend_type == "western"


class TestWeekendCheckerFridaySaturday:
    """Test Friday-Saturday weekend definition"""

    @pytest.mark.asyncio
    async def test_friday_is_weekend(self):
        """
        Test Friday, April 18, 2025 (Good Friday) - Should be weekend
        Friday = weekday 4
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-04-18", "friday_saturday")

        assert result.date == "2025-04-18"
        assert result.is_weekend is True, "Friday should be weekend in friday_saturday mode"
        assert result.day_name == "Friday"
        assert result.day_of_week == 4
        assert result.weekend_type == "friday_saturday"

    @pytest.mark.asyncio
    async def test_saturday_is_weekend(self):
        """
        Test Saturday, April 19, 2025 - Should be weekend
        Saturday = weekday 5
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-04-19", "friday_saturday")

        assert result.date == "2025-04-19"
        assert result.is_weekend is True, "Saturday should be weekend in friday_saturday mode"
        assert result.day_name == "Saturday"
        assert result.day_of_week == 5
        assert result.weekend_type == "friday_saturday"

    @pytest.mark.asyncio
    async def test_sunday_not_weekend(self):
        """
        Test Sunday, April 20, 2025 (Easter) - Should NOT be weekend
        Sunday = weekday 6
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-04-20", "friday_saturday")

        assert result.date == "2025-04-20"
        assert result.is_weekend is False, "Sunday should NOT be weekend in friday_saturday mode"
        assert result.day_name == "Sunday"
        assert result.day_of_week == 6
        assert result.weekend_type == "friday_saturday"

    @pytest.mark.asyncio
    async def test_thursday_not_weekend(self):
        """
        Test Thursday, April 17, 2025 - Should NOT be weekend
        Thursday = weekday 3
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-04-17", "friday_saturday")

        assert result.date == "2025-04-17"
        assert result.is_weekend is False, "Thursday should NOT be weekend in friday_saturday mode"
        assert result.day_name == "Thursday"
        assert result.day_of_week == 3
        assert result.weekend_type == "friday_saturday"

    @pytest.mark.asyncio
    async def test_wednesday_not_weekend(self):
        """
        Test Wednesday, December 24, 2025 (Christmas Eve) - Should NOT be weekend
        Wednesday = weekday 2
        """
        checker = get_weekend_checker()
        result = await checker.check("2025-12-24", "friday_saturday")

        assert result.date == "2025-12-24"
        assert result.is_weekend is False, "Wednesday should NOT be weekend in friday_saturday mode"
        assert result.day_name == "Wednesday"
        assert result.day_of_week == 2
        assert result.weekend_type == "friday_saturday"


class TestWeekendCheckerInputTypes:
    """Test different input types for weekend checker"""

    @pytest.mark.asyncio
    async def test_string_date_input(self):
        """Test with string date input"""
        checker = get_weekend_checker()
        result = await checker.check("2025-12-25", "israeli")

        assert result.is_weekend is True
        assert result.day_name == "Thursday"

    def test_datetime_input_sync(self):
        """Test with datetime object input (synchronous)"""
        checker = get_weekend_checker()
        dt = datetime(2025, 12, 25)

        is_weekend = checker.is_weekend(dt, "israeli")
        assert is_weekend is True

    def test_date_input_sync(self):
        """Test with date object input (synchronous)"""
        checker = get_weekend_checker()
        d = date(2025, 12, 25)

        is_weekend = checker.is_weekend(d, "israeli")
        assert is_weekend is True

    def test_default_weekend_type(self):
        """Test that default weekend type is used when not specified"""
        checker = WeekendChecker(default_weekend_type="israeli")

        # Thursday should be weekend with Israeli default
        is_weekend = checker.is_weekend("2025-12-25")
        assert is_weekend is True

        # Create checker with Western default
        checker_western = WeekendChecker(default_weekend_type="western")

        # Thursday should NOT be weekend with Western default
        is_weekend = checker_western.is_weekend("2025-12-25")
        assert is_weekend is False

    def test_saturday_sunday_alias(self):
        """Test that saturday_sunday is alias for western"""
        checker = get_weekend_checker()

        # Test with both
        is_weekend_western = checker.is_weekend("2025-04-20", "western")
        is_weekend_sat_sun = checker.is_weekend("2025-04-20", "saturday_sunday")

        assert is_weekend_western == is_weekend_sat_sun
        assert is_weekend_western is True  # Sunday should be weekend


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
