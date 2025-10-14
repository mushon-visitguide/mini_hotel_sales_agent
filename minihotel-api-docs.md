Real-Time Room Status Inquiry
Retrieve detailed information on rooms and reservations within a specified date range. This includes room numbers/names, types, and reservation details such as guest information and current status.

This feature is designed for providers who need to monitor room occupancy in real-time to manage services effectively. Examples include in-room security systems, phone/TV apps, mini-bar management etc. For instance, a smoke detector might be activated when a guest is present and deactivated when the room is vacant.

🚧
Do not query large date ranges without pre approval with the Minihotel team. Such queries may waste server resources and be inefficient.

Request
XML

<?xml version="1.0" encoding="UTF-8" ?>
<!-- Mini Hotel - Availability and Rates - Request --> 
<AvailRaters xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<Authentication username="Test" password="3657488" ResponseType="03" />
<Hotel id="sandbox" />
<DateRange from="2024-07-14" to="2024-07-17" /> 
</AvailRaters>
Response
The response includes the room number list, i.e. all the rooms available at the hotel (whether they are occupied or vacant), and the reservations who stay or arrive (check-in) at the queried date range.

XML

<AvailRaters>
    <Hotel id="sandbox" Name_h="Test Hotel MiniHotel" Name_e="Test Hotel MiniHotel" />
    <DateRange from="2024-07-14" to="2024-07-18" />
    <Rooms>
        <Room Number="01" Rmtype="DBL" />
        <Room Number="02" Rmtype="DBL" />
        <Room Number="101" Rmtype="DBL" />
        <Room Number="102" Rmtype="DBL" />
        <Room Number="103" Rmtype="Twin" />
        <Room Number="104" Rmtype="Twin" />
        <Room Number="301" Rmtype="Twin" />
        <Room Number="302" Rmtype="DBL" />
        <Room Number="303" Rmtype="DBL" />
        <Room Number="304" Rmtype="DBL" />
        <Room Number="401" Rmtype="Executive" />
        <Room Number="501" Rmtype="SNG" />
    </Rooms>
    <RoomsTypes>
        <RoomType Code="2BEDAPT" Description="Two bedroom apartment" />
        <RoomType Code="APT_SEA" Description="Apartment Sea View" />
        <RoomType Code="DBL" Description="Double room" />
        <RoomType Code="TRP" Description="Triple Room" />
        <RoomType Code="Twin" Description="Twin Room" />
    </RoomsTypes>
    <Reservations>
        <Reservation ResNumber="007003163" Namep="Jon" Namef="Doe" RoomNumber="01" RoomType="DBL"
            FromYmd="20240713" ToYmd="20240715" RoomsQty="0001" Status="OK" Board="HB" />
        <Reservation ResNumber="007003171" Namep="Walter" Namef="Matteo" RoomNumber="104" RoomType="Twin"
            FromYmd="20240714" ToYmd="20240715" RoomsQty="0001" Status="OK" Board="HB" />
        <Reservation ResNumber="007003108" Namep="Frank" Namef="Enstein" RoomNumber="02" RoomType="DBL" FromYmd="20240715"
            ToYmd="20240716" RoomsQty="0001" Status="OK" Board="HB" />
        <Reservation ResNumber="007003149" Namep="Cookie" Namef="Jam" RoomNumber="01" RoomType="DBL" FromYmd="20240715"
            ToYmd="20240716" RoomsQty="0001" Status="OK" Board="HB" />
    </Reservations>
</AvailRaters>
Response Explanation
Parameter	Description
Rooms	A Container holding all the hotel rooms at the time of the query. No matter what date range is used in the query. These rooms may be occupied or unoccupied.
RoomsTypes	A Container holding all the hotel room types at the time of the query. No matter what date range is used in the query. These types may be occupied or unoccupied.
Reservations	A Container holding all the hotel reservations for the date range used in the query, containing the room number and reservation status (for example: OK, IN, WL).
ℹ️
Reservations who checkout or cancelled in the queries range are not listed in the response. If a specific room has no reservations staying or arriving at the specified date range, then no reservations will be listed for the room.

Standard Status Codes List

OK: Confirmed
WL: Pending
IN: Checked-in
OUT: Checked-out
CL: Cancelled
BL: Black list
Other values can be customized in the system setup





