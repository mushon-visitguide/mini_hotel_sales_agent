"""Comprehensive tests for MiniHotel PMS integration"""
import os
import pytest
from datetime import date, timedelta
from src.pms import MiniHotelClient, PMSClientFactory
from src.pms.exceptions import (
    PMSConnectionError,
    PMSAuthenticationError,
    PMSValidationError,
    PMSDataError,
)


# Test credentials from environment
USERNAME = os.environ.get("MINIHOTEL_USERNAME", "visitguide")
PASSWORD = os.environ.get("MINIHOTEL_PASSWORD", "visg#!71R")
HOTEL_ID = os.environ.get("MINIHOTEL_HOTEL_ID", "wayinn")
USE_SANDBOX = os.environ.get("MINIHOTEL_SANDBOX", "false").lower() == "true"


@pytest.fixture
def client():
    """Create a MiniHotel client for testing"""
    return MiniHotelClient(
        username=USERNAME,
        password=PASSWORD,
        hotel_id=HOTEL_ID,
        use_sandbox=USE_SANDBOX,
    )


@pytest.fixture
def future_dates():
    """Generate valid future check-in and check-out dates"""
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=2)
    return check_in, check_out


class TestClientCreation:
    """Test MiniHotel client creation and configuration"""

    def test_create_production_client(self):
        """Test creating a production client"""
        client = MiniHotelClient(
            username="test_user",
            password="test_pass",
            hotel_id="test_hotel",
            use_sandbox=False,
        )
        assert client.username == "test_user"
        assert client.password == "test_pass"
        assert client.hotel_id == "test_hotel"
        assert client.use_sandbox is False
        assert client.timeout == 30

    def test_create_sandbox_client(self):
        """Test creating a sandbox client"""
        client = MiniHotelClient(
            username="test_user",
            password="test_pass",
            hotel_id="test_hotel",
            use_sandbox=True,
        )
        assert client.use_sandbox is True

    def test_custom_timeout(self):
        """Test creating client with custom timeout"""
        client = MiniHotelClient(
            username="test_user",
            password="test_pass",
            hotel_id="test_hotel",
            timeout=60,
        )
        assert client.timeout == 60

    def test_supports_guest_count(self, client):
        """Test that MiniHotel supports guest count filtering"""
        assert client.supports_guest_count is True

    def test_supports_children_breakdown(self, client):
        """Test that MiniHotel supports children/babies breakdown"""
        assert client.supports_children_breakdown is True

    def test_factory_creation(self):
        """Test creating MiniHotel client via factory"""
        client = PMSClientFactory.create(
            "minihotel",
            username="test",
            password="test",
            hotel_id="test",
        )
        assert isinstance(client, MiniHotelClient)
        assert client.supports_guest_count is True
        assert client.supports_children_breakdown is True

    def test_factory_unknown_pms(self):
        """Test factory with unknown PMS type"""
        with pytest.raises(ValueError, match="Unknown PMS type"):
            PMSClientFactory.create(
                "unknown_pms",
                username="test",
                password="test",
                hotel_id="test",
            )


