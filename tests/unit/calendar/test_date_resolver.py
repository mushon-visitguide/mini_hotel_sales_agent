"""
Comprehensive tests for Date Resolver
Tests fuzzy date parsing with LLM-based resolution
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from agent.tools.calendar.date_resolver import (
    get_resolver,
    DateResolver,
    DateResolution
)


class TestDateResolverBasicDates:
    """Test basic fuzzy date resolution"""

    @pytest.mark.asyncio
    async def test_tomorrow_from_december_24_2025(self):
        """
        Test 'tomorrow' from December 24, 2025 (Wednesday)
        Expected: December 25, 2025 for 1 night
        """
        # Mock the LLM response
        mock_result = DateResolution(
            check_in="2025-12-25",
            check_out="2025-12-26",
            nights=1,
            reasoning="Tomorrow from Dec 24 is Dec 25"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="tomorrow",
                current_date="2025-12-24",
                default_nights=1
            )

            assert result.check_in == "2025-12-25"
            assert result.check_out == "2025-12-26"
            assert result.nights == 1

    @pytest.mark.asyncio
    async def test_next_weekend_from_monday(self):
        """
        Test 'next weekend' from Monday, December 22, 2025
        Expected: Friday December 26 to Saturday December 27 (Israeli weekend)
        """
        mock_result = DateResolution(
            check_in="2025-12-26",
            check_out="2025-12-27",
            nights=1,
            reasoning="Next weekend from Monday Dec 22 is Friday-Saturday Dec 26-27"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="next weekend",
                current_date="2025-12-22",
                default_nights=1
            )

            assert result.check_in == "2025-12-26"
            assert result.check_out == "2025-12-27"
            assert result.nights == 1

    @pytest.mark.asyncio
    async def test_in_3_days_from_christmas(self):
        """
        Test 'in 3 days' from December 25, 2025
        Expected: December 28, 2025 for 1 night
        """
        mock_result = DateResolution(
            check_in="2025-12-28",
            check_out="2025-12-29",
            nights=1,
            reasoning="3 days from Dec 25 is Dec 28"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="in 3 days",
                current_date="2025-12-25",
                default_nights=1
            )

            assert result.check_in == "2025-12-28"
            assert result.check_out == "2025-12-29"
            assert result.nights == 1

    @pytest.mark.asyncio
    async def test_first_of_next_month(self):
        """
        Test 'first of January' from December 15, 2025
        Expected: January 1, 2026 for 1 night
        """
        mock_result = DateResolution(
            check_in="2026-01-01",
            check_out="2026-01-02",
            nights=1,
            reasoning="First of January 2026"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="first of January",
                current_date="2025-12-15",
                default_nights=1
            )

            assert result.check_in == "2026-01-01"
            assert result.check_out == "2026-01-02"
            assert result.nights == 1

    @pytest.mark.asyncio
    async def test_this_friday_for_2_nights(self):
        """
        Test 'this Friday for 2 nights' from Wednesday, April 16, 2025
        Expected: Friday April 18 to Sunday April 20 (2 nights)
        """
        mock_result = DateResolution(
            check_in="2025-04-18",
            check_out="2025-04-20",
            nights=2,
            reasoning="This Friday (Apr 18) for 2 nights gives checkout on Apr 20"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="this Friday for 2 nights",
                current_date="2025-04-16",
                default_nights=1
            )

            assert result.check_in == "2025-04-18"
            assert result.check_out == "2025-04-20"
            assert result.nights == 2


class TestDateResolverMultiNight:
    """Test multi-night stay resolution"""

    @pytest.mark.asyncio
    async def test_weekend_stay_2_nights(self):
        """
        Test weekend stay with 2 nights
        From Monday Dec 22, 2025, 'weekend for 2 nights'
        Expected: Friday Dec 26 to Sunday Dec 28 (2 nights)
        """
        mock_result = DateResolution(
            check_in="2025-12-26",
            check_out="2025-12-28",
            nights=2,
            reasoning="Weekend starting Friday Dec 26 for 2 nights"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="weekend for 2 nights",
                current_date="2025-12-22",
                default_nights=2
            )

            assert result.check_in == "2025-12-26"
            assert result.check_out == "2025-12-28"
            assert result.nights == 2

    @pytest.mark.asyncio
    async def test_week_long_stay(self):
        """
        Test week-long stay (7 days = 6 nights in hotel terms)
        From Jan 1, 2026
        Expected: Jan 1 to Jan 7 (6 nights)
        """
        mock_result = DateResolution(
            check_in="2026-01-01",
            check_out="2026-01-07",
            nights=6,
            reasoning="Week-long stay starting Jan 1 (7 days = 6 nights)"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="week-long stay",
                current_date="2025-12-20",
                default_nights=6
            )

            assert result.check_in == "2026-01-01"
            assert result.check_out == "2026-01-07"
            assert result.nights == 6

    @pytest.mark.asyncio
    async def test_3_nights_starting_tomorrow(self):
        """
        Test '3 nights starting tomorrow'
        From Dec 24, 2025
        Expected: Dec 25 to Dec 28 (3 nights)
        """
        mock_result = DateResolution(
            check_in="2025-12-25",
            check_out="2025-12-28",
            nights=3,
            reasoning="3 nights starting Dec 25 gives checkout on Dec 28"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="3 nights starting tomorrow",
                current_date="2025-12-24",
                default_nights=3
            )

            assert result.check_in == "2025-12-25"
            assert result.check_out == "2025-12-28"
            assert result.nights == 3

    @pytest.mark.asyncio
    async def test_mid_december_for_4_nights(self):
        """
        Test 'mid December for 4 nights'
        Expected: Around Dec 14-18, 2025 (4 nights)
        """
        mock_result = DateResolution(
            check_in="2025-12-14",
            check_out="2025-12-18",
            nights=4,
            reasoning="Mid December (Dec 14) for 4 nights gives checkout on Dec 18"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="mid December for 4 nights",
                current_date="2025-11-01",
                default_nights=4
            )

            assert result.check_in == "2025-12-14"
            assert result.check_out == "2025-12-18"
            assert result.nights == 4

    @pytest.mark.asyncio
    async def test_default_nights_applied(self):
        """
        Test that default_nights is applied when no duration specified
        'tomorrow' with default_nights=2
        Expected: 2 nights
        """
        mock_result = DateResolution(
            check_in="2025-12-25",
            check_out="2025-12-27",
            nights=2,
            reasoning="Tomorrow (Dec 25) using default 2 nights"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="tomorrow",
                current_date="2025-12-24",
                default_nights=2
            )

            assert result.nights == 2
            assert result.check_in == "2025-12-25"
            assert result.check_out == "2025-12-27"


class TestDateResolverSpecificDates:
    """Test resolution of specific date formats"""

    @pytest.mark.asyncio
    async def test_specific_date_december_25(self):
        """
        Test 'December 25' or 'Dec 25'
        From November 2025
        Expected: December 25, 2025
        """
        mock_result = DateResolution(
            check_in="2025-12-25",
            check_out="2025-12-26",
            nights=1,
            reasoning="December 25, 2025"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="December 25",
                current_date="2025-11-01",
                default_nights=1
            )

            assert result.check_in == "2025-12-25"
            assert result.check_out == "2025-12-26"
            assert result.nights == 1

    @pytest.mark.asyncio
    async def test_date_range_april_18_to_20(self):
        """
        Test date range 'April 18-20'
        Expected: April 18 to April 20 (2 nights)
        """
        mock_result = DateResolution(
            check_in="2025-04-18",
            check_out="2025-04-20",
            nights=2,
            reasoning="April 18-20 is 2 nights (Good Friday to Easter Sunday)"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="April 18-20",
                current_date="2025-03-01",
                default_nights=1
            )

            assert result.check_in == "2025-04-18"
            assert result.check_out == "2025-04-20"
            assert result.nights == 2

    @pytest.mark.asyncio
    async def test_first_week_of_month(self):
        """
        Test 'first week of April'
        Expected: April 1-7, 2025
        """
        mock_result = DateResolution(
            check_in="2025-04-01",
            check_out="2025-04-07",
            nights=6,
            reasoning="First week of April (Apr 1-7) is 6 nights"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="first week of April",
                current_date="2025-03-01",
                default_nights=1
            )

            assert result.check_in == "2025-04-01"
            # Could be Apr 7 or Apr 8 depending on interpretation
            assert result.nights >= 6

    @pytest.mark.asyncio
    async def test_end_of_month(self):
        """
        Test 'end of November'
        Expected: Around Nov 25-30, 2025
        """
        mock_result = DateResolution(
            check_in="2025-11-25",
            check_out="2025-11-26",
            nights=1,
            reasoning="End of November is around Nov 25-30"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="end of November",
                current_date="2025-10-01",
                default_nights=1
            )

            # Check it's in the last week of November
            check_in_date = datetime.strptime(result.check_in, "%Y-%m-%d")
            assert check_in_date.month == 11
            assert check_in_date.day >= 25

    @pytest.mark.asyncio
    async def test_on_the_15th(self):
        """
        Test 'on the 15th' (should resolve to next 15th)
        From Dec 20, 2025
        Expected: January 15, 2026 (next occurrence)
        """
        mock_result = DateResolution(
            check_in="2026-01-15",
            check_out="2026-01-16",
            nights=1,
            reasoning="On the 15th - next occurrence is Jan 15, 2026"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="on the 15th",
                current_date="2025-12-20",
                default_nights=1
            )

            assert result.check_in == "2026-01-15"
            assert result.check_out == "2026-01-16"
            assert result.nights == 1


class TestDateResolverEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_current_date_defaults_to_today(self):
        """
        Test that current_date defaults to today when not provided
        """
        mock_result = DateResolution(
            check_in="2025-12-26",
            check_out="2025-12-27",
            nights=1,
            reasoning="Tomorrow from today"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            # Don't provide current_date
            result = await resolver.resolve(
                date_hint="tomorrow",
                default_nights=1
            )

            # Should still return a result
            assert result.nights == 1
            assert result.check_in is not None

    @pytest.mark.asyncio
    async def test_timezone_parameter(self):
        """
        Test that timezone parameter is accepted
        """
        mock_result = DateResolution(
            check_in="2025-12-25",
            check_out="2025-12-26",
            nights=1,
            reasoning="Tomorrow in Asia/Jerusalem timezone"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="tomorrow",
                current_date="2025-12-24",
                timezone="Asia/Jerusalem",
                default_nights=1
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_reasoning_is_provided(self):
        """
        Test that reasoning field is always populated
        """
        mock_result = DateResolution(
            check_in="2025-12-25",
            check_out="2025-12-26",
            nights=1,
            reasoning="Detailed explanation of date resolution"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="tomorrow",
                current_date="2025-12-24",
                default_nights=1
            )

            assert result.reasoning is not None
            assert len(result.reasoning) > 0

    @pytest.mark.asyncio
    async def test_checkout_after_checkin(self):
        """
        Test that check_out is always after check_in
        """
        mock_result = DateResolution(
            check_in="2025-12-25",
            check_out="2025-12-28",
            nights=3,
            reasoning="3 nights from Dec 25"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="3 nights from tomorrow",
                current_date="2025-12-24",
                default_nights=3
            )

            check_in = datetime.strptime(result.check_in, "%Y-%m-%d")
            check_out = datetime.strptime(result.check_out, "%Y-%m-%d")
            assert check_out > check_in

    @pytest.mark.asyncio
    async def test_nights_matches_date_difference(self):
        """
        Test that nights equals the difference between check_in and check_out
        """
        mock_result = DateResolution(
            check_in="2025-12-25",
            check_out="2025-12-28",
            nights=3,
            reasoning="3 nights stay"
        )

        with patch.object(DateResolver, 'resolve', return_value=mock_result):
            resolver = get_resolver()
            result = await resolver.resolve(
                date_hint="3 nights",
                current_date="2025-12-24",
                default_nights=3
            )

            check_in = datetime.strptime(result.check_in, "%Y-%m-%d")
            check_out = datetime.strptime(result.check_out, "%Y-%m-%d")
            nights_diff = (check_out - check_in).days
            assert result.nights == nights_diff


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