Bulk ARI Data
ARI stands for: Availability, Rates and Inventory. In-effect it means that using this function you can pull Availability, Rates and Restrictions for a specific period (from - to). The bulk method is suitable for most use-cases, and especially if you're holding the data on your end. If you do not store the data on your end, or if you wish to get results per specific stay dates, then you may consider using the immediate method.

The bulk method is most suitable for OTAs and Agencies holding an ARI database, and that need to save long periods of ARI data on their end.

ℹ️
Note: Maximum period for the query: 1.5 years.

Request
Element	Attributes	Description	Example
Authentication	username, password		<Authentication username="Test" password="3657488" />
Authentication	MinimumNights	Use this attribute to get the minimum nights value. Options: YES, NO. If you don't use this attribute then it's like using "NO".	MinimumNights="YES"
Hotel	ID		Hotel id="sandbox"
DateRange	from, to		<DateRange from="2015-06-28" to="2015-06-30" />
Guests	adults, child, babies		<Guests adults="2" child="1" babies="0" />
Prices	rateCode	rateCode - The rate code supplied by the hotel. This value is Mandatory and cannot be left empty. Use*ALL* to get all the available codes.	<Prices rateCode="USD"> <Price boardCode="*ALL*" /> </Prices>/
Request Example:
XML

<?xml version="1.0" encoding="UTF-8" ?>
<!-- Mini Hotel - Availability and Rates - Request --> 
<AvailRaterq xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<Authentication username="Test" password="3657488" ResponseType="05" /> 
<Hotel id="sandbox" /> 
<DateRange from="2022-06-20" to="2022-06-30" /> 
<Prices rateCode="USD">
</Prices>
</AvailRaterq>
Response Example:
XML

<?xml version="1.0" encoding="UTF-8"?>
<AvailRaters>
<Hotel id="sandbox" Name_h="Sandbox Hotel MiniHotel" Currency="USD" />
<DateRange from="2022-01-15" to="2022-01-19" />
<RoomTypes>
<RoomType id="DBL" RoomName="Double Room" BasicOccupancy="002">
<Day Mdate="20220115" Mavailability="4" Mprice="26.10" Minngt="0" Mclose="No" McloseArr="No" McloseDep="No" ExtraAdultFee="22.00" ExtraChildFee="10.00" ExtraBabyFee="7.00" SingleUse="0.00" />
<Day Mdate="20220116" Mavailability="4" Mprice="22.50" Minngt="0" Mclose="No" McloseArr="No" McloseDep="No" ExtraAdultFee="22.00" ExtraChildFee="10.00" ExtraBabyFee="7.00" SingleUse="0.00" />
<Day Mdate="20220117" Mavailability="4" Mprice="22.50" Minngt="0" Mclose="No" McloseArr="No" McloseDep="No" ExtraAdultFee="22.00" ExtraChildFee="10.00" ExtraBabyFee="7.00" SingleUse="0.00" />
<Day Mdate="20220118" Mavailability="4" Mprice="22.50" Minngt="0" Mclose="No" McloseArr="No" McloseDep="No" ExtraAdultFee="22.00" ExtraChildFee="10.00" ExtraBabyFee="7.00" SingleUse="0.00" />
<Day Mdate="20220119" Mavailability="4" Mprice="22.50" Minngt="0" Mclose="No" McloseArr="No" McloseDep="No" ExtraAdultFee="22.00" ExtraChildFee="10.00" ExtraBabyFee="7.00" SingleUse="0.00" />
</RoomType>
<RoomType id="TRP" RoomName="TRIPLE" BasicOccupancy="003">
<Day Mdate="20220115" Mavailability="2" Mprice="27.90" Minngt="0" Mclose="No" McloseArr="No" McloseDep="No" ExtraAdultFee="85.00" ExtraChildFee="50.00" ExtraBabyFee="25.00" SingleUse="0.00" />
<Day Mdate="20220116" Mavailability="2" Mprice="27.90" Minngt="0" Mclose="No" McloseArr="No" McloseDep="No" ExtraAdultFee="85.00" ExtraChildFee="50.00" ExtraBabyFee="25.00" SingleUse="0.00" />
<Day Mdate="20220117" Mavailability="1" Mprice="28.80" Minngt="0" Mclose="No" McloseArr="No" McloseDep="No" ExtraAdultFee="85.00" ExtraChildFee="50.00" ExtraBabyFee="25.00" SingleUse="0.00" />
<Day Mdate="20220118" Mavailability="0" Mprice="28.80" Minngt="0" Mclose="No" McloseArr="No" McloseDep="No" ExtraAdultFee="85.00" ExtraChildFee="50.00" ExtraBabyFee="25.00" SingleUse="0.00" />
<Day Mdate="20220119" Mavailability="0" Mprice="28.80" Minngt="0" Mclose="No" McloseArr="No" McloseDep="No" ExtraAdultFee="85.00" ExtraChildFee="50.00" ExtraBabyFee="25.00" SingleUse="0.00" />
</RoomType>
</RoomTypes>
<Meals>
<Meal MealId="B">
<Day Mdate="20220115" MealAdult="0.00" MealBaby="0.00" MealChild="0.00" />
<Day Mdate="20220116" MealAdult="0.00" MealBaby="0.00" MealChild="0.00" />
<Day Mdate="20220117" MealAdult="0.00" MealBaby="0.00" MealChild="0.00" />
<Day Mdate="20220118" MealAdult="0.00" MealBaby="0.00" MealChild="0.00" />
<Day Mdate="20220119" MealAdult="0.00" MealBaby="0.00" MealChild="0.00" />
</Meal>
</Meals>
</AvailRaters>
Response Explanation:
Attribute	Description
Mavailability	Availability, room quantity available for the date specified
Mprice	Price for the date specified
Minngt	Minimum Nights for the date specified
Mclose	Closure Restriction for the date specified
McloseArr	Closure for arrival only, if relevant for the date specified
McloseDep	Closure for departure only, if relevant for the date specified
ExtraAdultFee	for the date specified
ExtraChildFee	for the date specified
ExtraBabyFee	for the date specified
SingleUse	The price per 1 adult only using the room, for the date specified
MealId	B = Breakfast; L = Lunch; D = Dinner
Updated over 1 year ago

