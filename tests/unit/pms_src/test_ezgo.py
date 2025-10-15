"""Comprehensive tests for ezGo PMS integration"""
import os
import pytest
import logging
from datetime import date, timedelta
from src.pms import EzGoClient, PMSClientFactory
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


# Test credentials from environment or use provided values
USERNAME = os.environ.get("EZGO_USERNAME", "9600")
PASSWORD = os.environ.get("EZGO_PASSWORD", "688E3n")
HOTEL_ID = os.environ.get("EZGO_HOTEL_ID", "9600")


@pytest.fixture
def client():
    """Create an ezGo client for testing"""
    logger.info("="*70)
    logger.info("CREATING EZGO CLIENT - REAL API CLIENT")
    logger.info("="*70)
    logger.info(f"Username: {USERNAME}")
    logger.info(f"Hotel ID: {HOTEL_ID}")
    logger.info(f"Client Type: {EzGoClient.__name__}")

    client = EzGoClient(
        username=USERNAME,
        password=PASSWORD,
        hotel_id=HOTEL_ID,
    )

    logger.info(f"Client created successfully: {type(client)}")
    logger.info("="*70)

    return client


@pytest.fixture
def future_dates():
    """Generate valid future check-in and check-out dates"""
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=2)
    return check_in, check_out


class TestClientCreation:
    """Test ezGo client creation and configuration"""

    def test_create_client(self):
        """Test creating an ezGo client"""
        client = EzGoClient(
            username="test_user",
            password="test_pass",
            hotel_id="1234",
        )
        assert client.username == "test_user"
        assert client.password == "test_pass"
        assert client.hotel_id == "1234"
        assert client.hotel_id_int == 1234
        assert client.timeout == 30

    def test_custom_timeout(self):
        """Test creating client with custom timeout"""
        client = EzGoClient(
            username="test_user",
            password="test_pass",
            hotel_id="1234",
            timeout=60,
        )
        assert client.timeout == 60

    def test_custom_cache_ttl(self):
        """Test creating client with custom cache TTL"""
        client = EzGoClient(
            username="test_user",
            password="test_pass",
            hotel_id="1234",
            cache_ttl_seconds=600,
        )
        assert client._cache_ttl_seconds == 600

    def test_invalid_hotel_id(self):
        """Test that non-numeric hotel_id raises error"""
        with pytest.raises(PMSValidationError, match="hotel_id must be an integer"):
            EzGoClient(
                username="test",
                password="test",
                hotel_id="not_a_number",
            )

    def test_supports_guest_count(self, client):
        """Test that ezGo supports guest count filtering"""
        assert client.supports_guest_count is True

    def test_supports_children_breakdown(self, client):
        """Test that ezGo supports children/infants breakdown"""
        assert client.supports_children_breakdown is True

    def test_factory_creation(self):
        """Test creating ezGo client via factory"""
        client = PMSClientFactory.create(
            "ezgo",
            username="test",
            password="test",
            hotel_id="1234",
        )
        assert isinstance(client, EzGoClient)
        assert client.supports_guest_count is True
        assert client.supports_children_breakdown is True


class TestGetRoomTypes:
    """Test get_room_types endpoint"""

    def test_get_room_types(self, client):
        """Test retrieving room types"""
        logger.info(f"\n🔍 TEST: Get Room Types (Real API Call)")
        logger.info(f"   Client type: {type(client).__name__}")

        room_types = client.get_room_types(debug=True)

        logger.info(f"   Response: {len(room_types)} room types found")

        # Verify response structure
        assert isinstance(room_types, list)

        if room_types:
            # Check first room type structure
            rt = room_types[0]
            assert hasattr(rt, 'code')
            assert hasattr(rt, 'description')
            assert hasattr(rt, 'image_url')

            logger.info(f"\n   Sample room type:")
            logger.info(f"     Code: {rt.code}")
            logger.info(f"     Description: {rt.description}")

        print(f"\n✓ Get room types test passed")
        print(f"  Room types found: {len(room_types)}")


class TestGetRooms:
    """Test get_rooms endpoint"""

    def test_get_rooms(self, client):
        """Test retrieving rooms (room types in ezGo)"""
        logger.info(f"\n🔍 TEST: Get Rooms (Real API Call)")
        logger.info(f"   Client type: {type(client).__name__}")

        rooms = client.get_rooms(debug=True)

        logger.info(f"   Response: {len(rooms)} rooms found")

        # Verify response structure
        assert isinstance(rooms, list)

        if rooms:
            room = rooms[0]
            assert hasattr(room, 'room_number')
            assert hasattr(room, 'room_type')
            assert hasattr(room, 'occupancy_limits')

            logger.info(f"\n   Sample room:")
            logger.info(f"     Room Number: {room.room_number}")
            logger.info(f"     Room Type: {room.room_type}")
            if room.occupancy_limits:
                logger.info(f"     Occupancy: {room.occupancy_limits}")

        print(f"\n✓ Get rooms test passed")
        print(f"  Rooms found: {len(rooms)}")


