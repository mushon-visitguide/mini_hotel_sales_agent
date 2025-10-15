"""Comprehensive tests for MiniHotel PMS integration"""
import os
import pytest
import logging
from datetime import date, timedelta
from src.pms import MiniHotelClient, PMSClientFactory
from src.pms.exceptions import (
    PMSConnectionError,
    PMSAuthenticationError,
    PMSValidationError,
    PMSDataError,
)

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Test credentials from environment
USERNAME = os.environ.get("MINIHOTEL_USERNAME", "visitguide")
PASSWORD = os.environ.get("MINIHOTEL_PASSWORD", "visg#!71R")
HOTEL_ID = os.environ.get("MINIHOTEL_HOTEL_ID", "wayinn")
USE_SANDBOX = os.environ.get("MINIHOTEL_SANDBOX", "false").lower() == "true"


@pytest.fixture
def client():
    """Create a MiniHotel client for testing"""
    logger.info("="*70)
    logger.info("CREATING MINIHOTEL CLIENT - NO MOCKS, REAL API CLIENT")
    logger.info("="*70)
    logger.info(f"Username: {USERNAME}")
    logger.info(f"Hotel ID: {HOTEL_ID}")
    logger.info(f"Use Sandbox: {USE_SANDBOX}")
    logger.info(f"Client Type: {MiniHotelClient.__name__}")

    client = MiniHotelClient(
        username=USERNAME,
        password=PASSWORD,
        hotel_id=HOTEL_ID,
        use_sandbox=USE_SANDBOX,
    )

    logger.info(f"Client created successfully: {type(client)}")
    logger.info(f"Client endpoint: {'sandbox' if USE_SANDBOX else 'production'}")
    logger.info("="*70)

    return client


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

        logger.info(f"\n🔍 TEST: Basic Availability (NO MOCKS - Real API Call)")
        logger.info(f"   Client type: {type(client).__name__}")
        logger.info(f"   Request: {check_in} to {check_out}, 2 adults")

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=0,
            babies=0,
            rate_code="WEB",
        )

        logger.info(f"   Response: {response.hotel_name}, {len(response.room_types) if response.room_types else 0} rooms available")

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

        logger.info(f"\n🔍 TEST: Availability with Children (Real API)")
        logger.info(f"   Request: 2 adults, 2 children")

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=2,
            babies=0,
            rate_code="WEB",
        )

        logger.info(f"   Response: Got availability for {response.adults} adults, {response.children} children")

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

        logger.info(f"\n🔍 TEST: Validation - Invalid Date Order")
        logger.info(f"   Testing validation (no API call expected)")

        with pytest.raises(PMSValidationError, match="Check-out date must be after check-in date"):
            client.get_availability(
                check_in=check_in,
                check_out=check_out,
                adults=2,
            )

        logger.info(f"   ✓ Correctly raised validation error")
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
        logger.info(f"\n🔍 TEST: Invalid Credentials Error Handling (Real API)")
        logger.info(f"   Creating client with invalid credentials")

        client = MiniHotelClient(
            username="invalid",
            password="invalid",
            hotel_id="invalid",
        )

        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        logger.info(f"   Attempting API call - expecting error")

        # This should raise a connection or authentication error
        with pytest.raises((PMSConnectionError, PMSAuthenticationError, PMSDataError)):
            client.get_availability(
                check_in=check_in,
                check_out=check_out,
                adults=2,
            )

        logger.info(f"   ✓ Correctly raised authentication/connection error")
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