Immediate ARI Data
Use this function to retrieve Availability & Rates for a specific stay date and a single rate code (one per request). The Immediate mode is intended for partners who don’t store data on their side and need ad-hoc responses—for example, querying a specific hotel, region, or other criteria.

If you're holding the data on your end, and you wish to save the data in bulks, then probably the best option for you would be the bulk method.

ℹ️
Note: The immediate request retrieves availability & prices per the specific stay dates requested, ad-hoc, considering limitations and restrictions. It does not fetch restriction values, and does not fetch bulk data.

Request
Element	Attributes	Description	Example
Authentication	username, password		<Authentication username="Test" password="3657488" />
Authentication	MinimumNights	Use this attribute to get the minimum nights value. Options: YES, NO. If you don't use this attribute then it's like using "NO".	MinimumNights="YES"
Hotel	ID		Hotel id="sandbox"
Area	ID	The values are custom, and they can be agreed with Minihotel prior to starting the integration.	Area id="US"; Area id="Paris"
DateRange	from, to		<DateRange from="2015-06-28" to="2015-06-30" />
Guests	adults, child, babies		<Guests adults="2" child="1" babies="0" />
Agent	id	Agent id is used in case there is need of agent filtering. As a partner, you are also considered as an agent.	<Agent id="Expedia" />
RoomTypes ➔ RoomType	id	This is an optional parameter. You can omit it (not using the parameter is the same as using the *ALL*value).
Special Values:
*MIN*- Get info for the lowest available rate.
The Response will include one room type only.
*ALL* - Get all room types.	<RoomTypes> <RoomType id="*MIN*" /> </RoomTypes>

<RoomTypes> <RoomType id="DBL" /> </RoomTypes>
Prices	rateCode	rateCode - The rate code value can be any value configured in the hotel settings (e.g., "USD", "EUR", "STD", etc.). This value is Mandatory and cannot be left empty. The request supports one rate code per call.	<Prices rateCode="USD"> <Price boardCode="BB" /> </Prices>/
Prices➔ Price	boardCode	boardCode - The board / meal arrangement code. This value is mandatory and cannot be left empty.
Use*ALL* to get all the available codes.
When*MIN*board code is specified, the minimal boards are filtered for each room type.	<Prices rateCode="EUR"> <Price boardCode="*ALL*" /> </Prices>/
ℹ️
Note: The rateCode attribute determines the currency. The codes are custom. In some cases the rate code has a similar value as a currency (eg. "USD"), but in other cases it may be a code such as "Standard", "Hotdeal" etc. The currency itself for any rate, is determined inside the Minihotel settings.

