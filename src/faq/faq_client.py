"""FAQ Client for The Way Inn Boutique Hotel

This module provides FAQ responses organized into 5 sections.
Each method returns a comprehensive string response that can be used
by AI agents or chatbots to answer guest questions.
"""


class FAQClient:
    """
    FAQ Client for hotel information retrieval.

    This class provides 5 main FAQ sections that cover all aspects
    of the hotel experience at The Way Inn boutique hotel in Tzfat (Safed), Israel.

    All methods return static string responses that are AI agent agnostic
    and can be used as tool responses in various conversational AI systems.
    """

    def __init__(self):
        """Initialize the FAQ Client."""
        pass

    def get_rooms_and_pricing_info(self) -> str:
        """
        Section 1: Rooms & Pricing Information

        Provides comprehensive information about:
        - Room types and categories
        - Rates and pricing
        - Package deals and special offers
        - What's included in each room
        - Bed configurations
        - Room-specific amenities

        Returns:
            str: Detailed information about all room types, configurations,
                 amenities, and pricing structure.

        Example:
            >>> faq = FAQClient()
            >>> info = faq.get_rooms_and_pricing_info()
            >>> print(info)
        """
        return """
=== ROOMS & PRICING - THE WAY INN ===

OVERVIEW:
The Way Inn offers 10 unique boutique suites for individuals and families. Each suite is named after Kabbalistic Sefirot (spiritual emanations) and decorated with local artwork.

Room sizes range from 25 to 75 sqm. Some include private terraces, private backyards, or mountain views.

ALL STANDARD AMENITIES INCLUDE:
- Air conditioning
- Underfloor heating or central heating
- Espresso machine
- Coffee/tea corner
- Small refrigerator
- Safe
- Free WiFi
- Private bathroom with natural SLS-free toiletries (shampoo, conditioner, body wash)
- Home-baked cookie box
- Wine for couples
- Milk jar
- Personal mineral water bottles in fridge

---

SUITE DETAILS:

1. CHOCHMA (Wisdom) - Couple Suite
   - Size: 25 sqm
   - Bed: King-size (can be separated)
   - Amenities: AC, coffee/tea corner, kettle, espresso machine, safe, sound system, free WiFi, desk, ensuite bathroom with shower, kitchenette, mini fridge, mountain-view terrace, underfloor heating
   - Capacity: 2 guests

2. BINA (Understanding) - Couple Suite
   - Size: 25 sqm
   - Bed: King-size (can be separated)
   - Amenities: AC, coffee/tea corner, kettle, espresso machine, safe, sound system, free WiFi, desk, ensuite bathroom with shower, kitchenette, mini fridge, mountain-view terrace, underfloor heating
   - Capacity: 2 guests

3. DA'AT (Knowledge) - Couple + 1
   - Size: 25 sqm
   - Bed: King-size (can be separated) + 1 foldable bed
   - Amenities: AC, coffee/tea corner, kettle, espresso machine, safe, sound system, free WiFi, desk, ensuite bathroom with shower, mini fridge, outdoor table and chairs in courtyard, underfloor heating
   - Capacity: 2 adults + 1 on foldable bed

4. GEVURA (Strength) - Couple Suite
   - Size: 25 sqm
   - Bed: King-size (can be separated)
   - Amenities: AC, coffee/tea corner, kettle, espresso machine, safe, sound system, free WiFi, desk, ensuite bathroom with shower, mini fridge, outdoor table and chairs in courtyard, underfloor heating
   - Capacity: 2 guests

5. CHESED (Kindness) - Couple + 1
   - Size: 28 sqm
   - Bed: King-size (can be separated) + 1 foldable bed
   - Amenities: AC, coffee/tea corner, kettle, espresso machine, safe, sound system, free WiFi, desk, toilet, ensuite bathroom with bathtub, mini fridge, outdoor table and chairs in courtyard, underfloor heating
   - Capacity: 2 adults + 1 on foldable bed

6. TIFERET (Beauty) - Couple + 1
   - Size: 28 sqm
   - Bed: King-size + 1 foldable bed
   - Amenities: AC, coffee/tea corner, kettle, espresso machine, safe, sound system, free WiFi, ensuite bathroom with shower, kitchenette, king-size bed, mini fridge, outdoor table and chairs on private terrace with breathtaking Galilee mountain views, seating area, underfloor heating
   - Capacity: 2 adults + 1 on foldable bed

7. NETZACH (Eternity) - Two-Room Suite (Couple + 3)
   - Size: 40 sqm
   - Beds: Queen-size + 2 single rolling beds in separate room (living room) + 1 sofa bed suitable for child up to 12
   - Amenities: AC, central heating, coffee/tea corner, kettle, espresso machine, safe, sound system, free WiFi, dining table, ensuite bathroom with shower, kitchenette, mini fridge, seating area with Galilee mountain views
   - Capacity: 2 adults in bedroom + 3 in living room (2 on single beds + 1 child on sofa bed)

8. HOD (Glory) - Two-Room Suite, 2 Levels (Couple + 4)
   - Size: 43.5 sqm (2 floors)
   - Beds: King-size (can be separated) + 4 sofa beds in separate living room
   - Amenities: Coffee/tea corner, kettle, espresso machine, safe, sound system, free WiFi, dining table, bathroom/shower, underfloor heating, kitchenette, mini fridge, outdoor table and chairs
   - Capacity: 2 adults in bedroom + 4 on sofa beds in living room

9. YESOD (Foundation) - Two-Room Suite (Couple + 4)
   - Size: 60 sqm
   - Beds: King-size (can be separated) + 4 sofa beds in separate living room
   - Amenities: AC, central heating, coffee/tea corner, kettle, espresso machine, safe, sound system, free WiFi, dining area, bathroom/shower, kitchenette, mini fridge, outdoor table and chairs
   - Capacity: 2 adults in bedroom + 4 on sofa beds in living room

10. MALCHUT (Kingdom) - Grand Suite (Couple + 5)
    - Size: 75 sqm (open-plan concept - no wall or door separation between rooms)
    - Beds: King-size (can be separated) + 5 sofa beds in same space
    - Amenities: AC, central heating, coffee/tea corner, kettle, espresso machine, safe, sound system, free WiFi, dining table, ensuite bathroom with shower, full-size refrigerator, large kitchen, piano, private backyard with hammocks and seating area
    - Capacity: 2 adults + 5 on sofa beds (open floor plan)

---

ADDITIONAL BED CONFIGURATION DETAILS:
- Chesed: 1 foldable bed
- Tiferet: 1 foldable bed
- Da'at: 1 foldable bed
- Netzach: 2 single rolling beds + 1 sofa bed (for child up to age 12)
- Hod: 4 sofa beds
- Yesod: 4 sofa beds
- Malchut: 5 sofa beds

---

PRICING NOTES:
- All quoted room prices INCLUDE VAT
- Extra bed for any age: 200 ₪ per night
- Free baby crib available
- Tourists with B/2 visa are exempt from VAT
- Israeli citizens are subject to VAT by law

PAYMENT METHODS:
- Visa
- MasterCard
- Cash

---

SPECIAL OFFERS & PARTNERSHIPS:
- 7% discount for direct bookings through website (www.thewayinn.co.il)
- Free cancellation up to 14 days before arrival for direct bookings
- Partnerships with Mega Lan (teachers, defense ministry employees, IDF, engineers, various health funds, banks, and more)
- Partnerships with Isracard TOP, American Express lifestyle cards, and various consumer clubs
- 5% discount at Pina Barosh restaurant on lunch/dinner menu + 30 ₪ off breakfast (when booked through hotel office)

---

For bookings and current availability, contact:
- Phone: 052-6881116
- Email: info@thewayinn.co.il
- Website: www.thewayinn.co.il
"""

    def get_policies_and_procedures_info(self) -> str:
        """
        Section 2: Policies & Procedures

        Provides information about:
        - Check-in/check-out times
        - Cancellation and prepayment policies
        - Payment methods accepted
        - Deposit requirements
        - Booking process
        - Age restrictions
        - Guest rules and conduct
        - Pet policies
        - Kosher policies

        Returns:
            str: Detailed information about hotel policies, procedures,
                 and important rules for guests.

        Example:
            >>> faq = FAQClient()
            >>> info = faq.get_policies_and_procedures_info()
            >>> print(info)
        """
        return """
=== POLICIES & PROCEDURES - THE WAY INN ===

OFFICE HOURS:
- Sunday-Thursday: 09:00-18:00
- Friday & Holiday Eves: 09:00-17:00 (in summer/winter: until 1 hour before Shabbat)
- Saturday: Office closed
- Office Phone: 052-6881116

---

CHECK-IN / CHECK-OUT:
- Check-in: 15:00-18:00 (Friday & holidays: until 1 hour before Shabbat)
- Check-out: 10:30
- Shabbat Check-out: Saturday evening (about 1 hour after Shabbat ends) - NO EXTRA CHARGE

---

CANCELLATION POLICY:

Standard Dates:
- Cancel/modify up to 14 days before arrival: NO CHARGE
- Cancel/modify between 14 days and arrival date OR no-show: FULL CHARGE

Holidays & August:
- Cancel/modify up to 30 days before arrival: NO CHARGE
- Cancel/modify 30-14 days before arrival: 50% CHARGE
- Cancel/modify 14 days before arrival, date of arrival, or no-show: FULL CHARGE

Direct website bookings receive 7% discount and free cancellation up to 14 days before arrival.

---

PAYMENT:
- Payment methods: Visa, MasterCard, Cash
- Tourists with B/2 visa: VAT EXEMPT
- Israeli citizens: VAT REQUIRED by law

---

CHILDREN & AGE:
- Children of all ages are welcome
- Free baby crib available
- Extra bed (any age): 200 ₪ per night
- No age restrictions

---

PET POLICY:
- Pets are NOT allowed

---

ACCESSIBILITY:
- Unfortunately, the property is NOT accessible for wheelchairs
- To enjoy the charm and privacy of our enchanting Tzfat alley, you must descend approximately 30 steps from HaPalmach Street

---

KOSHER POLICY:

Kitchen & Meals:
- The kitchen and meals (for groups of 25+ only) are under Rabbinate Tzfat supervision by Rabbi Bistritzky
- Mehadrin kosher option available with advance booking (groups of 25+ only)

Shabbat-Friendly Features:
- All doors open with keys (not electric)
- Entry gate has analog keypad suitable for Shabbat opening
- Shabbat timers available for lighting
- Hot plate, water urn, white tablecloth available (coordinate with reception in advance)
- Shabbat check-out: Saturday evening (about 1 hour after Shabbat ends) - NO EXTRA CHARGE

Shabbat Catering Options (contact in advance):
- Peretz Catering (Arhela): 050-3272299
- Mandis Catering: 053-9444160
- Monitin Catering: 052-4683300
- Devosh Catering: 052-778-8455

---

HOLIDAY POLICIES:

PASSOVER:
- Room prices include Passover kosher breakfast without kitniyot (legumes)
- Rest of year: No breakfast provided (except for groups of 25+ guests)

SUKKOT:
- Giant sukkah on rooftop with breathtaking Galilee mountain views
- Open and available to all property guests for holiday meals

---

BREAKFAST POLICY:
- The property does NOT serve breakfast
- Private chef meals available for minimum 25 guests
- Excellent cafes with rich Galilean breakfast within 4-minute walk

---

SMOKING POLICY:
- Smoking regulations apply as per Israeli law
- Outdoor areas available for smokers

---

BOOKING & RESERVATIONS:
- Direct booking through website: www.thewayinn.co.il (7% discount + free cancellation)
- Phone: 052-6881116
- Email: info@thewayinn.co.il
- Online booking platforms: Booking.com, Airbnb, etc. (standard policies apply)

---

CONDUCT & QUIET HOURS:
- The property is located in the Old City Artists' Quarter with emphasis on tranquility
- Guests are expected to respect the quiet, mystical atmosphere
- Suitable for romantic getaways, family gatherings, and spiritual retreats
- Please be considerate of other guests and neighbors

---

For any questions about policies, contact:
Phone: 052-6881116
Email: info@thewayinn.co.il
"""

    def get_facilities_and_services_info(self) -> str:
        """
        Section 3: Facilities & Services

        Provides information about:
        - Pool, spa, gym, restaurants, bars
        - Breakfast options
        - Parking and WiFi
        - Hammam (Turkish bath)
        - Massage and spa treatments
        - Room service and special services
        - Location and directions
        - Distance to attractions
        - Nearby restaurants/shops
        - Public transportation
        - Activities available

        Returns:
            str: Detailed information about all facilities, services,
                 location, and available activities.

        Example:
            >>> faq = FAQClient()
            >>> info = faq.get_facilities_and_services_info()
            >>> print(info)
        """
        return """
=== FACILITIES & SERVICES - THE WAY INN ===

LOCATION:
The Way Inn is a boutique suite complex nestled in the heart of the Artists' Quarter of Tzfat (Safed), within lovingly restored 300-year-old buildings. The stone structures, inner courtyards, and terraces facing the Galilee mountains create a tranquil, mystical, and inspiring atmosphere.

Address: Alley 17 Street 23, Tzfat 1320023, Israel

The complex is hidden in a quiet alley in the heart of the Old City, about 30 steps down from the main street.

---

GETTING HERE:

GPS: HaPalmach 68, Tzfat
This will take you to the street above our alley. Don't park immediately when GPS announces arrival. Continue along the curving road (turns left) and start looking for parking along the street. You'll see our sign on the right; below it are 25 steps leading down to us. Descend the steps, turn left, and you've arrived at The Way Inn.

PARKING:
- No private parking (due to Old City location, 30 steps below street level)
- Blue-white street parking on HaPalmach Street (paid via Pango)
  Hours: Sunday-Thursday 08:00-16:00 (NOT Friday/Saturday)
- Free public parking at Wolfson Community Center square (opposite, near the big stone building with clock tower)

BUS:
- Property is minutes' walk from central bus station
- Walk up Jerusalem Street, pass under stone arch, continue left down Old City Inn hotel steps, next alley turn right

---

PROPERTY FACILITIES:

ROOFTOP TERRACE:
- Spacious rooftop terrace with seating areas
- Panoramic views of Mount Meron and Upper Galilee mountains
- Shabbat/Friday evening musical Kabbalat Shabbat in summer
- Sunset yoga/Chi Gong sessions (by advance booking, extra fee)

COURTYARDS & COMMON AREAS:
- Shaded inner courtyards
- Shared lobby (workshop room) for guests
- Small reading library
- Fish pond in main plaza
- Mosaic sign landmark

INTERNET:
- Fast free WiFi throughout entire property
- Some areas don't require password; others use password: 12345678

---

HAMMAM & SPA:

TURKISH HAMMAM (Authentic Steam Sauna):
- Made of marble and Moroccan plaster
- Offers traditional scrubbing for skin cleansing and muscle relaxation
- Active during office hours only (09:00-18:00)

MASSAGE TREATMENTS ROOM:
Available treatments:
1. **All The Way Inn House Treatment**
   - Massage with unique blend of heated aromatic oils combined with hot stones
   - For skin flexibility, renewal, and muscle relaxation
   - Duration: 60/90 minutes | Price: 400/580 ₪

2. **Holistic Massage**
   - Combines three classic techniques: Swedish, deep tissue, aromatherapy with natural oils
   - For toxin release, stress relief, and muscle relaxation
   - Duration: 60/90 minutes | Price: 360/520 ₪

3. **Deep Tissue Massage**
   - Vigorous massage with circular movements in deep muscle tissue layers
   - For stress release, muscle relaxation, and toxin cleansing
   - Duration: 60/90 minutes | Price: 360/520 ₪

4. **Hot Stone Massage**
   - Massage using hot stones to release contractions and blockages
   - Heat increases blood circulation, aids toxin cleansing and release
   - Duration: 60/90 minutes | Price: 380/560 ₪

5. **Extremities Massage**
   - Foot, hand, and head massage focusing on energy points and nerve centers
   - For body relaxation and balance
   - Duration: 60 minutes | Price: 360 ₪

6. **Pregnancy Massage**
   - Gentle holistic massage for women in weeks 16-32 of pregnancy ONLY
   - Relieves fatigue and stress, relaxes contracted muscles
   - Duration: 60 minutes | Price: 360 ₪

FULL-DRESSED BODY TREATMENTS:

7. **Reflexology**
   - Foot pressure on points corresponding to body organs
   - Stimulates nervous system, improves blood flow, releases blockages and stress
   - Duration: 60 minutes | Price: 360 ₪

8. **Thai Massage**
   - Traditional treatment combining stretches, postures, and acupuncture point pressure along body energy channels
   - For stress release, flexibility improvement, vitality flow
   - Duration: 60/90 minutes | Price: 360/520 ₪

9. **Shiatsu**
   - Traditional Japanese treatment combining gentle stretches and acupuncture point pressure along body energy channels
   - For body and soul balance and harmony
   - Duration: 60/90 minutes | Price: 360/520 ₪

To book treatments: Call 052-6881116 Sunday-Thursday 09:00-22:00, Friday until 16:00
Treatments can be scheduled outside office hours with advance booking, subject to therapist availability.

---

ADDITIONAL SERVICES:

- Housekeeping service
- Laundry services (extra fee)
- Transportation services (by advance coordination, extra fee)
- Restaurant reservations assistance
- Day trip planning assistance
- Free city tour every Friday at 11:00 (Ruach Tzfat, starts at General Exhibition Gallery)
- Free city tour every Saturday at 16:00/10:30 (Beit HaKahal - "Build and Be Built", Alkabetz Alley)

---

DINING OPTIONS:

ON-SITE (Groups 25+ only):
- Chef Roni Bar-El offers seasonal Galilean evening meals (meat or vegetarian/vegan)
- Emphasis on local produce and regional wines
- Minimum 25 guests, advance booking required

NEARBY RESTAURANTS IN TZFAT (4-minute walk):
See detailed restaurant list in attractions section.

Excellent cafes along Jerusalem Street (pedestrian street):
- Se'uda BeGan Eden (dairy)
- Bella (dairy, hand-crafted pastries & café)
- Beit HaUgot (dairy)
- Yemenite Lachoach (simple, delicious! Airy Yemenite bread with cheeses)
- Monitin (dairy & breakfast)
- Shitaki (Asian fusion)
- Bashert (fusion - Jewish kitchen & meat smokehouse, Mehadrin kosher)

All kosher. See full details and hours in attractions section.

---

PRIVATE EVENTS & WORKSHOPS:

The property hosts:
- Gourmet meals, receptions, dessert menus for groups of 25-80 guests
- Entire property rental for corporate events, yoga/meditation workshops, spiritual retreats
- Bar/Bat Mitzvah celebrations with musical procession through Old City alleys
- Groom's Shabbat celebrations
- Intimate weddings up to 80 guests
- Restaurant & kitchen rental with external catering option

Our specialty: Bar/Bat Mitzvah production with musical procession through Old City alleys and ceremony guidance in ancient synagogue of your choice.

All catering and logistics services provided by property staff.

Contact Monika for details and organized quote:
Phone: 052-6881116
Email: info@thewayinn.co.il

---

ACTIVITIES & EXPERIENCES:

NEARBY ATTRACTIONS (Walking Distance):
- Galleries in Tzfat alleys - local artists' quarter
- Ancient synagogues
- Historic sites
- Shops, souvenirs, restaurants, cafes, banks, supermarket

AREA ACTIVITIES (Extra Fee, Advance Booking):
- Hikes in Biriya Forest, Nahal Amud, Nahal Rosh Pina, Nimrod Fortress
- Horseback riding at Bat Ya'ar and Golan Board
- Jeep/Razor tours
- Customized day trips
- Workshops: glass blowing, pottery, candle making
- Rooftop sunset yoga/Chi Gong
- Guided tours in Tzfat alleys and Galilee
- Summer Friday evening musical Kabbalat Shabbat on rooftop

FREE TOURS:
- Friday 11:00 - Ruach Tzfat city tour (starts at General Exhibition Gallery)
  Register: https://vstgd.link/gYSkrC
- Saturday 16:00 (winter 10:30) - Free tour from Beit HaKahal "Build and Be Built" in Alkabetz Alley

DISTANCE TO ATTRACTIONS:
- Jerusalem Street (main pedestrian street): 2-minute walk
- Old City galleries: 5-10 minute walk
- Ancient synagogues (Ari, Abuhav, Caro): 5-10 minute walk
- Crusader Fortress: 7-minute walk
- Ancient cemetery & Ari's Mikveh: 10-minute walk
- Bus station: 5-minute walk

---

NEARBY SERVICES:
- Currency exchange & ATMs: Bank HaPoalim on Jerusalem St, Discount & Tefahot at Tzelil Mall
- Supermarkets:
  - Supermarket on HaAliya B Street (5-minute walk)
  - Shufersal Big (south of city)
  - Hetzi Hinam (on road to Rosh Pina)

---

GALLERY RECOMMENDATIONS:
See detailed gallery list with locations in attractions section.

---

For facility questions and activity bookings:
Phone: 052-6881116
Email: info@thewayinn.co.il
Website: www.thewayinn.co.il
"""

    def get_my_reservations_info(self, guest_name: str = "Guest") -> str:
        """
        Section 4: My Reservations (Guest-Specific)

        Provides personalized reservation information:
        - Last 2 past reservations
        - Next 2 upcoming reservations
        - Quick actions (modify/cancel)

        Note: In a real implementation, this would query a database.
        This static version provides a template response.

        Args:
            guest_name: Name of the guest (default: "Guest")

        Returns:
            str: Information about guest's past and upcoming reservations
                 with quick action options.

        Example:
            >>> faq = FAQClient()
            >>> info = faq.get_my_reservations_info("John Smith")
            >>> print(info)
        """
        return f"""
=== MY RESERVATIONS - {guest_name.upper()} ===

Welcome back to The Way Inn, {guest_name}!

---

UPCOMING RESERVATIONS:

[In a live system, this would show your actual upcoming reservations]

To view your reservations:
1. Check your email confirmation from info@thewayinn.co.il
2. Contact our office: 052-6881116
3. Email us: info@thewayinn.co.il

Office Hours:
- Sunday-Thursday: 09:00-18:00
- Friday & Holiday Eves: 09:00-17:00 (until 1 hour before Shabbat)
- Saturday: Closed

---

PAST RESERVATIONS:

[In a live system, this would show your last 2 completed stays]

Thank you for staying with us! We hope to see you again soon.

---

QUICK ACTIONS:

MODIFY RESERVATION:
- Contact office: 052-6881116 or info@thewayinn.co.il
- Must be done during office hours
- Subject to availability and cancellation policy

CANCEL RESERVATION:
Standard Cancellation Policy:
- Up to 14 days before arrival: NO CHARGE
- 14 days or less: FULL CHARGE

Holiday & August Cancellation Policy:
- Up to 30 days before: NO CHARGE
- 30-14 days before: 50% CHARGE
- 14 days or less: FULL CHARGE

To cancel: Contact 052-6881116 or info@thewayinn.co.il

EXTEND STAY:
- Contact office to check availability
- Subject to room availability and current rates

CHANGE DATES:
- Subject to cancellation policy
- Contact office: 052-6881116 or info@thewayinn.co.il

---

BOOKING NEW STAY:

Direct Website Booking Benefits:
- 7% discount
- Free cancellation up to 14 days before arrival

Book at: www.thewayinn.co.il
Or call: 052-6881116
Or email: info@thewayinn.co.il

---

SPECIAL REQUESTS:
For any special requests (early check-in, late check-out, special occasions, dietary needs for group events, etc.):
- Email: info@thewayinn.co.il
- Phone: 052-6881116

We'll do our best to accommodate your needs!

---

LOYALTY PROGRAM:
[Contact us to learn about special returning guest offers]

Thank you for choosing The Way Inn!
"""

    def get_my_stay_guide_info(self) -> str:
        """
        Section 5: My Stay Guide (Guest-Specific)

        Provides essential information for current guests:
        - Door codes & WiFi passwords
        - Parking information
        - Room equipment guides
        - Property navigation & directions to each suite
        - Emergency contacts
        - Troubleshooting (hot water, coffee machine, electricity)

        Returns:
            str: Comprehensive guide for guests during their stay,
                 including practical information and troubleshooting.

        Example:
            >>> faq = FAQClient()
            >>> info = faq.get_my_stay_guide_info()
            >>> print(info)
        """
        return """
=== MY STAY GUIDE - THE WAY INN ===

ESSENTIAL INFORMATION FOR YOUR STAY

---

ENTRY GATE CODE:
Main gate keypad code: c1627

---

WIFI:
- Some areas: No password required
- Other areas: Password is 12345678

---

LOST YOUR KEY?

There are spare keys in small safes near each suite:

GEVURA, CHESED, HOD:
- Location: Shared courtyard with round blue stone table
- Behind the table: Blue metal cabinet with 3 safes (suite names labeled)
- Code: 1961

NETZACH:
- Location: Outside suite door, near electrical panel
- Code: 1961

TIFERET, YESOD, MALCHUT:
- Turn left at mosaic sign, immediately see small stone wall under stairs
- 3 safes on wall with suite names
- Code: 1961

CHOCHMA, BINA, DA'AT:
- Location: Outside main blue entrance gate (right side if arriving from outside, left if exiting)
- Wall with 3 safes labeled with suite names
- Code: 1961

---

DIRECTIONS TO YOUR SUITE:

FROM MAIN ENTRANCE GATE:

**CHOCHMA:**
Immediately after entrance gate, building on right side. First room facing entrance.

**BINA:**
After entrance gate, building on right. Enter building, on left side is hallway with 2 rooms. Right room is Bina.

**DA'AT:**
After entrance gate, building on right. Enter building, on left side is hallway with 2 rooms. Left room is Da'at.

**GEVURA:**
Enter through blue entrance gate, descend steps to main plaza, pass fish pond on right, reach mosaic sign. At sign turn RIGHT to shared courtyard. Left-most room (left-left) is Gevura.

**CHESED:**
Enter through blue entrance gate, descend steps to main plaza, pass fish pond on right, reach mosaic sign. At sign turn RIGHT to shared courtyard. On left side, right of Gevura room, is Chesed.

**TIFERET:**
Enter through blue entrance gate, descend steps to main plaza, pass fish pond on right, reach mosaic sign. At sign turn LEFT, immediately turn RIGHT and climb RIGHT staircase to private terrace through which you enter Tiferet suite.

**NETZACH:**
Enter through blue entrance gate, descend steps to main plaza, pass fish pond on right, reach mosaic sign. At sign turn LEFT and you'll see long staircase directly ahead leading to Netzach suite.

**HOD:**
Enter through blue entrance gate, descend steps to main plaza, pass fish pond on right, reach mosaic sign. At sign turn RIGHT to shared courtyard. Right-most room is Hod.

**YESOD:**
Enter through blue entrance gate, descend steps to main plaza, pass fish pond on right, reach mosaic sign. At sign turn LEFT and directly ahead you'll see Yesod suite.

**MALCHUT:**
Enter through blue entrance gate, descend steps to main plaza, pass fish pond on right, reach mosaic sign. At sign turn LEFT, immediately turn RIGHT, and straight ahead you'll see Malchut suite.

---

NEED MORE SUPPLIES?

SERVICE CLOSET:
Location: Enter straight to mosaic sign, turn right, at end of courtyard on left side behind tall bush.

Available items:
- Towels (face & body)
- Toilet paper
- Coffee/tea
- Espresso capsules
- Soap
- Extra pillow/cushion

IMPORTANT: Close closet tightly after use.

---

TROUBLESHOOTING:

NO HOT WATER?

Suites with water heater (check if heater is on):
- **GEVURA:** Right of bathroom door
- **CHESED:** Left of bed on wall inside arch
- **TIFERET:** Left of bathroom door
- **NETZACH:** On wall left of kitchenette in bedroom
- **YESOD:** Right of bathroom door
- **MALCHUT:** Immediately upon entering suite, right side

Suites with gas heating system:
- **HOD, CHOCHMA, BINA, DA'AT:** If power outage, gas system needs restart. Contact reception.

If still no hot water after checking heater → Contact reception: 052-6881116

---

HOW TO USE ESPRESSO MACHINE:

1. Check water container is full
2. Press power button - button will flash blue, coffee button won't light yet
3. After ~45 seconds, both buttons light blue = machine ready
4. To insert capsule: Slide silver handle all the way out
5. Open capsule packet, insert capsule in correct position (one capsule at a time)
6. Slide handle back
7. Place coffee cup under spout
8. Choose short or long cup according to preference
9. Enjoy fresh, quality coffee!

---

NO ELECTRICITY IN SUITE?

Often (especially after Shabbat), cleaners forget to turn off Shabbat timer.

Solution:
1. Go to electrical panel in suite
2. Open it
3. Look for Shabbat timer (small wheel with red teeth)
4. Lift transparent cover
5. On right side of wheel, slide small button to "0" position

If still no electricity → Contact reception: 052-6881116

---

ROOM AMENITIES GUIDE:

ALL ROOMS INCLUDE:
- Air conditioning
- Heating (underfloor or central)
- Espresso machine
- Coffee/tea corner with kettle
- Mini refrigerator
- Safe
- Sound system (most rooms)
- Free fast WiFi
- Private bathroom with natural toiletries (SLS-free)
- Luxury 100% cotton linens and towels
- Home-baked cookies
- Wine for couples
- Milk jar
- Personal mineral water bottles

SPECIFIC SUITE FEATURES:
- Chochma, Bina: Mountain-view terrace
- Tiferet: Private terrace with breathtaking Galilee views
- Chesed: Bathtub
- Netzach: Seating area with Galilee mountain views
- Hod: 2 floors
- Malchut: Full-size refrigerator, large kitchen, piano, private backyard with hammocks

---

EMERGENCY CONTACTS:

Office (During Hours): 052-6881116
Office Hours:
- Sun-Thu: 09:00-18:00
- Fri/Holiday Eves: 09:00-17:00 (until 1 hour before Shabbat)
- Saturday: CLOSED

Email: info@thewayinn.co.il

After Hours:
If urgent issue outside office hours, call: 052-6881116
(Leave message if no answer - we'll respond as soon as possible)

---

CHECK-OUT REMINDER:
- Standard check-out: 10:30
- Shabbat check-out: Saturday evening ~1 hour after Shabbat ends (NO EXTRA CHARGE)

Before leaving:
- Return key to office (if office open) or leave in suite
- Ensure all windows/doors closed
- Turn off all lights and AC/heating

---

ENJOY YOUR STAY!

Connect with the quiet, mystical atmosphere of Tzfat.
Explore the ancient alleys, visit galleries, experience the spiritual energy.

For any questions or needs during your stay:
Phone: 052-6881116
Email: info@thewayinn.co.il

Shalom and welcome!
"""


# Example usage
if __name__ == "__main__":
    faq = FAQClient()

    print("=" * 80)
    print("SECTION 1: ROOMS & PRICING")
    print("=" * 80)
    print(faq.get_rooms_and_pricing_info())

    print("\n" + "=" * 80)
    print("SECTION 2: POLICIES & PROCEDURES")
    print("=" * 80)
    print(faq.get_policies_and_procedures_info())

    print("\n" + "=" * 80)
    print("SECTION 3: FACILITIES & SERVICES")
    print("=" * 80)
    print(faq.get_facilities_and_services_info())

    print("\n" + "=" * 80)
    print("SECTION 4: MY RESERVATIONS")
    print("=" * 80)
    print(faq.get_my_reservations_info("John Doe"))

    print("\n" + "=" * 80)
    print("SECTION 5: MY STAY GUIDE")
    print("=" * 80)
    print(faq.get_my_stay_guide_info())