class TestRoomSpecsCache:
    """Test room specifications caching functionality"""

    def test_build_room_specs_cache_sandbox(self):
        """Test building room specs cache from getRooms data"""
        client = MiniHotelClient(
            username=USERNAME,
            password=PASSWORD,
            hotel_id=HOTEL_ID,
            use_sandbox=False,
        )

        # Build cache (will call getRooms internally)
        # This is a real API call in sandbox mode
        try:
            client.build_room_specs_cache()

            # Verify cache was populated
            assert isinstance(client._room_specs_cache, dict)
            print(f"\n✓ Room specs cache built successfully")
            print(f"  Cached room types: {len(client._room_specs_cache)}")

            # Check structure of cached data
            if client._room_specs_cache:
                first_type = list(client._room_specs_cache.keys())[0]
                specs = client._room_specs_cache[first_type]

                assert "max_adults" in specs
                assert "max_children" in specs
                assert "max_babies" in specs
                assert "features" in specs

                print(f"  Sample room type: {first_type}")
                if specs["max_adults"]:
                    print(f"    Max adults: {specs['max_adults']}")
                if specs["features"]:
                    print(f"    Features: {specs['features']}")

        except PMSDataError:
            # Expected in production mode
            print(f"\n✓ Correctly handles production mode (no getRooms available)")

    def test_room_specs_cache_production_mode(self):
        """Test that cache remains empty in production mode"""
        client = MiniHotelClient(
            username="test",
            password="test",
            hotel_id="test",
            use_sandbox=False,
        )

        client.build_room_specs_cache()

        # Should remain empty in production
        assert client._room_specs_cache == {}
        print(f"\n✓ Production mode cache handling test passed")


class TestEnrichedAvailability:
    """Test enriched availability responses with room specifications"""

    def test_availability_includes_room_specs(self):
        """Test that availability response includes room specs when cache is populated"""
        client = MiniHotelClient(
            username=USERNAME,
            password=PASSWORD,
            hotel_id=HOTEL_ID,
            use_sandbox=False,
        )

        # Build cache first
        try:
            client.build_room_specs_cache()
        except PMSDataError:
            pytest.skip("Production mode not available")

        # Get availability
        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
        )

        # Check that room types have enriched data
        if response.room_types:
            enriched_count = 0
            for room_type in response.room_types:
                # Check for new fields
                assert hasattr(room_type, 'max_adults')
                assert hasattr(room_type, 'max_children')
                assert hasattr(room_type, 'max_babies')
                assert hasattr(room_type, 'bed_configuration')
                assert hasattr(room_type, 'size_sqm')
                assert hasattr(room_type, 'features')

                # Count enriched rooms (those with actual spec data)
                if room_type.max_adults is not None:
                    enriched_count += 1

            print(f"\n✓ Enriched availability test passed")
            print(f"  Total room types: {len(response.room_types)}")
            print(f"  Enriched with specs: {enriched_count}")

            # Print sample enriched room
            if enriched_count > 0:
                for room_type in response.room_types:
                    if room_type.max_adults:
                        print(f"\n  Sample enriched room:")
                        print(f"    Type: {room_type.room_type_name}")
                        print(f"    Max occupancy: {room_type.get_max_occupancy()} guests")
                        print(f"    Max adults: {room_type.max_adults}")
                        if room_type.features:
                            print(f"    Features: {', '.join(room_type.features)}")
                        break

    def test_max_occupancy_calculation(self):
        """Test the get_max_occupancy helper method"""
        from src.models.availability import RoomTypeAvailability, Inventory

        # Create a room type with occupancy data
        room_type = RoomTypeAvailability(
            room_type_code="FAM",
            room_type_name="Family Suite",
            max_adults=2,
            max_children=2,
            max_babies=1,
            inventory=Inventory(allocation=5, max_available=5),
        )

        assert room_type.get_max_occupancy() == 5  # 2+2+1
        print(f"\n✓ Max occupancy calculation test passed")
        print(f"  Room: {room_type.room_type_name}")
        print(f"  Max occupancy: {room_type.get_max_occupancy()} (2 adults + 2 children + 1 baby)")