ℹ️
Note: Multiple rate codes are not supported in a single query, but you can submit multiple requests to retrieve several rate codes.

🚧
Note: Use either Hotel id or Area id. If you use both of them the system will ignore the area element.

Request Example - By Hotel ID:
XML

<?xml version="1.0" encoding="UTF-8" ?>
<!-- Mini Hotel - Availability and Rates - Request -->
<AvailRaterq xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<Authentication username="Test" password="3657488" />
<Hotel id="sandbox" />
<DateRange from="2024-06-18" to="2024-06-21" />
<Guests adults="2" child="" babies="" />
<RoomTypes>
<RoomType id="*ALL*" />
</RoomTypes>
<Prices rateCode="USD">
<Price boardCode="*ALL*" />
</Prices>
</AvailRaterq>
Response Example:
XML

<?xml version="1.0" encoding="UTF-8"?>
<AvailRaters>
    <Hotel id="sandbox" Name_h="Test Hotel MiniHotel" Name_e="Test Hotel MiniHotel" Currency="USD" />
    <DateRange from="2024-06-18" to="2024-06-21" />
    <Guests adults="2" child="0" babies="0" />
    <RoomType id="2BEDAPT" Name_h="Two bedroom apartment" Name_e="Two bedroom apartment">
        <Inventory Allocation="5" maxavail="5" />
        <price board="BB" boardDesc="BB" value="352.50" value_nrf="317.25" />
        <price board="FB" boardDesc="Full Board" value="652.50" value_nrf="587.25" />
        <price board="HB" boardDesc="Half Board" value="652.50" value_nrf="587.25" />
        <price board="RO" boardDesc="RO" value="202.50" value_nrf="182.25" />
    </RoomType>
    <RoomType id="DBL" Name_h="Double room" Name_e="Double room">
        <Inventory Allocation="8" maxavail="8" />
        <price board="BB" boardDesc="BB" value="352.50" value_nrf="317.25" />
        <price board="FB" boardDesc="Full Board" value="652.50" value_nrf="587.25" />
        <price board="HB" boardDesc="Half Board" value="652.50" value_nrf="587.25" />
        <price board="RO" boardDesc="RO" value="202.50" value_nrf="182.25" />
    </RoomType>
    <RoomType id="Executive" Name_h="Executive Room" Name_e="Executive Room">
        <Inventory Allocation="1" maxavail="1" />
        <price board="BB" boardDesc="BB" value="352.50" value_nrf="317.25" />
        <price board="FB" boardDesc="Full Board" value="652.50" value_nrf="587.25" />
        <price board="HB" boardDesc="Half Board" value="652.50" value_nrf="587.25" />
        <price board="RO" boardDesc="RO" value="202.50" value_nrf="182.25" />
    </RoomType>
</AvailRaters>
Request Example - By Area ID: (You may use id "US")
XML

<?xml version="1.0" encoding="UTF-8" ?>
<!-- Mini Hotel - Availability and Rates - Request -->
<AvailRaterq xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<Authentication username="Test" password="3657488" />
<Area id="US" Currency="USD" />
<DateRange from="2024-06-17" to="2024-06-20" />
<Guests adults="2" child="" babies="" />
<RoomTypes>
<RoomType id="*ALL*" />
</RoomTypes>
<Prices rateCode="USD">
<Price boardCode="*ALL*" />
</Prices>
</AvailRaterq>
Response Example:
XML

<?xml version="1.0" encoding="UTF-8"?>
<AvailRaters>
    <Hotel id="testhotel" Name_h="Test Hotel MiniHotel" Name_e="Test Hotel MiniHotel" Currency="USD" />
    <CancellPol Full="0002" OneNight="0007" />
    <DateRange from="2024-06-17" to="2024-06-20" />
    <Guests adults="2" child="0" babies="0" />
    <RoomType id="DBL" Name_h="Double room" Name_e="Double room">
        <Inventory Allocation="9" maxavail="9" />
        <price board="BB" boardDesc="BB" value="900" value_nrf="810.00" />
        <price board="FB" boardDesc="Full Board" value="1200" value_nrf="1080.00" />
        <price board="HB" boardDesc="Half Board" value="1200" value_nrf="1080.00" />
    </RoomType>
