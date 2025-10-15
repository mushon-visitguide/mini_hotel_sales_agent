"""
Comprehensive tests for resolve_date_with_context
Tests the integrated tool that combines holiday resolution, fuzzy dates, and weekend checking
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from agent.tools.calendar.tools import resolve_date_with_context
from agent.tools.calendar.holiday_resolver import HolidayResolution
from agent.tools.calendar.date_resolver import DateResolution
from agent.tools.calendar.weekend_checker import WeekendCheckResult


class TestDateWithContextHolidays:
    """Test resolve_date_with_context with holiday inputs"""

    @pytest.mark.asyncio
    async def test_christmas_eve_2025(self):
        """
        Test 'Christmas Eve 2025'
        Expected: Dec 24, 2025 (Wednesday) - NOT a weekend
        Source: Christmas Eve is always Dec 24
        """
        # Mock holiday resolver to return Christmas Eve
        mock_holiday = HolidayResolution(
            holiday_name="Christmas Eve",
            start_date="2025-12-24",
            end_date="2025-12-24",
            duration_days=1,
            year=2025,
            holiday_type="christian"
        )

        with patch('agent.tools.calendar.tools.get_holiday_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_resolver.resolve.return_value = mock_holiday
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="Christmas Eve 2025",
                current_date="2025-11-01",
                check_holiday=True,
                weekend_type="israeli"
            )

            assert result['is_holiday'] is True
            assert result['check_in'] == "2025-12-24"
            assert result['check_out'] == "2025-12-24"
            assert result['nights'] == 1
            assert result['holiday_info']['holiday_name'] == "Christmas Eve"
            # Dec 24, 2025 is Wednesday - not Israeli weekend
            assert result['is_weekend'] is False

    @pytest.mark.asyncio
    async def test_hanukkah_2025_is_weekend(self):
        """
        Test '2 nights in Hanukkah 2025'
        Expected: Dec 14-21, 2025 - Check if start date is weekend
        Hanukkah starts Dec 14 (Sunday) - IS Western weekend
        """
        mock_holiday = HolidayResolution(
            holiday_name="Hanukkah",
            start_date="2025-12-14",
            end_date="2025-12-21",
            duration_days=8,
            year=2025,
            holiday_type="jewish"
        )

        with patch('agent.tools.calendar.tools.get_holiday_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_resolver.resolve.return_value = mock_holiday
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="2 nights in Hanukkah",
                current_date="2025-11-01",
                check_holiday=True,
                weekend_type="western"
            )

            assert result['is_holiday'] is True
            assert result['check_in'] == "2025-12-14"
            assert result['nights'] == 8
            assert result['holiday_info']['holiday_name'] == "Hanukkah"
            # Dec 14, 2025 is Sunday - IS Western weekend
            assert result['is_weekend'] is True

    @pytest.mark.asyncio
    async def test_passover_2025(self):
        """
        Test 'Passover 2025'
        Expected: April 12-19, 2025
        Check if April 13 is Israeli weekend
        """
        mock_holiday = HolidayResolution(
            holiday_name="Passover",
            start_date="2025-04-13",
            end_date="2025-04-20",
            duration_days=8,
            year=2025,
            holiday_type="jewish"
        )

        with patch('agent.tools.calendar.tools.get_holiday_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_resolver.resolve.return_value = mock_holiday
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="Passover",
                current_date="2025-03-01",
                check_holiday=True,
                weekend_type="israeli"
            )

            assert result['is_holiday'] is True
            assert result['check_in'] == "2025-04-13"
            assert result['nights'] == 8
            # April 13, 2025 is Sunday - not Israeli weekend (Thu-Sat)
            assert result['is_weekend'] is False

    @pytest.mark.asyncio
    async def test_easter_2025_is_sunday(self):
        """
        Test 'Easter 2025'
        Expected: April 20, 2025 (Sunday) - IS Western weekend
        """
        mock_holiday = HolidayResolution(
            holiday_name="Easter",
            start_date="2025-04-20",
            end_date="2025-04-23",
            duration_days=4,
            year=2025,
            holiday_type="christian"
        )

        with patch('agent.tools.calendar.tools.get_holiday_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_resolver.resolve.return_value = mock_holiday
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="Easter 2025",
                current_date="2025-03-01",
                check_holiday=True,
                weekend_type="western"
            )

            assert result['is_holiday'] is True
            assert result['check_in'] == "2025-04-20"
            # April 20, 2025 is Sunday - IS Western weekend
            assert result['is_weekend'] is True
            assert result['weekend_info']['day_name'] == "Sunday"

    @pytest.mark.asyncio
    async def test_thanksgiving_2025_thursday(self):
        """
        Test 'Thanksgiving 2025'
        Expected: November 27, 2025 (Thursday) - IS Israeli weekend
        """
        mock_holiday = HolidayResolution(
            holiday_name="Thanksgiving",
            start_date="2025-11-27",
            end_date="2025-11-30",
            duration_days=4,
            year=2025,
            holiday_type="christian"
        )

        with patch('agent.tools.calendar.tools.get_holiday_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_resolver.resolve.return_value = mock_holiday
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="Thanksgiving",
                current_date="2025-10-01",
                check_holiday=True,
                weekend_type="israeli"
            )

            assert result['is_holiday'] is True
            assert result['check_in'] == "2025-11-27"
            # November 27, 2025 is Thursday - IS Israeli weekend
            assert result['is_weekend'] is True
            assert result['weekend_info']['day_name'] == "Thursday"


class TestDateWithContextFuzzyDates:
    """Test resolve_date_with_context with fuzzy date inputs (no holidays)"""

    @pytest.mark.asyncio
    async def test_tomorrow_not_weekend(self):
        """
        Test 'tomorrow' from Tuesday Dec 23, 2025
        Expected: Wednesday Dec 24 - NOT weekend
        """
        with patch('agent.tools.calendar.tools.get_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_date_result = DateResolution(
                check_in="2025-12-24",
                check_out="2025-12-25",
                nights=1,
                reasoning="Tomorrow from Dec 23 is Dec 24"
            )
            mock_resolver.resolve.return_value = mock_date_result
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="tomorrow",
                current_date="2025-12-23",
                check_holiday=True,
                weekend_type="israeli"
            )

            assert result['is_holiday'] is False
            assert result['check_in'] == "2025-12-24"
            assert result['nights'] == 1
            # Dec 24 is Wednesday - not Israeli weekend
            assert result['is_weekend'] is False

    @pytest.mark.asyncio
    async def test_next_weekend_is_weekend(self):
        """
        Test 'next weekend' from Monday Dec 22, 2025
        Expected: Friday Dec 26 - IS Israeli weekend
        """
        with patch('agent.tools.calendar.tools.get_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_date_result = DateResolution(
                check_in="2025-12-26",
                check_out="2025-12-27",
                nights=1,
                reasoning="Next weekend is Friday Dec 26"
            )
            mock_resolver.resolve.return_value = mock_date_result
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="next weekend",
                current_date="2025-12-22",
                check_holiday=False,  # Disable holiday check
                weekend_type="israeli"
            )

            assert result['is_holiday'] is False
            assert result['check_in'] == "2025-12-26"
            # Dec 26 is Friday - IS Israeli weekend
            assert result['is_weekend'] is True
            assert result['weekend_info']['day_name'] == "Friday"

    @pytest.mark.asyncio
    async def test_2_of_august_weekend_check(self):
        """
        Test 'I want to reserve 2 of Aug' - check if it's weekend
        August 2, 2025 is Saturday - IS Western weekend
        """
        with patch('agent.tools.calendar.tools.get_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_date_result = DateResolution(
                check_in="2025-08-02",
                check_out="2025-08-03",
                nights=1,
                reasoning="August 2, 2025"
            )
            mock_resolver.resolve.return_value = mock_date_result
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="2 of August",
                current_date="2025-07-01",
                check_holiday=False,
                weekend_type="western"
            )

            assert result['is_holiday'] is False
            assert result['check_in'] == "2025-08-02"
            # August 2, 2025 is Saturday - IS Western weekend
            assert result['is_weekend'] is True
            assert result['weekend_info']['day_name'] == "Saturday"

    @pytest.mark.asyncio
    async def test_in_3_days_from_thursday(self):
        """
        Test 'in 3 days' from Thursday Dec 25, 2025
        Expected: Sunday Dec 28 - IS Western weekend, NOT Israeli weekend
        """
        with patch('agent.tools.calendar.tools.get_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_date_result = DateResolution(
                check_in="2025-12-28",
                check_out="2025-12-29",
                nights=1,
                reasoning="3 days from Dec 25 is Dec 28"
            )
            mock_resolver.resolve.return_value = mock_date_result
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="in 3 days",
                current_date="2025-12-25",
                check_holiday=False,
                weekend_type="western"
            )

            assert result['is_holiday'] is False
            assert result['check_in'] == "2025-12-28"
            # Dec 28 is Sunday - IS Western weekend
            assert result['is_weekend'] is True
            assert result['weekend_info']['day_name'] == "Sunday"

    @pytest.mark.asyncio
    async def test_first_of_january_weekday(self):
        """
        Test 'first of January 2026'
        Expected: January 1, 2026 (Thursday) - IS Israeli weekend, NOT Western
        """
        with patch('agent.tools.calendar.tools.get_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_date_result = DateResolution(
                check_in="2026-01-01",
                check_out="2026-01-02",
                nights=1,
                reasoning="First of January 2026"
            )
            mock_resolver.resolve.return_value = mock_date_result
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="first of January",
                current_date="2025-12-01",
                check_holiday=False,
                weekend_type="israeli"
            )

            assert result['is_holiday'] is False
            assert result['check_in'] == "2026-01-01"
            # Jan 1, 2026 is Thursday - IS Israeli weekend
            assert result['is_weekend'] is True
            assert result['weekend_info']['day_name'] == "Thursday"


class TestDateWithContextWeekendTypes:
    """Test different weekend type configurations"""

    @pytest.mark.asyncio
    async def test_friday_israeli_vs_western(self):
        """
        Test Friday detection with different weekend types
        Friday should be Israeli weekend but NOT Western weekend
        """
        # Test with Israeli weekend
        with patch('agent.tools.calendar.tools.get_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_date_result = DateResolution(
                check_in="2025-12-26",
                check_out="2025-12-27",
                nights=1,
                reasoning="Friday Dec 26"
            )
            mock_resolver.resolve.return_value = mock_date_result
            mock_get_resolver.return_value = mock_resolver

            result_israeli = await resolve_date_with_context(
                user_input="Friday December 26",
                current_date="2025-12-20",
                check_holiday=False,
                weekend_type="israeli"
            )

            result_western = await resolve_date_with_context(
                user_input="Friday December 26",
                current_date="2025-12-20",
                check_holiday=False,
                weekend_type="western"
            )

            # Friday IS Israeli weekend
            assert result_israeli['is_weekend'] is True
            # Friday is NOT Western weekend
            assert result_western['is_weekend'] is False

    @pytest.mark.asyncio
    async def test_sunday_israeli_vs_western(self):
        """
        Test Sunday detection with different weekend types
        Sunday should be Western weekend but NOT Israeli weekend
        """
        with patch('agent.tools.calendar.tools.get_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_date_result = DateResolution(
                check_in="2025-04-20",
                check_out="2025-04-21",
                nights=1,
                reasoning="Sunday April 20 (Easter)"
            )
            mock_resolver.resolve.return_value = mock_date_result
            mock_get_resolver.return_value = mock_resolver

            result_israeli = await resolve_date_with_context(
                user_input="Sunday April 20",
                current_date="2025-04-01",
                check_holiday=False,
                weekend_type="israeli"
            )

            result_western = await resolve_date_with_context(
                user_input="Sunday April 20",
                current_date="2025-04-01",
                check_holiday=False,
                weekend_type="western"
            )

            # Sunday is NOT Israeli weekend
            assert result_israeli['is_weekend'] is False
            # Sunday IS Western weekend
            assert result_western['is_weekend'] is True

    @pytest.mark.asyncio
    async def test_saturday_both_weekends(self):
        """
        Test Saturday - should be weekend for BOTH Israeli and Western
        """
        with patch('agent.tools.calendar.tools.get_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_date_result = DateResolution(
                check_in="2025-12-27",
                check_out="2025-12-28",
                nights=1,
                reasoning="Saturday Dec 27"
            )
            mock_resolver.resolve.return_value = mock_date_result
            mock_get_resolver.return_value = mock_resolver

            result_israeli = await resolve_date_with_context(
                user_input="Saturday December 27",
                current_date="2025-12-20",
                check_holiday=False,
                weekend_type="israeli"
            )

            result_western = await resolve_date_with_context(
                user_input="Saturday December 27",
                current_date="2025-12-20",
                check_holiday=False,
                weekend_type="western"
            )

            # Saturday IS weekend for both
            assert result_israeli['is_weekend'] is True
            assert result_western['is_weekend'] is True

    @pytest.mark.asyncio
    async def test_thursday_only_israeli_weekend(self):
        """
        Test Thursday - should be Israeli weekend ONLY
        """
        with patch('agent.tools.calendar.tools.get_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_date_result = DateResolution(
                check_in="2025-11-27",
                check_out="2025-11-28",
                nights=1,
                reasoning="Thursday Nov 27 (Thanksgiving)"
            )
            mock_resolver.resolve.return_value = mock_date_result
            mock_get_resolver.return_value = mock_resolver

            result_israeli = await resolve_date_with_context(
                user_input="Thursday November 27",
                current_date="2025-11-01",
                check_holiday=False,
                weekend_type="israeli"
            )

            result_western = await resolve_date_with_context(
                user_input="Thursday November 27",
                current_date="2025-11-01",
                check_holiday=False,
                weekend_type="western"
            )

            # Thursday IS Israeli weekend
            assert result_israeli['is_weekend'] is True
            # Thursday is NOT Western weekend
            assert result_western['is_weekend'] is False

    @pytest.mark.asyncio
    async def test_monday_neither_weekend(self):
        """
        Test Monday - should NOT be weekend for either type
        """
        with patch('agent.tools.calendar.tools.get_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_date_result = DateResolution(
                check_in="2025-12-29",
                check_out="2025-12-30",
                nights=1,
                reasoning="Monday Dec 29"
            )
            mock_resolver.resolve.return_value = mock_date_result
            mock_get_resolver.return_value = mock_resolver

            result_israeli = await resolve_date_with_context(
                user_input="Monday December 29",
                current_date="2025-12-20",
                check_holiday=False,
                weekend_type="israeli"
            )

            result_western = await resolve_date_with_context(
                user_input="Monday December 29",
                current_date="2025-12-20",
                check_holiday=False,
                weekend_type="western"
            )

            # Monday is NOT weekend for either
            assert result_israeli['is_weekend'] is False
            assert result_western['is_weekend'] is False


class TestDateWithContextDisableFeatures:
    """Test disabling specific features"""

    @pytest.mark.asyncio
    async def test_disable_holiday_check(self):
        """
        Test with check_holiday=False
        Should skip holiday detection even if holiday mentioned
        """
        with patch('agent.tools.calendar.tools.get_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_date_result = DateResolution(
                check_in="2025-12-25",
                check_out="2025-12-26",
                nights=1,
                reasoning="Resolved as regular date"
            )
            mock_resolver.resolve.return_value = mock_date_result
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="Christmas",  # Holiday keyword
                current_date="2025-11-01",
                check_holiday=False,  # Disable holiday check
                weekend_type="israeli"
            )

            # Should not detect as holiday
            assert result['is_holiday'] is False
            assert result['holiday_info'] is None
            # But should still check weekend
            assert 'is_weekend' in result

    @pytest.mark.asyncio
    async def test_hebrew_holiday_keyword(self):
        """
        Test Hebrew holiday keyword 'חנוכה' (Hanukkah)
        Should be detected as holiday
        """
        mock_holiday = HolidayResolution(
            holiday_name="Hanukkah",
            start_date="2025-12-14",
            end_date="2025-12-21",
            duration_days=8,
            year=2025,
            holiday_type="jewish"
        )

        with patch('agent.tools.calendar.tools.get_holiday_resolver') as mock_get_resolver:
            mock_resolver = AsyncMock()
            mock_resolver.resolve.return_value = mock_holiday
            mock_get_resolver.return_value = mock_resolver

            result = await resolve_date_with_context(
                user_input="חנוכה 2025",  # Hebrew
                current_date="2025-11-01",
                check_holiday=True,
                weekend_type="israeli"
            )

            assert result['is_holiday'] is True
            assert result['check_in'] == "2025-12-14"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