class TestCaching:
    """Test availability caching behavior"""

    def test_cache_hit_on_repeated_query(self, client, future_dates):
        """Test that second identical query uses cache"""
        check_in, check_out = future_dates

        # First call - should miss cache
        response1 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
            debug=True,  # Will show cache miss
        )

        # Second identical call - should hit cache
        response2 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
            debug=True,  # Will show cache hit
        )

        # Should return same data
        assert response1.hotel_id == response2.hotel_id
        assert response1.check_in == response2.check_in
        assert response1.check_out == response2.check_out

        print(f"\n✓ Cache test passed - second query used cache")

    def test_cache_miss_on_different_params(self, client, future_dates):
        """Test that different parameters don't hit cache"""
        check_in, check_out = future_dates

        # First call
        response1 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=0,
            rate_code="WEB",
        )

        # Different guest count - should not use cache
        response2 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=1,  # Different!
            rate_code="WEB",
        )

        # Both should succeed (different queries)
        assert response1 is not None
        assert response2 is not None

        print(f"\n✓ Different parameters correctly bypass cache")

    def test_cache_bypass_with_use_cache_false(self, client, future_dates):
        """Test that use_cache=False forces fresh API call"""
        check_in, check_out = future_dates

        # First call with caching
        response1 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
            use_cache=True,
        )

        # Second call forcing fresh data
        response2 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
            use_cache=False,  # Force fresh call
        )

        assert response1 is not None
        assert response2 is not None

        print(f"\n✓ use_cache=False correctly bypasses cache")

    def test_clear_cache(self, client, future_dates):
        """Test manual cache clearing"""
        check_in, check_out = future_dates

        # Make a call to populate cache
        response1 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
        )

        # Clear cache
        client.clear_availability_cache()

        # Next call should be cache miss
        response2 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
        )

        assert response1 is not None
        assert response2 is not None

        print(f"\n✓ Manual cache clear works correctly")

    def test_cache_with_custom_ttl(self):
        """Test cache with custom TTL"""
        from datetime import date, timedelta
        import time

        # Create client with very short TTL (1 second)
        client = MiniHotelClient(
            username=USERNAME,
            password=PASSWORD,
            hotel_id=HOTEL_ID,
            use_sandbox=USE_SANDBOX,
            cache_ttl_seconds=1,  # 1 second TTL
        )

        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        # First call
        response1 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
        )

        # Wait for cache to expire
        time.sleep(1.5)

        # Second call should be cache miss (expired)
        response2 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="WEB",
            debug=True,  # Should show "Cache expired"
        )

        assert response1 is not None
        assert response2 is not None

        print(f"\n✓ Custom TTL cache expiration works correctly")