</AvailRaters>
<AvailRaters>
    <Hotel id="sandbox" Name_h="Test Hotel MiniHotel" Name_e="Test Hotel MiniHotel" Currency="USD" />
    <DateRange from="2024-06-17" to="2024-06-20" />
    <Guests adults="2" child="0" babies="0" />
    <RoomType id="2BEDAPT" Name_h="Two bedroom apartment" Name_e="Two bedroom apartment">
        <Inventory Allocation="5" maxavail="5" />
        <price board="BB" boardDesc="BB" value="352.50" value_nrf="317.25" />
        <price board="FB" boardDesc="Full Board" value="652.50" value_nrf="587.25" />
        <price board="HB" boardDesc="Half Board" value="652.50" value_nrf="587.25" />
        <price board="RO" boardDesc="RO" value="202.50" value_nrf="182.25" />
    </RoomType>
    <RoomType id="DBL" Name_h="Double room" Name_e="Double room">
        <Inventory Allocation="8" maxavail="8" />
        <price board="BB" boardDesc="BB" value="352.50" value_nrf="317.25" />
        <price board="FB" boardDesc="Full Board" value="652.50" value_nrf="587.25" />
        <price board="HB" boardDesc="Half Board" value="652.50" value_nrf="587.25" />
        <price board="RO" boardDesc="RO" value="202.50" value_nrf="182.25" />
    </RoomType>
    <RoomType id="Executive" Name_h="Executive Room" Name_e="Executive Room">
        <Inventory Allocation="1" maxavail="1" />
        <price board="BB" boardDesc="BB" value="352.50" value_nrf="317.25" />
        <price board="FB" boardDesc="Full Board" value="652.50" value_nrf="587.25" />
        <price board="HB" boardDesc="Half Board" value="652.50" value_nrf="587.25" />
        <price board="RO" boardDesc="RO" value="202.50" value_nrf="182.25" />
    </RoomType>
