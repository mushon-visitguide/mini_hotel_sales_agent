"""ezGo PMS implementation"""
from datetime import date
from typing import List, Optional
from zeep import Client as SoapClient
from zeep.exceptions import Fault as SoapFault
from zeep.helpers import serialize_object
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


class EzGoClient(PMSClient):
    """
    ezGo PMS implementation.

    Supports:
    - Guest count filtering (adults, children, infants)
    - SOAP-based API
    - Multiple board bases (RO, BB, HB, FB, AI)
    - Real-time availability and pricing
    """

    # Endpoints
    WSDL_URL = "https://onlineres.ezgo.co.il/service.asmx?WSDL"

    def __init__(
        self,
        username: str,
        password: str,
        hotel_id: str,
        agency_channel_id: int = 0,
        timeout: int = 30,
        cache_ttl_seconds: int = 300,
    ):
        """
        Initialize ezGo client.

        Args:
            username: ezGo API username
            password: ezGo API password
            hotel_id: Hotel ID in ezGo system (must be integer)
            agency_channel_id: Agency channel ID (default: 0)
            timeout: Request timeout in seconds (default: 30)
            cache_ttl_seconds: Cache TTL for availability (default: 300 = 5 minutes)
        """
        super().__init__(username, password, hotel_id, cache_ttl_seconds)
        self.agency_channel_id = agency_channel_id
        self.timeout = timeout

        # Convert hotel_id to int for ezGo
        try:
            self.hotel_id_int = int(hotel_id)
        except ValueError:
            raise PMSValidationError(f"ezGo hotel_id must be an integer, got: {hotel_id}")

        # Initialize SOAP client
        try:
            from zeep.transports import Transport
            from zeep import Settings
            transport = Transport(timeout=self.timeout)
            # Disable strict mode and raw response to allow flexibility
            settings = Settings(strict=False, xml_huge_tree=True, raw_response=False, xsd_ignore_sequence_order=True)
            self.soap_client = SoapClient(self.WSDL_URL, transport=transport, settings=settings)
        except Exception as e:
            raise PMSConnectionError(f"Failed to initialize SOAP client: {e}")

        # Cache for room type specifications
        self._room_specs_cache = {}

    @property
    def supports_guest_count(self) -> bool:
        """ezGo supports guest count filtering"""
        return True

    @property
    def supports_children_breakdown(self) -> bool:
        """ezGo distinguishes children and infants"""
        return True

    def _create_authentication(self):
        """Create authentication object for SOAP requests"""
        return {
            'sUsrName': self.username,
            'sPwd': self.password
        }

    def _create_date(self, d: date):
        """Convert Python date to ezGo wsDate format"""
        return {
            'Year': d.year,
            'Month': d.month,
            'Day': d.day
        }

    def _parse_board_code(self, board_code: str) -> str:
        """
        Map board filter to ezGo board base.

        Args:
            board_code: Board code from abstraction ("*ALL*", "*MIN*", "BB", etc.)

        Returns:
            ezGo eBoardBase_t value
        """
        if board_code == "*ALL*":
            return "NotSet"  # Will return all board types
        elif board_code == "*MIN*":
            return "NotSet"  # We'll filter for cheapest after getting results
        elif board_code in ["RO", "BB", "HB", "FB", "AI"]:
            return board_code
        else:
            # Default to NotSet for unknown codes
            return "NotSet"

    def get_room_types(self, debug: bool = False) -> List[RoomType]:
        """
        Retrieve all room types from ezGo.

        This calls AgencyChannels_HotelsList to get hotel metadata including room types.

        Args:
            debug: If True, print debug information

        Returns:
            List of RoomType objects

        Raises:
            PMSConnectionError: If unable to connect
            PMSAuthenticationError: If authentication fails
            PMSDataError: If response is invalid
        """
        try:
            if debug:
                print(f"\n[DEBUG] Calling AgencyChannels_HotelsList")
                print(f"[DEBUG] Agency Channel ID: {self.agency_channel_id}")

            auth = self._create_authentication()
            response = self.soap_client.service.AgencyChannels_HotelsList(
                auth,
                self.agency_channel_id
            )

            if debug:
                print(f"[DEBUG] Response received")

            # Serialize the response to dict for easier parsing
            response_dict = serialize_object(response)

            # Check for errors
            error_info = response_dict.get('Error', {})
            if error_info and error_info.get('iErrorId', 0) != 0:
                error_msg = error_info.get('sErrorDescription', 'Unknown error')
                if "authentication" in error_msg.lower() or "permission" in error_msg.lower():
                    raise PMSAuthenticationError(f"Authentication failed: {error_msg}")
                raise PMSDataError(f"API error: {error_msg}")

            room_types = []

            hotels_data = response_dict.get('aHotels', {})
            if hotels_data:
                hotel_list = hotels_data.get('wsHotelInfo', [])

                # Find our hotel in the list
                hotel = None
                for h in hotel_list:
                    if h.get('iHotelCode') == self.hotel_id_int:
                        hotel = h
                        break

                if not hotel:
                    raise PMSDataError(f"Hotel {self.hotel_id} not found in hotel list")

                # Extract room types from hotel
                room_types_data = hotel.get('RoomTypes', {})
                if room_types_data:
                    room_type_list = room_types_data.get('wsHotelRoomInfo', [])
                    for rt in room_type_list:
                        # Get room type name (prefer primary language)
                        name = ""
                        name_data = rt.get('Name', {})
                        if name_data:
                            name_pairs = name_data.get('wsKeyValuePair', [])
                            if name_pairs and len(name_pairs) > 0:
                                name = name_pairs[0].get('Value', '')

                        # Get description
                        desc = ""
                        desc_data = rt.get('Desc', {})
                        if desc_data:
                            desc_pairs = desc_data.get('wsKeyValuePair', [])
                            if desc_pairs and len(desc_pairs) > 0:
                                desc = desc_pairs[0].get('Value', '')

                        # Get first image if available
                        image_url = None
                        images_data = rt.get('Images', {})
                        if images_data:
                            image_list = images_data.get('string', [])
                            if image_list and len(image_list) > 0:
                                image_url = image_list[0]

                        room_type_code = str(rt.get('iRoomTypeCode', ''))

                        room_types.append(
                            RoomType(
                                code=room_type_code,
                                description=name or desc or f"Room Type {room_type_code}",
                                image_url=image_url
                            )
                        )

                        # Store room specs in cache for later use
                        max_adults = rt.get('iMaxAdults', 0)
                        max_children = rt.get('iMaxChilds', 0)
                        max_infants = rt.get('iMaxInfants', 0)

                        self._room_specs_cache[room_type_code] = {
                            "max_adults": max_adults if max_adults > 0 else None,
                            "max_children": max_children if max_children > 0 else None,
                            "max_babies": max_infants if max_infants > 0 else None,
                            "features": [],  # Could parse from Facilities
                            "bed_configuration": None,
                            "size_sqm": None,
                        }

            return room_types

        except SoapFault as e:
            raise PMSConnectionError(f"SOAP fault: {e}")
        except Exception as e:
            if isinstance(e, (PMSAuthenticationError, PMSDataError)):
                raise
            raise PMSConnectionError(f"Error retrieving room types: {e}")

    def get_rooms(self, room_number: Optional[str] = None, debug: bool = False) -> List[Room]:
        """
        Retrieve room information from ezGo.

        Note: ezGo API provides room TYPE information but not individual room inventory.
        This method returns room types as "rooms" for compatibility.

        Args:
            room_number: Optional room number filter (not supported by ezGo)
            debug: If True, print debug information

        Returns:
            List of Room objects (actually room types)

        Raises:
            PMSConnectionError: If unable to connect
            PMSDataError: If response is invalid
        """
        # ezGo doesn't have individual room inventory like MiniHotel
        # We'll return room types as rooms for API compatibility

        room_types = self.get_room_types(debug=debug)
        rooms = []

        for rt in room_types:
            # Get cached specs
            specs = self._room_specs_cache.get(rt.code, {})

            # Build occupancy limits
            occupancy_limits = []
            if specs.get("max_adults"):
                occupancy_limits.append(GuestOccupancy(guest_type="A", max_count=specs["max_adults"]))
            if specs.get("max_children"):
                occupancy_limits.append(GuestOccupancy(guest_type="C", max_count=specs["max_children"]))
            if specs.get("max_babies"):
                occupancy_limits.append(GuestOccupancy(guest_type="B", max_count=specs["max_babies"]))

            rooms.append(
                Room(
                    room_number=rt.code,  # Use room type code as room number
                    room_type=rt.code,
                    serial=None,
                    status=None,
                    wing=None,
                    color=None,
                    is_dorm=False,
                    is_bed=False,
                    occupancy_limits=occupancy_limits if occupancy_limits else None,
                    attributes=None,
                    image_url=rt.image_url
                )
            )

        return rooms

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
        Get availability and pricing from ezGo (AgencyChannels_SearchHotels).

        Uses automatic caching to reduce API calls for repeated queries.

        Args:
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            children: Number of children
            babies: Number of babies/infants
            rate_code: Currency code ("ILS" or "USD")
            room_type_filter: "*ALL*", "*MIN*", or specific room type code
            board_filter: "*ALL*", "*MIN*", or specific board code
            debug: If True, print debug information
            use_cache: If True, use cache (default: True)

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

        # Calculate number of nights
        nights = (check_out - check_in).days

        # Parse room type filter
        room_type_code = 0  # 0 means all room types
        room_type_option = "AllCombination"
        if room_type_filter == "*ALL*":
            room_type_option = "AllCombination"
        elif room_type_filter == "*MIN*":
            room_type_option = "CheapestResult"
        else:
            try:
                room_type_code = int(room_type_filter)
                room_type_option = "Specific"
            except ValueError:
                pass  # Keep as AllCombination

        # Parse board filter
        board_base = self._parse_board_code(board_filter)
        board_option = "AllCombination"
        if board_filter == "*MIN*":
            board_option = "CheapestResult"
        elif board_filter != "*ALL*":
            board_option = "Specific"

        # Map rate_code to currency
        currency = "ILS" if rate_code in ["ILS", "NIS"] else "USD"

        try:
            if debug:
                print(f"\n[DEBUG] Calling AgencyChannels_SearchHotels")
                print(f"[DEBUG] Hotel: {self.hotel_id_int}, Dates: {check_in} to {check_out}")
                print(f"[DEBUG] Guests: {adults}A {children}C {babies}I, Nights: {nights}")
                print(f"[DEBUG] Room Type: {room_type_code} ({room_type_option})")
                print(f"[DEBUG] Board: {board_base} ({board_option})")
                print(f"[DEBUG] Currency: {currency}")

            request = {
                'Id_AgencyChannel': self.agency_channel_id,
                'Authentication': self._create_authentication(),
                'Date_Start': self._create_date(check_in),
                'iNights': nights,
                'Id_Agency': 0,  # 0 for agency channel
                'ID_Region': 0,  # 0 for all regions
                'Id_Hotel': self.hotel_id_int,
                'iRoomTypeCode': room_type_code,
                'eBoardBase': board_base,
                'eBoardBaseOption': board_option,
                'eDomesticIncoming': 'Domestic',  # Could be configurable
                'eRoomTypeCodeOption': room_type_option,
                'iAdults': adults,
                'iChilds': children,
                'iInfants': babies,
                'eCurrency': currency,
                'bDailyPrice': False,  # We want total price
                'bVerbal': True,  # We want verbose/readable codes
                'eLng': 'En',  # Language: 'He' or 'En' (added in newer API version)
            }

            response = self.soap_client.service.AgencyChannels_SearchHotels(wsRequest=request)

            if debug:
                print(f"[DEBUG] Response received")

            # Serialize the response to dict for easier parsing
            response_dict = serialize_object(response)

            # Check for errors
            error_info = response_dict.get('Error', {})
            if error_info and error_info.get('iErrorId', 0) != 0:
                error_msg = error_info.get('sErrorDescription', 'Unknown error')
                if "authentication" in error_msg.lower():
                    raise PMSAuthenticationError(f"Authentication failed: {error_msg}")
                raise PMSDataError(f"API error: {error_msg}")

            # Parse response
            hotel_name = f"Hotel {self.hotel_id}"
            room_types = []

            hotels_data = response_dict.get('aHotels', {})
            if hotels_data:
                hotel_list = hotels_data.get('wsSearchHotel', [])
                for hotel in hotel_list:
                    if hotel.get('iHotelCode') != self.hotel_id_int:
                        continue

                    rooms_data = hotel.get('Rooms', {})
                    if rooms_data:
                        room_list = rooms_data.get('wsSearchHotelRoom', [])
                        for room in room_list:
                            room_type_code = str(room.get('iRoomTypeCode', ''))
                            board_code = room.get('eBoardBase', 'RO')

                            # Get room type name from cache or use code
                            room_type_name = f"Room Type {room_type_code}"
                            specs = self._room_specs_cache.get(room_type_code, {})

                            # Try to get name from room types (if cached)
                            if not specs:
                                try:
                                    rt_list = self.get_room_types(debug=False)
                                    for rt in rt_list:
                                        if rt.code == room_type_code:
                                            room_type_name = rt.description
                                            specs = self._room_specs_cache.get(room_type_code, {})
                                            break
                                except:
                                    pass  # Use default name

                            # Map board base to description
                            board_descriptions = {
                                "RO": "Room Only",
                                "BB": "Bed & Breakfast",
                                "HB": "Half Board",
                                "FB": "Full Board",
                                "AI": "All Inclusive",
                                "NotSet": "No Board"
                            }
                            board_desc = board_descriptions.get(board_code, board_code)

                            # Create inventory
                            available_count = room.get('iAvailable', 0)
                            inventory = Inventory(
                                allocation=available_count,
                                max_available=available_count
                            )

                            # Create board price
                            price_value = float(room.get('cPrice', 0))
                            prices = [
                                BoardPrice(
                                    board_code=board_code,
                                    board_description=board_desc,
                                    price=price_value,
                                    price_non_refundable=None  # ezGo doesn't provide this
                                )
                            ]

                            # Check if we already have this room type in results
                            existing = None
                            for rt in room_types:
                                if rt.room_type_code == room_type_code:
                                    existing = rt
                                    break

                            if existing:
                                # Add this board option to existing room type
                                if existing.prices:
                                    existing.prices.append(prices[0])
                                # Update inventory to maximum available
                                if existing.inventory and available_count > existing.inventory.allocation:
                                    existing.inventory = inventory
                            else:
                                # Create new room type entry
                                room_types.append(
                                    RoomTypeAvailability(
                                        room_type_code=room_type_code,
                                        room_type_name=room_type_name,
                                        room_type_name_local=None,
                                        inventory=inventory,
                                        prices=prices,
                                        # Merge cached specifications
                                        max_adults=specs.get("max_adults"),
                                        max_children=specs.get("max_children"),
                                        max_babies=specs.get("max_babies"),
                                        bed_configuration=specs.get("bed_configuration"),
                                        size_sqm=specs.get("size_sqm"),
                                        features=specs.get("features"),
                                    )
                                )

            response_obj = AvailabilityResponse(
                hotel_id=self.hotel_id,
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
                self._availability_cache[cache_key] = (time(), response_obj)
                if debug:
                    print(f"[DEBUG] Cached response for {check_in} to {check_out}")

            return response_obj

        except SoapFault as e:
            raise PMSConnectionError(f"SOAP fault: {e}")
        except Exception as e:
            if isinstance(e, (PMSAuthenticationError, PMSValidationError, PMSDataError)):
                raise
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
        Generate an ezGo booking link.

        Note: ezGo typically requires using BookReservation API endpoint.
        This generates a placeholder URL that would need to be replaced with
        actual booking endpoint once configured.

        Args:
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            children: Number of children
            babies: Number of babies
            room_type_code: Optional room type code
            rate_code: Optional rate code
            board_code: Optional board code
            **kwargs: Additional parameters

        Returns:
            Booking URL (placeholder for ezGo)

        Raises:
            PMSValidationError: If parameters are invalid
        """
        # Validate dates
        self.validate_dates(check_in, check_out)

        # Validate guest counts
        if adults < 1:
            raise PMSValidationError("At least 1 adult is required")

        # Format dates
        check_in_str = check_in.strftime("%Y-%m-%d")
        check_out_str = check_out.strftime("%Y-%m-%d")

        # Build URL (this is a placeholder - actual booking would use SOAP API)
        url = f"https://ws.ez-go.co.il/book?hotel={self.hotel_id}&checkin={check_in_str}&checkout={check_out_str}"

        # Add guest parameters
        url += f"&adults={adults}"
        if children:
            url += f"&children={children}"
        if babies:
            url += f"&infants={babies}"

        # Add optional parameters
        if room_type_code:
            url += f"&roomtype={room_type_code}"
        if board_code:
            url += f"&board={board_code}"

        return url