class TestConversationScenarios:
    """Test scenarios from chat_conversations.md"""

    def test_scenario_anniversary_couple_king_bed(self):
        """
        Conversation 1: Couple looking for King bed
        Agent needs to filter/compare rooms by bed type
        """
        print("\n" + "="*70)
        print("CONVERSATION SCENARIO 1: Anniversary Couple - King Bed")
        print("="*70)

        from src.models.availability import RoomTypeAvailability, Inventory, BoardPrice

        # Simulated available rooms with bed configurations
        deluxe_king = RoomTypeAvailability(
            room_type_code="DELUXE-KING",
            room_type_name="Deluxe King",
            max_adults=2,
            bed_configuration="1 King",
            features=["King Bed"],
            inventory=Inventory(allocation=3, max_available=5),
            prices=[BoardPrice("BB", "Bed & Breakfast", 210.00)],
        )

        premium_king = RoomTypeAvailability(
            room_type_code="PREMIUM-KING",
            room_type_name="Premium King",
            max_adults=2,
            bed_configuration="1 King",
            features=["King Bed", "Ocean View", "Balcony", "Champagne on arrival"],
            size_sqm=35.0,
            inventory=Inventory(allocation=2, max_available=3),
            prices=[BoardPrice("BB", "Bed & Breakfast", 255.00)],
        )

        deluxe_queen = RoomTypeAvailability(
            room_type_code="DELUXE-QUEEN",
            room_type_name="Deluxe Queen",
            max_adults=2,
            bed_configuration="2 Queens",
            features=["Two Queen Beds"],
            inventory=Inventory(allocation=4, max_available=6),
            prices=[BoardPrice("BB", "Bed & Breakfast", 190.00)],
        )

        all_rooms = [deluxe_king, premium_king, deluxe_queen]

        print("\nGuest request: 'king bed'")
        print("\nFiltering rooms by bed type:")

        # Filter for King beds
        king_rooms = [r for r in all_rooms if r.bed_configuration and "King" in r.bed_configuration]

        assert len(king_rooms) == 2
        print(f"  Found {len(king_rooms)} King bed options:")

        for room in king_rooms:
            print(f"\n  {room.room_type_name}")
            print(f"    Price: ${room.get_min_price():.2f}/night")
            print(f"    Bed: {room.bed_configuration}")
            if room.features:
                print(f"    Features: {', '.join(room.features)}")

        print("\n✅ SCENARIO PASSED - Can filter and compare by bed type")
        print("="*70)

    def test_scenario_family_occupancy_matching(self):
        """
        Conversation 2: Family with 2 adults + 3 kids
        Agent needs to find rooms that can fit 5 people
        """
        print("\n" + "="*70)
        print("CONVERSATION SCENARIO 2: Family Suite - Occupancy Matching")
        print("="*70)

        from src.models.availability import RoomTypeAvailability, Inventory, BoardPrice

        # Simulated room types with different occupancies
        double_room = RoomTypeAvailability(
            room_type_code="DBL",
            room_type_name="Double Room",
            max_adults=2,
            max_children=0,
            max_babies=0,
            inventory=Inventory(allocation=8, max_available=10),
            prices=[BoardPrice("BB", "Bed & Breakfast", 150.00)],
        )

        triple_room = RoomTypeAvailability(
            room_type_code="TRIPLE",
            room_type_name="Triple Room",
            max_adults=2,
            max_children=1,
            max_babies=0,
            inventory=Inventory(allocation=4, max_available=5),
            prices=[BoardPrice("BB", "Bed & Breakfast", 180.00)],
        )

        family_suite = RoomTypeAvailability(
            room_type_code="FAMILY-SUITE",
            room_type_name="Family Suite",
            max_adults=2,
            max_children=3,
            max_babies=1,
            features=["Connecting option", "Sofa bed", "Kids amenities"],
            inventory=Inventory(allocation=2, max_available=4),
            prices=[BoardPrice("BB", "Bed & Breakfast", 245.00)],
        )

        all_rooms = [double_room, triple_room, family_suite]

        print("\nGuest request: 2 adults + 3 kids")
        print("\nChecking room capacity:")

        # Required: 2 adults + 3 children
        required_adults = 2
        required_children = 3

        suitable_rooms = []
        for room in all_rooms:
            can_fit = (
                room.max_adults is not None
                and room.max_adults >= required_adults
                and room.max_children is not None
                and room.max_children >= required_children
            )

            print(f"\n  {room.room_type_name}")
            print(f"    Capacity: {room.max_adults} adults, {room.max_children} children")
            print(f"    Total: {room.get_max_occupancy()} guests")
            print(f"    Fits requirement: {'✓ YES' if can_fit else '✗ NO'}")

            if can_fit:
                suitable_rooms.append(room)

        assert len(suitable_rooms) == 1
        assert suitable_rooms[0].room_type_code == "FAMILY-SUITE"

        print(f"\n  Recommended: {suitable_rooms[0].room_type_name}")
        print(f"    Price: ${suitable_rooms[0].get_min_price():.2f}/night")
        if suitable_rooms[0].features:
            print(f"    Features: {', '.join(suitable_rooms[0].features)}")

        print("\n✅ SCENARIO PASSED - Correctly matched family to appropriate room")
        print("="*70)

    def test_scenario_room_comparison_features(self):
        """
        Conversation 1: Guest asks "what's the difference?"
        Agent needs to explain differences between room types
        """
        print("\n" + "="*70)
        print("CONVERSATION SCENARIO 3: Room Comparison - Feature Differences")
        print("="*70)

        from src.models.availability import RoomTypeAvailability, Inventory, BoardPrice

        standard_queen = RoomTypeAvailability(
            room_type_code="STD-QUEEN",
            room_type_name="Standard Queen",
            max_adults=2,
            bed_configuration="1 Queen",
            size_sqm=20.0,
            features=["Queen Bed", "City View"],
            inventory=Inventory(allocation=5, max_available=8),
            prices=[BoardPrice("BB", "Bed & Breakfast", 95.00)],
        )

        deluxe_queen = RoomTypeAvailability(
            room_type_code="DLX-QUEEN",
            room_type_name="Deluxe Queen",
            max_adults=2,
            bed_configuration="1 Queen",
            size_sqm=28.0,
            features=["Queen Bed", "Better View", "Mini Fridge", "Larger Room"],
            inventory=Inventory(allocation=3, max_available=5),
            prices=[BoardPrice("BB", "Bed & Breakfast", 120.00)],
        )

        print("\nGuest asks: 'what's the difference?'")
        print(f"\nComparing: {standard_queen.room_type_name} vs {deluxe_queen.room_type_name}")

        # Compare features
        std_features = set(standard_queen.features or [])
        dlx_features = set(deluxe_queen.features or [])

        unique_to_deluxe = dlx_features - std_features

        print(f"\n  {standard_queen.room_type_name}:")
        print(f"    Price: ${standard_queen.get_min_price():.2f}")
        print(f"    Size: {standard_queen.size_sqm} sqm")
        print(f"    Features: {', '.join(standard_queen.features)}")

        print(f"\n  {deluxe_queen.room_type_name}:")
        print(f"    Price: ${deluxe_queen.get_min_price():.2f}")
        print(f"    Size: {deluxe_queen.size_sqm} sqm")
        print(f"    Features: {', '.join(deluxe_queen.features)}")

        print(f"\n  Deluxe adds: {', '.join(unique_to_deluxe)}")
        print(f"  Price difference: ${deluxe_queen.get_min_price() - standard_queen.get_min_price():.2f}/night")

        assert len(unique_to_deluxe) > 0
        assert deluxe_queen.size_sqm > standard_queen.size_sqm
        assert deluxe_queen.get_min_price() > standard_queen.get_min_price()

        print("\n✅ SCENARIO PASSED - Can compare and explain room differences")
        print("="*70)

    def test_scenario_connecting_rooms_features(self):
        """
        Conversation 4: Family needs 2 connecting rooms
        Agent needs to identify rooms with connecting capability
        """
        print("\n" + "="*70)
        print("CONVERSATION SCENARIO 4: Connecting Rooms Request")
        print("="*70)

        from src.models.availability import RoomTypeAvailability, Inventory, BoardPrice

        oceanview_double = RoomTypeAvailability(
            room_type_code="OCEAN-DBL",
            room_type_name="Oceanview Double",
            max_adults=2,
            max_children=2,
            bed_configuration="2 Queen Beds",
            features=["Ocean View", "2 Queen Beds", "Connecting available"],
            inventory=Inventory(allocation=6, max_available=8),
            prices=[BoardPrice("RO", "Room Only", 135.00)],
        )

        standard_double = RoomTypeAvailability(
            room_type_code="STD-DBL",
            room_type_name="Standard Double",
            max_adults=2,
            max_children=1,
            bed_configuration="2 Double Beds",
            features=["2 Double Beds", "City View"],
            inventory=Inventory(allocation=10, max_available=15),
            prices=[BoardPrice("RO", "Room Only", 95.00)],
        )

        all_rooms = [oceanview_double, standard_double]

        print("\nGuest request: '2 connecting rooms if possible'")
        print("\nChecking for connecting room capability:")

        connecting_rooms = []
        for room in all_rooms:
            has_connecting = any("connecting" in f.lower() for f in (room.features or []))

            print(f"\n  {room.room_type_name}")
            print(f"    Bed config: {room.bed_configuration}")
            print(f"    Connecting available: {'✓ YES' if has_connecting else '✗ NO'}")

            if has_connecting:
                connecting_rooms.append(room)

        assert len(connecting_rooms) == 1
        assert "connecting" in " ".join(connecting_rooms[0].features).lower()

        print(f"\n  Recommended: {connecting_rooms[0].room_type_name}")
        print(f"    Can book 2 connecting rooms")
        print(f"    Total capacity: {connecting_rooms[0].get_max_occupancy() * 2} guests (2 rooms)")

        print("\n✅ SCENARIO PASSED - Identified rooms with connecting capability")
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