class TestGetAvailability:
    """Test get_availability endpoint"""

    def test_basic_availability(self, client, future_dates):
        """Test basic availability request with 2 adults"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=0,
            babies=0,
            rate_code="WEB",
        )

        # Verify basic response structure
        assert response.hotel_id == HOTEL_ID
        assert response.check_in == check_in
        assert response.check_out == check_out
        assert response.adults == 2
        assert response.children == 0
        assert response.babies == 0
        assert response.currency is not None
        assert response.hotel_name is not None

        print(f"\n✓ Basic availability test passed")
        print(f"  Hotel: {response.hotel_name}")
        print(f"  Currency: {response.currency}")
        print(f"  Available room types: {len(response.room_types) if response.room_types else 0}")

    def test_availability_with_children(self, client, future_dates):
        """Test availability request with adults and children"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=2,
            babies=0,
            rate_code="WEB",
        )

        assert response.adults == 2
        assert response.children == 2
        assert response.babies == 0

        print(f"\n✓ Availability with children test passed")
        print(f"  Guests: {response.adults} adults, {response.children} children")

    def test_availability_with_babies(self, client, future_dates):
        """Test availability request with babies"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=1,
            babies=1,
            rate_code="WEB",
        )

        assert response.adults == 2
        assert response.children == 1
        assert response.babies == 1

        print(f"\n✓ Availability with babies test passed")
        print(f"  Guests: {response.adults} adults, {response.children} children, {response.babies} babies")

    def test_availability_single_adult(self, client, future_dates):
        """Test availability for single adult"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=1,
            rate_code="WEB",
        )

        assert response.adults == 1
        print(f"\n✓ Single adult availability test passed")

    def test_availability_room_type_filter(self, client, future_dates):
        """Test availability with specific room type filter"""
        check_in, check_out = future_dates

        # First get all room types
        response_all = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
            room_type_filter="*ALL*",
        )

        # If we have room types, try filtering for a specific one
        if response_all.room_types and len(response_all.room_types) > 0:
            first_room_type = response_all.room_types[0].room_type_code

            response_filtered = client.get_availability(
                check_in=check_in,
                check_out=check_out,
                adults=2,
                rate_code="WEB",
                room_type_filter=first_room_type,
            )

            print(f"\n✓ Room type filter test passed")
            print(f"  Filtered for: {first_room_type}")
            if response_filtered.room_types:
                print(f"  Results: {len(response_filtered.room_types)} room type(s)")

    def test_availability_min_price(self, client, future_dates):
        """Test availability with minimum price filter"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
            room_type_filter="*MIN*",
        )

        print(f"\n✓ Minimum price filter test passed")

    def test_availability_board_filter(self, client, future_dates):
        """Test availability with board filter"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
            board_filter="*MIN*",
        )

        print(f"\n✓ Board filter test passed")

    def test_availability_longer_stay(self, client):
        """Test availability for a week-long stay"""
        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=7)

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
        )

        assert response.check_in == check_in
        assert response.check_out == check_out

        print(f"\n✓ Longer stay test passed")
        print(f"  Duration: {(check_out - check_in).days} nights")

    def test_availability_debug_mode(self, client, future_dates):
        """Test availability with debug mode enabled"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
            debug=True,
        )

        assert response is not None
        print(f"\n✓ Debug mode test passed")


class TestGetAvailabilityValidation:
    """Test validation for get_availability endpoint"""

    def test_invalid_dates_checkout_before_checkin(self, client):
        """Test that check-out before check-in raises error"""
        check_in = date.today() + timedelta(days=30)
        check_out = check_in - timedelta(days=1)

        with pytest.raises(PMSValidationError, match="Check-out date must be after check-in date"):
            client.get_availability(
                check_in=check_in,
                check_out=check_out,
                adults=2,
            )

        print(f"\n✓ Invalid dates validation test passed")

    def test_invalid_dates_same_day(self, client):
        """Test that same-day check-in/out raises error"""
        check_in = date.today() + timedelta(days=30)
        check_out = check_in

        with pytest.raises(PMSValidationError, match="Check-out date must be after check-in date"):
            client.get_availability(
                check_in=check_in,
                check_out=check_out,
                adults=2,
            )

        print(f"\n✓ Same-day validation test passed")

    def test_invalid_dates_past(self, client):
        """Test that past check-in date raises error"""
        check_in = date.today() - timedelta(days=1)
        check_out = check_in + timedelta(days=1)

        with pytest.raises(PMSValidationError, match="Check-in date cannot be in the past"):
            client.get_availability(
                check_in=check_in,
                check_out=check_out,
                adults=2,
            )

        print(f"\n✓ Past date validation test passed")

    def test_invalid_zero_adults(self, client, future_dates):
        """Test that zero adults raises error"""
        check_in, check_out = future_dates

        with pytest.raises(PMSValidationError, match="At least 1 adult is required"):
            client.get_availability(
                check_in=check_in,
                check_out=check_out,
                adults=0,
            )

        print(f"\n✓ Zero adults validation test passed")


class TestAvailabilityResponse:
    """Test availability response data structure"""

    def test_response_structure(self, client, future_dates):
        """Test that response has all expected fields"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
        )

        # Check all required fields
        assert hasattr(response, 'hotel_id')
        assert hasattr(response, 'hotel_name')
        assert hasattr(response, 'currency')
        assert hasattr(response, 'check_in')
        assert hasattr(response, 'check_out')
        assert hasattr(response, 'adults')
        assert hasattr(response, 'children')
        assert hasattr(response, 'babies')
        assert hasattr(response, 'room_types')

        print(f"\n✓ Response structure test passed")

    def test_room_type_availability_structure(self, client, future_dates):
        """Test room type availability structure"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
        )

        if response.room_types:
            room_type = response.room_types[0]

            assert hasattr(room_type, 'room_type_code')
            assert hasattr(room_type, 'room_type_name')
            assert hasattr(room_type, 'inventory')
            assert hasattr(room_type, 'prices')

            print(f"\n✓ Room type structure test passed")
            print(f"  Sample: {room_type.room_type_name}")

    def test_get_available_rooms_method(self, client, future_dates):
        """Test get_available_rooms helper method"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
        )

        available = response.get_available_rooms()

        assert isinstance(available, list)
        print(f"\n✓ Get available rooms method test passed")
        print(f"  Available rooms: {len(available)}")

    def test_min_price_method(self, client, future_dates):
        """Test get_min_price helper method on room types"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
        )

        if response.room_types:
            for room_type in response.room_types:
                min_price = room_type.get_min_price()

                if min_price is not None:
                    assert isinstance(min_price, (int, float))
                    assert min_price >= 0

            print(f"\n✓ Min price method test passed")

    def test_inventory_data(self, client, future_dates):
        """Test inventory data in response"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
        )

        has_inventory = False
        if response.room_types:
            for room_type in response.room_types:
                if room_type.inventory:
                    has_inventory = True
                    assert hasattr(room_type.inventory, 'allocation')
                    assert hasattr(room_type.inventory, 'max_available')
                    assert room_type.inventory.allocation >= 0
                    assert room_type.inventory.max_available >= 0

        print(f"\n✓ Inventory data test passed")
        print(f"  Has inventory: {has_inventory}")

    def test_price_data(self, client, future_dates):
        """Test price data in response"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
        )

        has_prices = False
        if response.room_types:
            for room_type in response.room_types:
                if room_type.prices:
                    has_prices = True
                    for price in room_type.prices:
                        assert hasattr(price, 'board_code')
                        assert hasattr(price, 'board_description')
                        assert hasattr(price, 'price')
                        assert price.price >= 0

        print(f"\n✓ Price data test passed")
        print(f"  Has prices: {has_prices}")


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_credentials(self):
        """Test authentication error with invalid credentials"""
        client = MiniHotelClient(
            username="invalid",
            password="invalid",
            hotel_id="invalid",
        )

        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        # This should raise a connection or authentication error
        with pytest.raises((PMSConnectionError, PMSAuthenticationError, PMSDataError)):
            client.get_availability(
                check_in=check_in,
                check_out=check_out,
                adults=2,
            )

        print(f"\n✓ Invalid credentials test passed")


class TestBookingLinkGeneration:
    """Test booking link generation"""

    def test_new_format_with_url_code(self):
        """Test new format booking link generation with url_code"""
        print("\n" + "="*70)
        print("TEST: New Format Booking Link (with url_code)")
        print("="*70)

        client = MiniHotelClient(
            username="test",
            password="test",
            hotel_id="test_hotel",
            url_code="wayinn123",
        )

        print(f"Client Configuration:")
        print(f"  - hotel_id: {client.hotel_id}")
        print(f"  - url_code: {client.url_code}")
        print(f"  - use_sandbox: {client.use_sandbox}")

        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        print(f"\nBooking Parameters:")
        print(f"  - Check-in: {check_in}")
        print(f"  - Check-out: {check_out}")
        print(f"  - Adults: 2")
        print(f"  - Children: 0")
        print(f"  - Room Type: PREMIUM-KING")

        link = client.generate_booking_link(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=0,
            room_type_code="PREMIUM-KING",
        )

        print(f"\nGenerated Link:")
        print(f"  {link}")

        # Format expected dates
        expected_from = check_in.strftime("%Y%m%d")
        expected_to = check_out.strftime("%Y%m%d")

        print(f"\nLink Components:")
        print(f"  ✓ Base URL: frame1.hotelpms.io")
        print(f"  ✓ URL Code: wayinn123")
        print(f"  ✓ Date Format: {expected_from} to {expected_to} (YYYYMMDD)")
        print(f"  ✓ Currency: ILS")
        print(f"  ✓ Language: en-US")
        print(f"  ✓ Room Type: PREMIUM-KING")
        print(f"  ✓ Rate Parameter: rp=d2Vi (base64 'web')")

        assert "frame1.hotelpms.io" in link
        assert "wayinn123" in link
        assert expected_from in link  # Date format YYYYMMDD
        assert expected_to in link
        assert "currency=ILS" in link
        assert "language=en-US" in link
        assert "roomType=PREMIUM-KING" in link
        assert "rp=d2Vi" in link  # base64 of "web"

        print(f"\n✅ TEST PASSED - New format booking link")
        print("="*70)

    def test_new_format_with_hebrew_language(self):
        """Test new format with Hebrew language"""
        print("\n" + "="*70)
        print("TEST: Hebrew Language Booking Link")
        print("="*70)

        client = MiniHotelClient(
            username="test",
            password="test",
            hotel_id="test_hotel",
            url_code="wayinn123",
        )

        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        print(f"Booking Parameters:")
        print(f"  - Language: he (Hebrew)")
        print(f"  - Adults: 2")

        link = client.generate_booking_link(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            language="he",
        )

        print(f"\nGenerated Link:")
        print(f"  {link}")

        print(f"\nLanguage Check:")
        print(f"  ✓ Hebrew detected, using language=he-IL")

        assert "language=he-IL" in link

        print(f"\n✅ TEST PASSED - Hebrew language")
        print("="*70)

    def test_old_format_without_url_code(self):
        """Test old format booking link generation without url_code"""
        print("\n" + "="*70)
        print("TEST: Old Format Booking Link (without url_code)")
        print("="*70)

        client = MiniHotelClient(
            username="test",
            password="test",
            hotel_id="wayinn",
        )

        print(f"Client Configuration:")
        print(f"  - hotel_id: {client.hotel_id}")
        print(f"  - url_code: {client.url_code} (None - using fallback format)")

        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        print(f"\nBooking Parameters:")
        print(f"  - Check-in: {check_in}")
        print(f"  - Check-out: {check_out}")
        print(f"  - Adults: 2")
        print(f"  - Children: 1")
        print(f"  - Babies: 1")
        print(f"  - Room Type: DELUXE")

        link = client.generate_booking_link(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=1,
            babies=1,
            room_type_code="DELUXE",
        )

        print(f"\nGenerated Link:")
        print(f"  {link}")

        # Format expected dates
        expected_checkin = check_in.strftime("%Y-%m-%d")
        expected_checkout = check_out.strftime("%Y-%m-%d")

        print(f"\nLink Components:")
        print(f"  ✓ Base URL: api.minihotel.cloud/gds")
        print(f"  ✓ Hotel ID: wayinn")
        print(f"  ✓ Date Format: {expected_checkin} to {expected_checkout} (YYYY-MM-DD)")
        print(f"  ✓ Adults: 2")
        print(f"  ✓ Children: 1")
        print(f"  ✓ Infants: 1")
        print(f"  ✓ Room Type: DELUXE")

        assert "api.minihotel.cloud/gds" in link
        assert "hotel=wayinn" in link
        assert f"checkin={expected_checkin}" in link
        assert f"checkout={expected_checkout}" in link
        assert "adults=2" in link
        assert "children=1" in link
        assert "infants=1" in link
        assert "room=DELUXE" in link

        print(f"\n✅ TEST PASSED - Old format booking link")
        print("="*70)

    def test_booking_link_validation(self):
        """Test booking link validation"""
        client = MiniHotelClient(
            username="test",
            password="test",
            hotel_id="test_hotel",
        )

        # Test past date validation
        check_in = date.today() - timedelta(days=1)
        check_out = check_in + timedelta(days=2)

        with pytest.raises(PMSValidationError, match="Check-in date cannot be in the past"):
            client.generate_booking_link(
                check_in=check_in,
                check_out=check_out,
                adults=2,
            )

        # Test invalid date order
        check_in = date.today() + timedelta(days=30)
        check_out = check_in - timedelta(days=1)

        with pytest.raises(PMSValidationError, match="Check-out date must be after check-in date"):
            client.generate_booking_link(
                check_in=check_in,
                check_out=check_out,
                adults=2,
            )

        # Test zero adults
        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        with pytest.raises(PMSValidationError, match="At least 1 adult is required"):
            client.generate_booking_link(
                check_in=check_in,
                check_out=check_out,
                adults=0,
            )

        print(f"\n✓ Booking link validation test passed")

    def test_booking_link_with_custom_currency(self):
        """Test booking link with custom currency"""
        print("\n" + "="*70)
        print("TEST: Custom Currency Booking Link")
        print("="*70)

        client = MiniHotelClient(
            username="test",
            password="test",
            hotel_id="test_hotel",
            url_code="wayinn123",
        )

        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        print(f"Booking Parameters:")
        print(f"  - Currency: USD (custom, not default ILS)")
        print(f"  - Adults: 2")

        link = client.generate_booking_link(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            currency="USD",
        )

        print(f"\nGenerated Link:")
        print(f"  {link}")

        print(f"\nCurrency Check:")
        print(f"  ✓ Custom currency USD applied")

        assert "currency=USD" in link

        print(f"\n✅ TEST PASSED - Custom currency")
        print("="*70)


# Convenience function for running tests manually
if __name__ == "__main__":
    print("MiniHotel PMS Integration - Comprehensive Test Suite")
    print("=" * 70)
    print("\nTo run all tests, use: pytest src/tests/test_minihotel.py -v")
    print("To run with output: pytest src/tests/test_minihotel.py -v -s")
    print("\nTo run specific test classes:")
    print("  pytest src/tests/test_minihotel.py::TestClientCreation -v")
    print("  pytest src/tests/test_minihotel.py::TestGetAvailability -v")
    print("  pytest src/tests/test_minihotel.py::TestGetAvailabilityValidation -v")
    print("  pytest src/tests/test_minihotel.py::TestAvailabilityResponse -v")
    print("  pytest src/tests/test_minihotel.py::TestBookingLinkGeneration -v")
    print("  pytest src/tests/test_minihotel.py::TestErrorHandling -v")
    print("\n" + "=" * 70)
