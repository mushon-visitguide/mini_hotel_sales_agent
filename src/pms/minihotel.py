"""MiniHotel PMS implementation"""
import requests
import xml.etree.ElementTree as ET
from datetime import date
from typing import List, Optional
from .base import PMSClient
from .exceptions import (
    PMSConnectionError,
    PMSAuthenticationError,
    PMSValidationError,
    PMSDataError,
)
from ..models.room import RoomType, Room, GuestOccupancy, RoomAttribute
from ..models.availability import (
    AvailabilityResponse,
    RoomTypeAvailability,
    Inventory,
    BoardPrice,
)


def _is_hebrew_language(language: str) -> bool:
    """Check if the language is Hebrew."""
    hebrew_codes = ["he", "heb", "hebrew", "iw", "he-IL"]
    return language.lower() in [code.lower() for code in hebrew_codes]


class MiniHotelClient(PMSClient):
    """
    MiniHotel PMS implementation.

    Supports:
    - Guest count filtering (adults, children, babies)
    - Multiple rate codes and board codes
    - Static data (room types, rooms)
    - Real-time availability and pricing
    """

    # Endpoints
    SANDBOX_ENDPOINT = "https://sandbox.minihotel.cloud/agents/ws/settings/rooms/RoomsMain.asmx"
    PRODUCTION_ENDPOINT = "https://api.minihotel.cloud/gds"

    def __init__(
        self,
        username: str,
        password: str,
        hotel_id: str,
        use_sandbox: bool = False,
        timeout: int = 30,
        url_code: Optional[str] = None,
        cache_ttl_seconds: int = 300,
    ):
        """
        Initialize MiniHotel client.

        Args:
            username: MiniHotel API username
            password: MiniHotel API password
            hotel_id: Hotel ID in MiniHotel system
            use_sandbox: If True, use sandbox endpoint (default: False)
            timeout: Request timeout in seconds (default: 30)
            url_code: Optional URL code for new booking frame format
            cache_ttl_seconds: Cache TTL for availability (default: 300 = 5 minutes)
        """
        super().__init__(username, password, hotel_id, cache_ttl_seconds)
        self.use_sandbox = use_sandbox
        self.timeout = timeout
        self.url_code = url_code
        # Cache for room type specifications (derived from getRooms)
        self._room_specs_cache = {}

    @property
    def supports_guest_count(self) -> bool:
        """MiniHotel supports guest count filtering"""
        return True

    @property
    def supports_children_breakdown(self) -> bool:
        """MiniHotel distinguishes children and babies"""
        return True

    def _get_endpoint(self, endpoint_type: str = "availability") -> str:
        """Get the appropriate endpoint URL"""
        if self.use_sandbox:
            return f"{self.SANDBOX_ENDPOINT}/{endpoint_type}"
        return self.PRODUCTION_ENDPOINT

    def _make_request(self, xml_request: str, endpoint_type: str = "availability", debug: bool = False) -> str:
        """
        Make HTTP request to MiniHotel API.

        Args:
            xml_request: XML request body
            endpoint_type: Type of endpoint for sandbox mode
            debug: If True, print debug information

        Returns:
            XML response as string

        Raises:
            PMSConnectionError: If unable to connect
            PMSAuthenticationError: If authentication fails
        """
        endpoint = self._get_endpoint(endpoint_type)

        if debug:
            print(f"\n[DEBUG] Request to: {endpoint}")
            print(f"[DEBUG] Request XML:\n{xml_request}\n")

        try:
            response = requests.post(
                endpoint,
                data=xml_request,
                headers={"Content-Type": "application/xml"},
                timeout=self.timeout,
            )

            if debug:
                print(f"[DEBUG] Status Code: {response.status_code}")
                print(f"[DEBUG] Response (first 500 chars):\n{response.text[:500]}\n")

            response.raise_for_status()
            return response.text

        except requests.exceptions.Timeout:
            raise PMSConnectionError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise PMSConnectionError(f"Unable to connect to MiniHotel API: {e}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise PMSAuthenticationError("Invalid credentials")
            raise PMSConnectionError(f"HTTP error: {e}")
        except Exception as e:
            raise PMSConnectionError(f"Unexpected error: {e}")

    def get_room_types(self, debug: bool = False) -> List[RoomType]:
        """
        Retrieve all room types from MiniHotel.

        Note: Only works in sandbox mode. Production should extract room types
        from availability responses.

        Args:
            debug: If True, print debug information

        Returns:
            List of RoomType objects

        Raises:
            PMSConnectionError: If unable to connect
            PMSDataError: If response is invalid
        """
        if not self.use_sandbox:
            raise PMSDataError("get_room_types is only available in sandbox mode. Use get_availability to get room types in production.")

        xml_request = f'''<?xml version="1.0" encoding="UTF-8"?>
<Request>
    <Settings name="getRoomTypes">
        <Authentication username="{self.username}" password="{self.password}"/>
        <Hotel id="{self.hotel_id}" />
    </Settings>
</Request>'''

        response_xml = self._make_request(xml_request, "getRoomTypes", debug=debug)

        try:
            root = ET.fromstring(response_xml)
            room_types = []

            for room_type_elem in root.findall(".//RoomTypes"):
                code = room_type_elem.findtext("Type", "")
                description = room_type_elem.findtext("Description", "")
                image = room_type_elem.findtext("Image", "")

                if code:  # Only add if code is not empty
                    room_types.append(
                        RoomType(
                            code=code,
                            description=description,
                            image_url=image if image else None,
                        )
                    )

            return room_types

        except ET.ParseError as e:
            raise PMSDataError(f"Invalid XML response: {e}")
        except Exception as e:
            raise PMSDataError(f"Error parsing room types: {e}")

    def get_rooms(self, room_number: Optional[str] = None, debug: bool = False) -> List[Room]:
        """
        Retrieve room information from MiniHotel.

        Note: Only works in sandbox mode.

        Args:
            room_number: Optional room number filter
            debug: If True, print debug information

        Returns:
            List of Room objects

        Raises:
            PMSConnectionError: If unable to connect
            PMSDataError: If response is invalid
        """
        if not self.use_sandbox:
            raise PMSDataError("get_rooms is only available in sandbox mode.")
        room_number_xml = (
            f"<room_number>{room_number}</room_number>" if room_number else ""
        )

        xml_request = f'''<?xml version="1.0" encoding="UTF-8"?>
<Request>
    <Settings name="getRooms">
        <Authentication username="{self.username}" password="{self.password}"/>
        <Hotel id="{self.hotel_id}" />
        {room_number_xml}
    </Settings>
</Request>'''

        response_xml = self._make_request(xml_request, "getRooms", debug=debug)

        try:
            root = ET.fromstring(response_xml)
            rooms = []

            for room_elem in root.findall(".//rnm_struct_room"):
                # Basic room info
                serial = room_elem.findtext("rm_serial", "")
                number = room_elem.findtext("rm_number", "")
                room_type = room_elem.findtext("rm_type", "")
                status = room_elem.findtext("rm_status", "")
                wing = room_elem.findtext("rm_wing", "")
                color = room_elem.findtext("rm_color", "")
                is_dorm = room_elem.findtext("rm_dorm", "0") == "1"
                is_bed = room_elem.findtext("rm_bed", "0") == "1"
                image = room_elem.findtext("rm_image", "")

                # Parse occupancy limits
                occupancy_limits = []
                for occ_elem in room_elem.findall(".//rec_rooms_gst_max"):
                    guest_type = occ_elem.findtext("rgm_gst_type", "")
                    max_count = int(occ_elem.findtext("rgm_max", "0"))
                    if guest_type:
                        occupancy_limits.append(
                            GuestOccupancy(guest_type=guest_type, max_count=max_count)
                        )

                # Parse attributes
                attributes = []
                for attr_elem in room_elem.findall(".//rnm_attribute"):
                    attr_code = attr_elem.get("code", "")
                    attr_desc = attr_elem.get("description", "")
                    if attr_code:
                        attributes.append(
                            RoomAttribute(code=attr_code, description=attr_desc)
                        )

                if number:  # Only add if room number exists
                    rooms.append(
                        Room(
                            room_number=number,
                            room_type=room_type,
                            serial=serial if serial else None,
                            status=status if status else None,
                            wing=wing if wing else None,
                            color=color if color else None,
                            is_dorm=is_dorm,
                            is_bed=is_bed,
                            occupancy_limits=occupancy_limits if occupancy_limits else None,
                            attributes=attributes if attributes else None,
                            image_url=image if image else None,
                        )
                    )

            return rooms

        except ET.ParseError as e:
            raise PMSDataError(f"Invalid XML response: {e}")
        except Exception as e:
            raise PMSDataError(f"Error parsing rooms: {e}")

    def build_room_specs_cache(self, debug: bool = False) -> None:
        """
        Build cache of room type specifications by analyzing physical rooms.

        This derives max occupancy and features per room type from getRooms() data.
        Should be called once during initialization or periodically to refresh cache.

        Args:
            debug: If True, print debug information
        """
        if not self.use_sandbox:
            # In production, we can't call getRooms, so cache remains empty
            # Specs will not be available unless manually populated
            return

        rooms = self.get_rooms(debug=debug)

        # Group rooms by type
        from collections import defaultdict
        rooms_by_type = defaultdict(list)
        for room in rooms:
            rooms_by_type[room.room_type].append(room)

        # Derive specs for each room type
        for room_type_code, type_rooms in rooms_by_type.items():
            max_adults = 0
            max_children = 0
            max_babies = 0
            all_features = set()

            for room in type_rooms:
                # Get max occupancy from this room
                if room.occupancy_limits:
                    for occ in room.occupancy_limits:
                        if occ.guest_type == "A":  # Adult
                            max_adults = max(max_adults, occ.max_count)
                        elif occ.guest_type == "C":  # Child
                            max_children = max(max_children, occ.max_count)
                        elif occ.guest_type == "B":  # Baby
                            max_babies = max(max_babies, occ.max_count)

                # Collect features/attributes
                if room.attributes:
                    for attr in room.attributes:
                        all_features.add(attr.description)

            # Store in cache
            self._room_specs_cache[room_type_code] = {
                "max_adults": max_adults if max_adults > 0 else None,
                "max_children": max_children if max_children > 0 else None,
                "max_babies": max_babies if max_babies > 0 else None,
                "features": sorted(list(all_features)) if all_features else None,
                "bed_configuration": None,  # Could be inferred from room type name
                "size_sqm": None,  # Not available in MiniHotel API
            }

    def get_availability(
        self,
        check_in: date,
        check_out: date,
        adults: int,
        children: int = 0,
        babies: int = 0,
        rate_code: str = "USD",
        room_type_filter: str = "*ALL*",
        board_filter: str = "*ALL*",
        debug: bool = False,
        use_cache: bool = True,
    ) -> AvailabilityResponse:
        """
        Get availability and pricing from MiniHotel (Immediate ARI).

        Uses automatic caching to reduce API calls for repeated queries.

        Args:
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            children: Number of children
            babies: Number of babies
            rate_code: Rate code (determines currency)
            room_type_filter: "*ALL*", "*MIN*", or specific room type
            board_filter: "*ALL*", "*MIN*", or specific board code
            debug: If True, print debug information
            use_cache: If True, use cache (default: True). Set to False to force fresh API call.

        Returns:
            AvailabilityResponse object

        Raises:
            PMSConnectionError: If unable to connect
            PMSValidationError: If parameters are invalid
            PMSDataError: If response is invalid
        """
        # Validate dates
        self.validate_dates(check_in, check_out)

        # Validate guest counts
        if adults < 1:
            raise PMSValidationError("At least 1 adult is required")

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(
                check_in, check_out, adults, children, babies,
                rate_code, room_type_filter, board_filter
            )

            if cache_key in self._availability_cache:
                cache_timestamp, cached_response = self._availability_cache[cache_key]
                if self._is_cache_valid(cache_timestamp):
                    if debug:
                        print(f"[DEBUG] Cache hit for {check_in} to {check_out}")
                    return cached_response
                else:
                    if debug:
                        print(f"[DEBUG] Cache expired for {check_in} to {check_out}")

        # Cache miss or expired - make API call
        if debug and use_cache:
            print(f"[DEBUG] Cache miss for {check_in} to {check_out}, making API call")

        # Format dates as YYYY-MM-DD
        check_in_str = check_in.strftime("%Y-%m-%d")
        check_out_str = check_out.strftime("%Y-%m-%d")

        xml_request = f'''<?xml version="1.0" encoding="UTF-8" ?>
<AvailRaterq xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<Authentication username="{self.username}" password="{self.password}" />
<Hotel id="{self.hotel_id}" />
<DateRange from="{check_in_str}" to="{check_out_str}" />
<Guests adults="{adults}" child="{children}" babies="{babies}" />
<RoomTypes>
<RoomType id="{room_type_filter}" />
</RoomTypes>
<Prices rateCode="{rate_code}">
<Price boardCode="{board_filter}" />
</Prices>
</AvailRaterq>'''

        response_xml = self._make_request(xml_request, debug=debug)

        try:
            root = ET.fromstring(response_xml)

            # Parse hotel info
            hotel_elem = root.find(".//Hotel")
            if hotel_elem is None:
                raise PMSDataError("No hotel information in response")

            hotel_id = hotel_elem.get("id", "")
            hotel_name = hotel_elem.get("Name_e", hotel_elem.get("Name_h", ""))
            currency = hotel_elem.get("Currency", "")

            # Parse date range and guests
            date_range = root.find(".//DateRange")
            guests_elem = root.find(".//Guests")

            # Parse room types with availability
            room_types = []
            for rt_elem in root.findall(".//RoomType"):
                rt_code = rt_elem.get("id", "")
                rt_name = rt_elem.get("Name_e", rt_elem.get("Name_h", ""))
                rt_name_local = rt_elem.get("Name_h")

                # Parse inventory
                inventory = None
                inv_elem = rt_elem.find("Inventory")
                if inv_elem is not None:
                    allocation = int(inv_elem.get("Allocation", "0"))
                    max_avail = int(inv_elem.get("maxavail", "0"))
                    inventory = Inventory(allocation=allocation, max_available=max_avail)

                # Parse prices
                prices = []
                for price_elem in rt_elem.findall("price"):
                    board = price_elem.get("board", "")
                    board_desc = price_elem.get("boardDesc", "")
                    value = float(price_elem.get("value", "0"))
                    value_nrf = price_elem.get("value_nrf")

                    prices.append(
                        BoardPrice(
                            board_code=board,
                            board_description=board_desc,
                            price=value,
                            price_non_refundable=float(value_nrf) if value_nrf else None,
                        )
                    )

                if rt_code:  # Only add if room type code exists
                    # Get cached specs for this room type
                    specs = self._room_specs_cache.get(rt_code, {})

                    room_types.append(
                        RoomTypeAvailability(
                            room_type_code=rt_code,
                            room_type_name=rt_name,
                            room_type_name_local=rt_name_local,
                            inventory=inventory,
                            prices=prices if prices else None,
                            # Merge cached specifications
                            max_adults=specs.get("max_adults"),
                            max_children=specs.get("max_children"),
                            max_babies=specs.get("max_babies"),
                            bed_configuration=specs.get("bed_configuration"),
                            size_sqm=specs.get("size_sqm"),
                            features=specs.get("features"),
                        )
                    )

            response = AvailabilityResponse(
                hotel_id=hotel_id,
                hotel_name=hotel_name,
                currency=currency,
                check_in=check_in,
                check_out=check_out,
                adults=adults,
                children=children,
                babies=babies,
                room_types=room_types if room_types else None,
            )

            # Store in cache
            if use_cache:
                from time import time
                cache_key = self._get_cache_key(
                    check_in, check_out, adults, children, babies,
                    rate_code, room_type_filter, board_filter
                )
                self._availability_cache[cache_key] = (time(), response)
                if debug:
                    print(f"[DEBUG] Cached response for {check_in} to {check_out}")

            return response

        except ET.ParseError as e:
            raise PMSDataError(f"Invalid XML response: {e}")
        except ValueError as e:
            raise PMSDataError(f"Error parsing numeric values: {e}")
        except Exception as e:
            raise PMSDataError(f"Error parsing availability: {e}")

    def generate_booking_link(
        self,
        check_in: date,
        check_out: date,
        adults: int,
        children: int = 0,
        babies: int = 0,
        room_type_code: Optional[str] = None,
        rate_code: Optional[str] = None,
        board_code: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate a MiniHotel booking link.

        Supports two URL formats:
        1. New format (if url_code is set): Uses frame1.hotelpms.io booking frame
        2. Old format (fallback): Uses api.minihotel.cloud/gds

        Args:
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            children: Number of children
            babies: Number of babies
            room_type_code: Optional room type code
            rate_code: Optional rate code (not used in current implementation)
            board_code: Optional board code (not used in current implementation)
            **kwargs: Additional parameters including:
                - language: Language code (default: "en")
                - currency: Currency code for new format (default: "ILS")

        Returns:
            Complete booking URL

        Raises:
            PMSValidationError: If parameters are invalid
        """
        # Validate dates
        self.validate_dates(check_in, check_out)

        # Validate guest counts
        if adults < 1:
            raise PMSValidationError("At least 1 adult is required")

        # Extract optional parameters
        language = kwargs.get("language", "en")
        currency = kwargs.get("currency", "ILS")

        # Format dates
        check_in_str = check_in.strftime("%Y-%m-%d")
        check_out_str = check_out.strftime("%Y-%m-%d")

        if self.url_code:
            # New URL format with url_code
            base_url = "https://frame1.hotelpms.io/BookingFrameClient/hotel"

            # Format dates as YYYYMMDD (no dashes)
            from_date = check_in.strftime("%Y%m%d")
            to_date = check_out.strftime("%Y%m%d")

            # Determine language
            url_language = "he-IL" if _is_hebrew_language(language) else "en-US"

            # Build URL with required parameters
            url = f"{base_url}/{self.url_code}/book/rooms?currency={currency}&language={url_language}&rp=d2Vi&from={from_date}&to={to_date}"

            # Add room type if specified
            if room_type_code:
                url += f"&roomType={room_type_code}"
        else:
            # Fallback to old format
            url = f"https://api.minihotel.cloud/gds/?hotel={self.hotel_id}&checkin={check_in_str}&checkout={check_out_str}"

            # Add guest parameters
            if adults:
                url += f"&adults={adults}"
            if children:
                url += f"&children={children}"
            if babies:
                url += f"&infants={babies}"
            if room_type_code:
                url += f"&room={room_type_code}"

        return url