</AvailRaters>
Response Explanation
Element	Attribute	Description
Hotel	id	Hotel's unique id code
Hotel	Name_h	Hotel name. It may contain any language, but it is basically dedicated for the local language (according to the hotel's location)
Hotel	Name_e	Hotel name. It may contain any language, but it's basically dedicated for English
Hotel	Currency	The currency code for the prices returned in the response.
Inventory	Allocation	Number of available rooms
Inventory	maxavail	The total number of rooms
Price	board	Code Meal arrangement
Price	boardDesc	Description of Meal arrangement
Price	value	The regular price value
Price	value_nrf	The non refundable price value. Note: The non refundable factor is set in the Minihotel system settings, per each portal/agent.


getRooms ()
Get Room information & static data, per room number. For example: Room codes, attributes, occupancy settings, cleaning status, etc.

This query is based on room numbers. To retrieve a list of all available rooms, simply leave the room_number element empty.

Alternatively, you can use the Room Status function as a complementary tool to getRooms() for obtaining a complete list of available rooms.

HTTP Request Method = POST.

Sandbox Endpoint
Production Endpoint

https://sandbox.minihotel.cloud/agents/ws/settings/rooms/RoomsMain.asmx/getRooms
Request
Element	Description	Type
room_number	Room Number (Optional value).
Note: If this parameter is empty, you will receive all rooms.	String
Request Example
XML

<?xml version="1.0" encoding="UTF-8"?>
<Request>
    <Settings name="getRooms">
    <Authentication username="Test" password="3657488"/>
    <Hotel id="sandbox" />
    <room_number>101</room_number>
</Settings>
</Request>
Response
Parameter	Description	Type
ArrayOfRnm_struct_room	Rooms container	List Of()
#Rnm_struct_room	Room record	
#rm_serial	Room serial number	String
#rm_number	Room number	String
#rm_type	Room type	String
#rm_clsdt1	Closed date – From	String Format: yyyyMMdd
#rm_clsdt2	Closed date – To	String Format: yyyyMMdd
#rm_status	Room cleaning status:
C = Clean
D = Dirty	String (1 char len)
#rm_dorm	Dormitory (Is the unit a dorm)	String (Binary)
#rm_wing	Wing code	String (1 char len)
#rm_bed	Bed (Is the unit a bed)	String (Binary)
#rm_occ	Not included in occupancy	String (Binary)
#rm_color	Room color	String
#ArrayOfRec_rooms_gst_max	Room maximum guest by type (container)	List Of()
#rec_rooms_gst_max	Room maximum guest by type (record)	String
#rgm_gst_type	Guest type:
A = Adult
B = Baby
C = Child	String
#rgm_max	Max quantity of guests	String
#ArrayOfRnm_struct_room_attributes	Room attributes container	List Of()
#rnm_attribute	Room attribute record	
#attr “code”	Room attribute code	String
#attr “description”	Room attribute description	String
Response Example
XML

<Response>
    <ServerInfo>
        <Name>SANDBOX1</Name>
        <ResponseTime>22 ms</ResponseTime>
        <DateTime>7/8/2018 2:48:17 PM</DateTime>
    </ServerInfo>
    <ArrayOfRnm_struct_room xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
        <rnm_struct_room>
            <rm_serial>001</rm_serial>
            <rm_number>102</rm_number>
            <rm_type>DBL-Interno</rm_type>
            <rm_clsdt1 />
            <rm_clsdt2 />
            <rm_status>C</rm_status>
            <rm_dorm>0</rm_dorm>
            <rm_wing>1</rm_wing>
            <rm_bed>0</rm_bed>
            <rm_occ>0</rm_occ>
           <rm_image>https://sandbox.minihotel.cloud/agents/ws/settings/rooms/RoomImage.aspx?h=YlVab1V4V3l2clA2WDZ5YkxuSDU5dGdZW==</rm_image>
             <ArrayOfRec_rooms_gst_max>
                <rec_rooms_gst_max>
                    <rgm_gst_type>A</rgm_gst_type>
                    <rgm_max>2</rgm_max>
                </rec_rooms_gst_max>
                <rec_rooms_gst_max>
                    <rgm_gst_type>C</rgm_gst_type>
                    <rgm_max>0</rgm_max>
                </rec_rooms_gst_max>
                <rec_rooms_gst_max>
                    <rgm_gst_type>B</rgm_gst_type>
                    <rgm_max>0</rgm_max>
                </rec_rooms_gst_max>
            </ArrayOfRec_rooms_gst_max>
            <ArrayOfRnm_struct_room_attributes>
                <rnm_attribute code="1" description="Garden view" />
                <rnm_attribute code="2" description="Sea view" />
            </ArrayOfRnm_struct_room_attributes>
        </rnm_struct_room>
    </ArrayOfRnm_struct_room>
</Response>


Bulk ARI - Reverse API
This API is intended for updating Minihotel's ARI (Availability, rates and inventory) data from your end into Minihotel. You may check the Minihotel "Rates & Availability" menu using the sandbox hotel, to review your work.

Models
Room
Parameter	Description	Type	Required/Optional
RoomTypeCode	The room type code you want to update	String	Required
Dates	Array of Date	Array[Date]	Required
Date
Parameter	Description	Type	Required/Optional	Notes
Date	Specify a date on which you want to update the data.	String	Required	Date format: YYYY-MM-DD. Min. date: Current date. Max. date: 1.5 years from current date
Availability	Number of rooms available for this room type.	Integer	Optional	Min: 0. Max: 999. You can send null to clear the manual availability override
MinimumNights	Minimum number of nights a guest must book.	Integer	Optional	
MinimumNightsArrival	Minimum number of nights if a guest checks in at this date.	Integer	Optional	
Close	Specifies if the room is closed at this date, making it non-bookable.	Boolean	Optional	
CloseOnArrival	Specifies if the room is unavailable to book if the guest checks-in at this date	Boolean	Optional	
CloseOnDeparture	Specifies if the room is unavailable to book if the guest checks-out at this date.	Boolean	Optional	
Rates	Array of Rate. Update the room type rate per price list.	Array[Rate]	Optional	
ℹ️
Note: Maximum period for the query: 1.5 years

🚧
Do not include the optional parameters for the fields you don't wish to update

Rate
Parameter	Description	Type	Required/Optional	Notes
PriceList	Code for the price list you want to update	String	Required	
Price	Rate for this price list	Decimal	Required	Decimal or null allowed. If you send null, it will remove the current price.
Example
A single date

JSON

[
    {
        "RoomTypeCode": "DBL",
        "Dates": [
            {
                "Date": "2024-11-28",
                "Availability": 4,
                "MinimumNights": 0,
                "MinimumNightsArrival": 0,
                "Close": false,
                "CloseOnArrival": false,
                "CloseOnDeparture": true,
                "Rates": [
                    {
                        "PriceList": "USD",
                        "Price": 90.50
                    },
                    {
                        "PriceList": "ILS",
                        "Price": 310.30
                    }
                ]
            }
        ]
    }
]
XML

<?xml version="1.0" encoding="utf-8"?>
<ArrayOfRoom xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <Room RoomTypeCode="DBL">
		<Dates>
			<Date Value="2024-11-28">
	            	<Availability>4</Availability>
		            <MinimumNights>0</MinimumNights>
		            <MinimumNightsArrival>0</MinimumNightsArrival>
		            <Close>false</Close>
		            <CloseOnArrival>false</CloseOnArrival>
		            <CloseOnDeparture>true</CloseOnDeparture>
		            <Rates>
		                <Rate PriceList="USD">
		                    <Price>90.50</Price>
		                </Rate>
		                <Rate PriceList="USD">
		                    <Price>310.30</Price>
		                </Rate>                    
	            	</Rates>
			</Date>
		</Dates>
</Room>
</ArrayOfRoom>
Multi dates

JSON

[
    {
        "RoomTypeCode": "DBL",
        "Dates": [
            {
                "Date": "2024-06-11",
                "Availability": 4,
                "MinimumNights": 0,
                "MinimumNightsArrival": 0,
                "Close": false,
                "CloseOnArrival": false,
                "CloseOnDeparture": false,
                "Rates": [
                    {
                        "PriceList": "USD",
                        "Price": 81
                    }
                ]
            },
            {
                "Date": "2024-06-12",
                "Availability": 4,
                "MinimumNights": 2,
                "MinimumNightsArrival": 0,
                "Close": false,
                "CloseOnArrival": false,
                "CloseOnDeparture": false,
                "Rates": [
                    {
                        "PriceList": "USD",
                        "Price": 71.50
                    }
                ]
            }
        ]
    }
]
Response
The response contains Warnings and Errors arrays with messages detailing problems found with the provided request.

Parameter	Description	Type
Response	Container for the response	Object
Errors	Array of Error	Array[Error]
Warnings	Array of Warning	Array[Warning]
Error	Message that contains the details of the error	String
Warning	Message that contains the details of the warning	String
Example
JSON

{
    "Warnings": [
        "(Room 'DBL' at 2019-12-20) Warning: Availability cannot be less than 0 (accepted values: 0-999 or null). Availability will not be updated. (Provided value: -1)"
    ],
    "Errors": [
        "(Room 'DBL' at 2025-02-15) Error: Date cannot be greater than 1.5 years from now. The provided data for this date will not be updated. (Current maximum date: 2021-06-17)"
    ]
}
XML

<Response xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <Warnings>
        <Warning>(Room 'DBL' at 2019-12-20) Warning: Availability cannot be less than 0 (accepted values: 0-999 or null). Availability will not be updated. (Provided value: -5)</Warning>
    </Warnings>
    <Error>
        <Error>(Room 'DBL' at 2025-02-15) Error: Date cannot be greater than 1.5 years from the current date. The provided data for this date will not be updated. (Current maximum date: 2021-06-17)</Error>
    </Error>
</Response>
ℹ️
All API responses include an X-Request-ID header with a unique GUID value. This helps our development team trace your requests and responses. If you encounter any issues or errors while using our API, please contact us and provide the X-Request-ID.


Minihotel Booking Engine
Minihotel provides a Booking Engine that allows guests to check availability and book rooms directly online. It can either be embedded into an existing website or accessed via a direct URL.

This page explains how to use the direct URL version, including optional parameters to prefill guest data such as dates, room type, currency, and language.

Direct Link and URL Parameters
Sandbox URL
https://sandbox.minihotel.cloud/BookingFrameClient/hotel/{HotelID}/{InstanceID}/book/rooms?[parameters]
Production URL - International
Production URL - Latam

https://frame1.hotelpms.io/BookingFrameClient/hotel/{HotelID}/{InstanceID}/book/rooms?[parameters]

ID	Description	Example
{HotelID}	Internal Minihotel identifier for the hotel	B263C4CD7A30D45315E78416F6F4F942
{InstanceID}	Unique instance UUID for the hotel	153f2c6a-a062-4c7b-97d7-c6bb89533ae6
The Link
The direct link takes guests to the hotel’s dedicated Booking Engine — a standalone mini-site that can either be used on its own or linked from your website or the hotel's homepage. Use the provided direct link as the destination for your booking buttons, links, banners, or any other marketing materials. If you prefer to embed the Booking Engine within your own site, please refer to our embed instructions here.

Link

https://sandbox.minihotel.cloud/BookingFrameClient/hotel/B263C4CD7A30D45315E78416F6F4F942/153f2c6a-a062-4c7b-97d7-c6bb89533ae6/book/rooms
ℹ️
Note: The production booking link is unique for each hotel. Developers should obtain it directly from the hotel manager, property owner, or by contacting Minihotel support

Parameter	Required	Description	Example
from	Optional	Start date of stay, in YYYYMMDD format	from=20250601
to	Optional	End date of stay, in YYYYMMDD format	to=20250603
nAdults	Optional	Number of adults.	nAdults=2
nChilds	Optional	Number of children.	nChilds=1
nBabies	Optional	Number of infants.	nBabies=1
roomType	Optional	Filter results to show only a specific room type (e.g., STD, DLX)	roomType=DLX
currency	Optional	Three-letter ISO currency code (e.g., EUR, USD)	currency=USD
language	Optional	Language locale format (e.g., en-US, he-IL, es-ES)	language=en-US
Examples
Basic booking with date range (June 1–3, 2025)


https://sandbox.minihotel.cloud/BookingFrameClient/hotel/B263C4CD7A30D45315E78416F6F4F942/153f2c6a-a062-4c7b-97d7-c6bb89533ae6/book/rooms?currency=USD&language=en-US&from=20250601&to=20250603
Filter by room type "DBL"


https://sandbox.minihotel.cloud/BookingFrameClient/hotel/B263C4CD7A30D45315E78416F6F4F942/153f2c6a-a062-4c7b-97d7-c6bb89533ae6/book/rooms?currency=USD&language=en-US&roomType=DBL
Specify 3 adults)