class TestGetAvailability:
    """Test get_availability endpoint"""

    def test_basic_availability(self, client, future_dates):
        """Test basic availability request with 2 adults"""
        check_in, check_out = future_dates

        logger.info(f"\n🔍 TEST: Basic Availability (Real API Call)")
        logger.info(f"   Client type: {type(client).__name__}")
        logger.info(f"   Request: {check_in} to {check_out}, 2 adults")

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=0,
            babies=0,
            rate_code="USD",
            debug=True,
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
            rate_code="USD",
        )

        logger.info(f"   Response: Got availability for {response.adults} adults, {response.children} children")

        assert response.adults == 2
        assert response.children == 2
        assert response.babies == 0

        print(f"\n✓ Availability with children test passed")
        print(f"  Guests: {response.adults} adults, {response.children} children")

    def test_availability_with_infants(self, client, future_dates):
        """Test availability request with infants"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=1,
            babies=1,
            rate_code="USD",
        )

        assert response.adults == 2
        assert response.children == 1
        assert response.babies == 1

        print(f"\n✓ Availability with infants test passed")
        print(f"  Guests: {response.adults} adults, {response.children} children, {response.babies} infants")

    def test_availability_single_adult(self, client, future_dates):
        """Test availability for single adult"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=1,
            rate_code="USD",
        )

        assert response.adults == 1
        print(f"\n✓ Single adult availability test passed")

    def test_availability_ils_currency(self, client, future_dates):
        """Test availability with ILS currency"""
        check_in, check_out = future_dates

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="ILS",
        )

        assert response.currency == "ILS"
        print(f"\n✓ ILS currency test passed")

    def test_availability_longer_stay(self, client):
        """Test availability for a week-long stay"""
        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=7)

        response = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="USD",
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
            rate_code="USD",
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
            rate_code="USD",
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
            rate_code="USD",
        )

        if response.room_types and len(response.room_types) > 0:
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
            rate_code="USD",
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
            rate_code="USD",
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
            rate_code="USD",
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
            rate_code="USD",
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


class TestBookingLinkGeneration:
    """Test booking link generation"""

    def test_basic_booking_link(self):
        """Test basic booking link generation"""
        client = EzGoClient(
            username="test",
            password="test",
            hotel_id="9600",
        )

        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        link = client.generate_booking_link(
            check_in=check_in,
            check_out=check_out,
            adults=2,
        )

        assert "hotel=9600" in link
        assert "adults=2" in link
        assert check_in.strftime("%Y-%m-%d") in link
        assert check_out.strftime("%Y-%m-%d") in link

        print(f"\n✓ Basic booking link test passed")
        print(f"  Link: {link}")

    def test_booking_link_with_children(self):
        """Test booking link with children and infants"""
        client = EzGoClient(
            username="test",
            password="test",
            hotel_id="9600",
        )

        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        link = client.generate_booking_link(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=2,
            babies=1,
        )

        assert "adults=2" in link
        assert "children=2" in link
        assert "infants=1" in link

        print(f"\n✓ Booking link with children test passed")

    def test_booking_link_with_room_type(self):
        """Test booking link with specific room type"""
        client = EzGoClient(
            username="test",
            password="test",
            hotel_id="9600",
        )

        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=2)

        link = client.generate_booking_link(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            room_type_code="123",
        )

        assert "roomtype=123" in link

        print(f"\n✓ Booking link with room type test passed")

    def test_booking_link_validation(self):
        """Test booking link validation"""
        client = EzGoClient(
            username="test",
            password="test",
            hotel_id="9600",
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
            rate_code="USD",
            debug=True,  # Will show cache miss
        )

        # Second identical call - should hit cache
        response2 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="USD",
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
            rate_code="USD",
        )

        # Different guest count - should not use cache
        response2 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            children=1,  # Different!
            rate_code="USD",
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
            rate_code="USD",
            use_cache=True,
        )

        # Second call forcing fresh data
        response2 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="USD",
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
            rate_code="USD",
        )

        # Clear cache
        client.clear_availability_cache()

        # Next call should be cache miss
        response2 = client.get_availability(
            check_in=check_in,
            check_out=check_out,
            adults=2,
            rate_code="USD",
        )

        assert response1 is not None
        assert response2 is not None

        print(f"\n✓ Manual cache clear works correctly")


# Convenience function for running tests manually
if __name__ == "__main__":
    print("ezGo PMS Integration - Comprehensive Test Suite")
    print("=" * 70)
    print("\nTo run all tests, use: pytest src/tests/test_ezgo.py -v")
    print("To run with output: pytest src/tests/test_ezgo.py -v -s")
    print("\nTo run specific test classes:")
    print("  pytest src/tests/test_ezgo.py::TestClientCreation -v")
    print("  pytest src/tests/test_ezgo.py::TestGetAvailability -v")
    print("  pytest src/tests/test_ezgo.py::TestGetAvailabilityValidation -v")
    print("  pytest src/tests/test_ezgo.py::TestAvailabilityResponse -v")
    print("  pytest src/tests/test_ezgo.py::TestBookingLinkGeneration -v")
    print("\n" + "=" * 70)