https://sandbox.minihotel.cloud/BookingFrameClient/hotel/B263C4CD7A30D45315E78416F6F4F942/153f2c6a-a062-4c7b-97d7-c6bb89533ae6/book/rooms?currency=USD&language=en-US&nAdults=3


Embedding the Booking Engine
In addition to using the Booking Engine's direct link, you can embed the Minihotel Booking Engine directly into your own website using an . This provides a seamless booking experience within your domain.

To embed the booking engine, you need to follow the next two steps.

1. Get the snippet
Copy and paste the following code snippet, replacing the src URL with your hotel's unique production booking URL as needed.

Snippet

<iframe id="hw-booking-frame"    src="https://sandbox.minihotel.cloud/BookingFrameClient/hotel/B263C4CD7A30D45315E78416F6F4F942/153f2c6a-a062-4c7b-97d7-c6bb89533ae6/book/rooms?currency=USD&language=en-US&rp=" frameborder="0" allowtransparency="true" scrolling="no" style="width: 100%;">
</iframe>
<script src="https://sandbox.minihotel.cloud/BookingFrameClient/public/assets/booking-frame/js/iframe-resizer.min.js"></script>
<script src="https://sandbox.minihotel.cloud/BookingFrameClient/public/assets/booking-frame/js/main.js"></script>
2. Place the Snippet in the Tag
Insert the snippet inside the tag of your HTML page, wherever you want the booking engine to appear.

HTML

<!DOCTYPE html>
<html>
	<head>
		<meta charset="utf-8">
		<title>...</title>
		<script src="scripts.js" type="text/javascript"></script>
		<link rel="stylesheet" href="style.css">

		<!--------------------------------->
		<!--        Other scripts        -->
		<!--------------------------------->

		...
        
	</head>
	<body>

		<div>
			<h1>...</h1>
		</div>

		<!--------------------------------->
		<!--   Content of your website   -->
		<!--------------------------------->

		...

		<!--------------------------------->
		<!-- Paste the code snippet here -->
		<!--------------------------------->

	</body>
</html>
💡
Tip: If you're using a CMS like WordPress, ensure the snippet is inserted into a custom HTML block or widget that supports JavaScript.

ℹ️
Note: The production booking link is unique for each hotel. Developers should obtain it directly from the hotel manager, property owner, or by contacting Minihotel support.

