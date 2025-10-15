#!/usr/bin/env python3
"""
EZGO Hotel Room Availability Scanner
Searches for available rooms across a date range
"""

import json
from datetime import datetime, timedelta
from zeep import Client
from zeep.helpers import serialize_object
# import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
# from threading import Lock
from openai import OpenAI
import os
import argparse
import requests
import asyncio


def format_price(price):
    """Safely format price with validation"""
    if price is None:
        return "N/A"
    try:
        return f"{float(price):.1f}"
    except (ValueError, TypeError):
        return "N/A"

# ==================== CONFIGURATION ====================
# Easily changeable variables - modify these as needed

# System configuration
SYSTEM = "ezgo"  # Reservation system (currently only ezgo supported)
USERNAME = "9600"
PASSWORD = "688E3n"

# Date configuration
START_DATE = datetime.now() + timedelta(days=1)  # Start date for search (tomorrow)
END_DATE = START_DATE + timedelta(days=7)  # End date for search range

# Guest configuration
NUM_NIGHTS = 2  # Number of nights per stay
NUM_ADULTS = 2  # Number of adults
NUM_CHILDREN = 0  # Number of children

# System URLs (based on SYSTEM selection)
EZGO_URL = "https://onlineres.ezgo.co.il/service.asmx?WSDL"

# AI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Load from environment variable
AI_MODEL = "gpt-4-turbo-preview"  # Options: "gpt-4", "gpt-3.5-turbo", "gpt-4-turbo-preview"
USE_AI_PROMPT = True  # Set to False to use manual configuration above
# ========================================================


def read_ai_prompt(filename="ai_prompt.txt"):
    """Read the AI prompt from file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                return content
            return None
    except FileNotFoundError:
        return None


def calculate_easter(year):
    """Calculate Easter date using Computus algorithm for Western Christianity"""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    
    return datetime(year, month, day)


def get_christian_holiday_dates(holiday_name, year):
    """Get Christian holiday dates for the given year"""
    
    # Fixed date holidays
    fixed_holidays = {
        "Christmas": {'date': f"{year}-12-25", 'duration': 2},  # Dec 24-25
        "Christmas Eve": {'date': f"{year}-12-24", 'duration': 1},
        "New Year": {'date': f"{year}-01-01", 'duration': 1},
        "New Year's Day": {'date': f"{year}-01-01", 'duration': 1},
        "Epiphany": {'date': f"{year}-01-06", 'duration': 1},
        "Valentine's Day": {'date': f"{year}-02-14", 'duration': 1},
        "All Saints Day": {'date': f"{year}-11-01", 'duration': 1},
        "Thanksgiving": {'date': calculate_thanksgiving(year), 'duration': 4},  # US Thanksgiving
    }
    
    # Check if it's a fixed date holiday
    if holiday_name in fixed_holidays:
        holiday_info = fixed_holidays[holiday_name]
        return {
            'holiday_name': holiday_name,
            'start_date': holiday_info['date'],
            'duration_days': holiday_info['duration'],
            'year': year
        }
    
    # Easter-based holidays
    easter_date = calculate_easter(year)
    
    easter_holidays = {
        "Easter": {'offset': 0, 'duration': 4},  # Good Friday to Easter Monday
        "Good Friday": {'offset': -2, 'duration': 1},
        "Palm Sunday": {'offset': -7, 'duration': 1},
        "Ash Wednesday": {'offset': -46, 'duration': 1},
        "Pentecost": {'offset': 49, 'duration': 1},
        "Ascension Day": {'offset': 39, 'duration': 1},
    }
    
    if holiday_name in easter_holidays:
        holiday_info = easter_holidays[holiday_name]
        holiday_date = easter_date + timedelta(days=holiday_info['offset'])
        return {
            'holiday_name': holiday_name,
            'start_date': holiday_date.strftime('%Y-%m-%d'),
            'duration_days': holiday_info['duration'],
            'year': year
        }
    
    return None


def calculate_thanksgiving(year):
    """Calculate US Thanksgiving (4th Thursday of November)"""
    november_first = datetime(year, 11, 1)
    # Find first Thursday
    days_until_thursday = (3 - november_first.weekday()) % 7
    first_thursday = november_first + timedelta(days=days_until_thursday)
    # Add 3 weeks to get 4th Thursday
    thanksgiving = first_thursday + timedelta(weeks=3)
    return thanksgiving.strftime('%Y-%m-%d')


def detect_and_fetch_holiday_dates(prompt_text, year):
    """
    Detect Jewish holidays in prompt and fetch their dates for the given year
    Returns dict with holiday info or None
    """
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # First detect if there's a holiday mentioned
    detection_prompt = f"""
    Check if this text mentions any Jewish or Christian holiday. Return JSON with:
    - found: true/false
    - holiday_name: The holiday name in English
    - holiday_type: "jewish" or "christian"
    - holiday_hebrew: The Hebrew name if mentioned
    
    Jewish holidays to detect:
    - ראש השנה / Rosh Hashanah (Jewish New Year) 
    - יום כיפור / Yom Kippur (Day of Atonement)
    - סוכות / Sukkot (Feast of Tabernacles)
    - שמיני עצרת / Shemini Atzeret
    - שמחת תורה / Simchat Torah
    - חנוכה / Hanukkah / Chanukah
    - פסח / Passover / Pesach
    - שבועות / Shavuot (Pentecost)
    - פורים / Purim
    - טו בשבט / Tu BiShvat (New Year of Trees)
    - ל"ג בעומר / Lag BaOmer / Lag B'Omer
    - תשעה באב / Tisha B'Av (9th of Av)
    - יום העצמאות / Yom HaAtzmaut (Israel Independence Day)
    - יום הזיכרון / Yom HaZikaron (Memorial Day)
    - יום השואה / Yom HaShoah (Holocaust Remembrance)
    - יום ירושלים / Yom Yerushalayim (Jerusalem Day)
    - טו באב / Tu B'Av
    
    Christian holidays to detect:
    - Christmas / חג המולד / קריסמס
    - Christmas Eve
    - Easter / פסחא / איסטר
    - Good Friday
    - Palm Sunday
    - New Year / ראש השנה האזרחית
    - Epiphany
    - Valentine's Day / יום האהבה
    - All Saints Day
    - Thanksgiving
    - Ash Wednesday
    - Pentecost
    
    Text to analyze: "{prompt_text}"
    """
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You detect Jewish holidays in text. Return only JSON."},
                {"role": "user", "content": detection_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        detection_result = json.loads(response.choices[0].message.content)
        
        if not detection_result.get('found', False):
            return None
            
        holiday_name = detection_result.get('holiday_name', '')
        holiday_type = detection_result.get('holiday_type', 'jewish')
        
        # Fetch dates based on holiday type
        print(f"Detected {holiday_type} holiday: {holiday_name} for year {year}")
        
        if holiday_type == 'christian':
            # Handle Christian holidays
            return get_christian_holiday_dates(holiday_name, year)
        
        # For Jewish holidays, use Hebcal API
        # Include major holidays (maj=on), minor holidays (min=on), Israeli national holidays (i=on), and modern holidays (mod=on)
        hebcal_url = f"https://www.hebcal.com/hebcal?v=1&cfg=json&year={year}&month=x&maj=on&min=on&i=on&mod=on"
        
        try:
            response = requests.get(hebcal_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                # Map holiday names to Hebcal titles
                holiday_mappings = {
                    "Rosh Hashanah": ["Rosh Hashana"],
                    "Yom Kippur": ["Yom Kippur"],
                    "Sukkot": ["Sukkot"],
                    "Passover": ["Pesach", "Passover"],
                    "Hanukkah": ["Chanukah"],
                    "Purim": ["Purim"],
                    "Shavuot": ["Shavuot"],
                    "Simchat Torah": ["Shmini Atzeret", "Simchat Torah"],
                    "Tu BiShvat": ["Tu BiShvat"],
                    "Lag BaOmer": ["Lag BaOmer", "Lag B'Omer"],
                    "Tisha B'Av": ["Tish'a B'Av"],
                    "Yom HaAtzmaut": ["Yom HaAtzma'ut", "Yom HaAtzma"],
                    "Yom HaZikaron": ["Yom HaZikaron"],
                    "Yom HaShoah": ["Yom HaShoah"],
                    "Yom Yerushalayim": ["Yom Yerushalayim"],
                    "Tu B'Av": ["Tu B'Av"],
                }
                
                # Find the holiday dates
                holiday_dates = []
                search_terms = holiday_mappings.get(holiday_name, [holiday_name])
                
                # Special tracking for Hanukkah start date
                hanukkah_start_date = None

                for item in items:
                    title = item.get('title', '')

                    # Skip eve/erev entries and variations that aren't the main holiday
                    if any(skip in title for skip in ['Erev', 'Sheni', 'Shushan', 'Meshulash', 'LaBehemot']):
                        continue

                    for search_term in search_terms:
                        # For Yom HaAtzmaut, be more flexible with the apostrophe
                        if "HaAtzma" in search_term and "HaAtzma" in title:
                            # Match even if apostrophe is different
                            title_check = True
                        else:
                            title_check = search_term.lower() in title.lower()

                        if title_check:
                            date_str = item.get('date', '')
                            if date_str:
                                # Special handling for Hanukkah - we ONLY want "1 Candle" as the start
                                if holiday_name == "Hanukkah" and "Chanukah" in title:
                                    # Look specifically for the first candle
                                    if "1 Candle" in title:
                                        hanukkah_start_date = date_str
                                        # Don't break - keep looking in case there are multiple years
                                else:
                                    # For other holidays, skip days after the first
                                    # (We want the start date, not II, III, IV, etc.)
                                    if not any(num in title for num in [' II', ' III', ' IV', ' V', ' VI', ' VII', ' VIII']):
                                        # Parse date from Hebcal format (YYYY-MM-DD)
                                        holiday_dates.append(date_str)

                # For Hanukkah, use the specifically found start date
                if holiday_name == "Hanukkah" and hanukkah_start_date:
                    holiday_dates = [hanukkah_start_date]
                
                if holiday_dates:
                    # Get first and last dates for holiday period
                    holiday_dates.sort()
                    start_date = holiday_dates[0]
                    
                    # Determine holiday duration
                    holiday_durations = {
                        "Rosh Hashanah": 2,
                        "Yom Kippur": 1,
                        "Sukkot": 7,
                        "Passover": 8,  # 8 days in diaspora, 7 in Israel
                        "Hanukkah": 8,
                        "Purim": 1,
                        "Shavuot": 2,
                        "Simchat Torah": 1,
                        "Tu BiShvat": 1,
                        "Lag BaOmer": 1,
                        "Tisha B'Av": 1,
                        "Yom HaAtzmaut": 1,
                        "Yom HaZikaron": 1,
                        "Yom HaShoah": 1,
                        "Yom Yerushalayim": 1,
                        "Tu B'Av": 1,
                    }
                    
                    duration = holiday_durations.get(holiday_name, 1)
                    
                    return {
                        'holiday_name': holiday_name,
                        'start_date': start_date,
                        'duration_days': duration,
                        'year': year
                    }
                    
        except Exception as e:
            print(f"Error fetching holiday dates from Hebcal: {e}")
            
    except Exception as e:
        print(f"Error detecting holiday: {e}")
    
    return None


def parse_prompt_with_ai(prompt_text):
    """
    Use GPT-4 to parse natural language prompt into search parameters
    Returns dict with: start_date, num_nights, num_adults, num_children, search_days
    """
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Get today's date for reference
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    current_year = today.year
    current_month = today.month

    # First check for Jewish holidays
    holiday_info = None
    holiday_info = detect_and_fetch_holiday_dates(prompt_text, current_year)

    # If we found a holiday but it's already passed, get next year's date
    if holiday_info:
        holiday_date = datetime.strptime(holiday_info['start_date'], '%Y-%m-%d')
        if holiday_date.date() < today.date():
            print(f"Holiday {holiday_info['holiday_name']} {current_year} has passed, checking {current_year + 1}")
            holiday_info = detect_and_fetch_holiday_dates(prompt_text, current_year + 1)
            if holiday_info:
                print(f"Updated to {current_year + 1}: {holiday_info['start_date']}")

    # If no holiday found in current year, try next year
    if not holiday_info:
        holiday_info = detect_and_fetch_holiday_dates(prompt_text, current_year + 1)

    # Special handling for Hanukkah which can span Dec-Jan
    if not holiday_info and any(h in prompt_text.lower() for h in ['חנוכה', 'hanukkah', 'chanukah', 'hanukah']):
        # If we're in Nov/Dec, check if Hanukkah starts in current year
        # If we're in Jan/Feb, check if Hanukkah from previous year is still ongoing
        if current_month >= 11:  # November or December
            # Already checked current and next year above
            pass
        elif current_month <= 2:  # January or February
            # Check previous year for Hanukkah that might still be ongoing
            holiday_info = detect_and_fetch_holiday_dates(prompt_text, current_year - 1)

    # Debug output to verify holiday detection
    if holiday_info:
        print(f"DEBUG: Holiday info retrieved: {holiday_info}")

    # Prepare holiday context for the prompt - AFTER all date validation
    holiday_context = ""
    if holiday_info:
        holiday_context = f"""
        IMPORTANT: Holiday detected!
        Holiday: {holiday_info['holiday_name']}
        Start date: {holiday_info['start_date']}
        Duration: {holiday_info['duration_days']} days

        For this holiday request:
        - YOU MUST set start_date to {holiday_info['start_date']} - DO NOT use any other date!
        - ALWAYS set search_days to {holiday_info['duration_days']} to search the entire holiday period
        - Keep num_nights at the default (2) unless the user explicitly specifies a different number
        - DO NOT set num_nights to the holiday duration - people rarely stay for entire holidays
        - The user wants to find availability for num_nights somewhere during the holiday period
        - Many people prefer to arrive a day before holidays, so consider searching a few days before too
        """

    # Create system prompt with defaults and examples
    system_prompt = f"""You are a hotel booking assistant. Parse the user's request and extract booking parameters.
    Today's date is {today_str}.

    {holiday_context}
    
    Return a JSON object with these fields:
    - start_date: in format "YYYY-MM-DD" (if not specified, use tomorrow: {(today + timedelta(days=1)).strftime('%Y-%m-%d')})
    - num_nights: number of nights to stay (default: 2, ALWAYS use 2 unless user specifies duration)
    - num_adults: number of adults (default: 2)
    - num_children: number of children (default: 0)
    - search_days: how many days to search from start_date (default: 7)
    
    IMPORTANT DATE PARSING RULES:
    - CRITICAL: Never return dates in the past! Today is {today_str}. Any date before today must be advanced to the next occurrence.
    - When user gives a specific date (like "4.1", "on the 15th", "January 4"):
      * If that date in current year ({current_year}) has already passed, use next year ({current_year + 1})
      * For day-of-month without month specified: if day has passed this month, use next month

    - DAY OF WEEK PARSING (weekday is 0=Monday, 1=Tuesday... 6=Sunday):
      * Hebrew days: ראשון/יום ראשון=Sunday, שני/יום שני=Monday, שלישי/יום שלישי=Tuesday,
                     רביעי/יום רביעי=Wednesday, חמישי/יום חמישי=Thursday, שישי/יום שישי=Friday, שבת/יום שבת=Saturday
      * English days: Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday
      * When user says JUST a day name (e.g., "Monday", "יום שני", "שבת"):
        - Find the NEXT upcoming occurrence (never in the past)
        - If today is Tuesday and they say "Monday", that's 6 days ahead
        - If today IS Monday and they say "Monday", that's 7 days ahead (next Monday)
      * When user says "this [day]" or "[day] הזה":
        - Use this week's occurrence IF it hasn't passed yet
        - If it has passed, use next week's occurrence
      * When user says "next [day]" or "[day] הבא":
        - Always use NEXT WEEK's occurrence (7-13 days from today)
      * Special cases: "שבת הקרובה", "השבת הקרובה", "בשבת" = closest upcoming Saturday

    - ISRAELI WEEKEND: Thursday evening through Saturday (NOT Friday-Sunday!)
      * For "weekend", "סוף השבוע", or "סופ״ש": start_date should be Thursday
      * Default weekend stay is 2 nights (Thu-Sat)
      * Search Thu, Fri, Sat for availability (search_days: 3)
    - If user specifies exact dates like "9-11 November" or "Nov 9-11", this means:
      * Check-in: November 9
      * Check-out: November 11
      * Calculate num_nights as the difference (e.g., Nov 9-11 = 2 nights)
      * Set start_date to the check-in date
      * Set search_days to 1 (only search this specific date)

    - When user provides a SPECIFIC SINGLE DATE (not a range or holiday):
      * Format "X.Y" (like "1.2", "15.3") = specific date, set search_days: 1
      * Specific day names ("Sunday", "יום ראשון", "שבת") = specific date, set search_days: 1
      * "this [day]" or "[day] הזה" = specific date, set search_days: 1
      * "next [day]" or "[day] הבא" = specific date, set search_days: 1
      * "on the 15th" or "ב-15" = specific date, set search_days: 1
      * Relative specific dates: "tomorrow", "מחר", "in 2 days", "בעוד 3 ימים" = specific date, set search_days: 1
      * EXCEPTION: If a Jewish/Christian holiday is detected, use holiday duration for search_days

    - When user provides a RANGE or general request:
      * "next month" or "in [month name]" = search entire month (search_days: 28-31)
      * "next week" = search entire week (search_days: 7)
      * No specific date mentioned = use default (search_days: 7)

    - search_days determines the date range to search for availability, not the length of stay

    Examples of parsing (assuming today is {today_str} which is a {today.strftime('%A')}):
    "I need a room for tomorrow" -> start_date: {(today + timedelta(days=1)).strftime('%Y-%m-%d')}, search_days: 1 (specific date)
    "in 3 days" or "בעוד 3 ימים" -> start_date: {(today + timedelta(days=3)).strftime('%Y-%m-%d')}, search_days: 1
    "מחר" (tomorrow) -> start_date: {(today + timedelta(days=1)).strftime('%Y-%m-%d')}, search_days: 1
    "1.2" -> start_date: {current_year}-02-01, search_days: 1 (specific date)
    "4.1" when today is after Jan 4 -> start_date: {current_year + 1}-01-04, search_days: 1
    "4.1" when today is before Jan 4 -> start_date: {current_year}-01-04, search_days: 1
    "on the 20th" when today is the 25th -> start_date: next month's 20th, search_days: 1
    "on the 20th" when today is the 15th -> start_date: current month's 20th, search_days: 1

    Day of week examples (if today is Wednesday):
    "Monday" or "יום שני" -> next Monday (5 days ahead), search_days: 1
    "Thursday" or "יום חמישי" -> tomorrow (1 day ahead), search_days: 1
    "Wednesday" or "יום רביעי" -> next Wednesday (7 days ahead), search_days: 1
    "שבת" or "שבת הקרובה" or "בשבת" -> this Saturday (3 days ahead), search_days: 1
    "this Monday" or "יום שני הזה" -> next Monday (5 days), search_days: 1
    "next Monday" or "יום שני הבא" -> Monday of next week (12 days ahead), search_days: 1

    Holiday examples (holidays override specific date rule):
    "סוכות" or "Sukkot" -> start_date: [Sukkot start date], search_days: 7 (entire holiday)
    "פסח" or "Passover" -> start_date: [Passover start date], search_days: 8 (entire holiday)
    "חנוכה" or "Hanukkah" -> start_date: [Hanukkah start date], search_days: 8 (entire holiday)
    "ראש השנה" or "Rosh Hashanah" -> start_date: [RH start date], search_days: 2 (entire holiday)
    "Christmas" -> start_date: [Dec 25], search_days: 2 (Christmas Eve and Day)

    Other examples:
    "9-11 November" or "November 9-11" -> start_date: {current_year}-11-09 (or {current_year + 1} if past), num_nights: 2, search_days: 1
    "Check in Dec 25, check out Dec 28" -> start_date: {current_year}-12-25 (or {current_year + 1} if past), num_nights: 3, search_days: 1
    "weekend" or "סוף השבוע" -> Israeli weekend: start_date: next Thursday, num_nights: 2, search_days: 3 (Thu-Sat)
    "2 adults and 1 child" -> num_adults: 2, num_children: 1
    "3 nights in December" -> num_nights: 3, start_date: {current_year}-12-01 (or {current_year + 1} if past), search_days: 31
    "next month" -> start_date: first day of next month, search_days: 30 or 31 (entire month)
    "for a week" or "week-long" or "7 days" -> num_nights: 6 (7 days = 6 nights in hotels)
    "check in on the 15th" -> start_date: next occurrence of 15th (this month if future, next month if past)

    HEBREW DURATION PARSING:
    "שבוע" or "שבוע שלם" or "7 ימים" -> num_nights: 6 (a week = 7 days = 6 nights)
    "לילה" or "לילה אחד" -> num_nights: 1
    "שני לילות" or "2 לילות" -> num_nights: 2
    "שלושה לילות" or "3 לילות" -> num_nights: 3
    "ארבעה לילות" or "4 לילות" -> num_nights: 4
    "חמישה לילות" or "5 לילות" -> num_nights: 5
    "חודש" or "חודש שלם" -> num_nights: 30
    "סוף שבוע" or "סופ״ש" -> num_nights: 2 (Israeli weekend)

    IMPORTANT DAYS TO NIGHTS CONVERSION:
    "יום" or "יום אחד" or "1 יום" -> num_nights: 1 (staying 1 day = overnight)
    "יומיים" or "2 ימים" -> num_nights: 1 (2 days = 1 night)
    "3 ימים" or "שלושה ימים" -> num_nights: 2 (3 days = 2 nights)
    "4 ימים" or "ארבעה ימים" -> num_nights: 3 (4 days = 3 nights)
    "5 ימים" or "חמישה ימים" -> num_nights: 4 (5 days = 4 nights)
    "6 ימים" or "שישה ימים" -> num_nights: 5 (6 days = 5 nights)
    "7 ימים" or "שבעה ימים" -> num_nights: 6 (7 days = 6 nights)
    RULE: X days = X-1 nights (except "יום" alone which usually means overnight)

    HEBREW GUEST PARSING:
    "חדר זוגי" or "זוג" -> num_adults: 2
    "חדר ליחיד" or "יחיד" -> num_adults: 1
    "משפחה של 4" or "משפחה" -> num_adults: 2, num_children: 2
    "2 מבוגרים וילד" -> num_adults: 2, num_children: 1
    "חדר משפחתי" -> num_adults: 2, num_children: 2 (typical family room)

    HEBREW DAY VARIATIONS:
    "ביום [day]" or "ב[day]" -> on [day] (closest upcoming)
    "[day] הקרוב/ה" -> closest upcoming occurrence
    "[day] הבא/ה" -> next week's occurrence
    "ה[day]" -> the upcoming [day]

    Be smart about dates - "next month" means search the ENTIRE next month for availability.
    For specific date ranges (e.g. "9-11 November"), calculate the exact nights and only search that specific date.
    For ambiguous family sizes, assume 2 adults and rest are children.
    IMPORTANT: Remember that hotel stays count NIGHTS, not days. A week (7 days) = 6 nights!
    """
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # Lower temperature for more consistent parsing
        )
        
        params = json.loads(response.choices[0].message.content)

        # Post-process validation: ensure the date is not in the past
        if 'start_date' in params:
            parsed_date = datetime.strptime(params['start_date'], '%Y-%m-%d')
            if parsed_date.date() < today.date():
                # Date is in the past, advance it to next year
                print(f"Warning: AI returned past date {params['start_date']}, advancing to next year")
                parsed_date = parsed_date.replace(year=parsed_date.year + 1)
                params['start_date'] = parsed_date.strftime('%Y-%m-%d')
                print(f"Updated start_date to: {params['start_date']}")

        # Return both params and holiday_info for validation
        return {'params': params, 'holiday_info': holiday_info}
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None


def check_single_date_availability(username, password, check_date, nights, adults, children):
    """
    Helper function to check availability for a single date
    Returns availability info or None if no rooms available
    """
    hotel_id = username
    
    # Select URL based on system
    if SYSTEM.lower() == "ezgo":
        url = EZGO_URL
    else:
        url = EZGO_URL  # Default to EZGO
    
    # Create SOAP client
    client = Client(url)
    auth = {'sUsrName': username, 'sPwd': password}
    
    date_obj = {
        'Year': check_date.year,
        'Month': check_date.month,
        'Day': check_date.day
    }
    
    search_request = {
        'Id_AgencyChannel': 0,
        'Authentication': auth,
        'Date_Start': date_obj,
        'iNights': nights,
        'Id_Agency': 0,
        'ID_Region': 0,
        'Id_Hotel': hotel_id,
        'iRoomTypeCode': 0,
        'eBoardBase': 'BB',
        'eBoardBaseOption': 'AllCombination',
        'eDomesticIncoming': 'Domestic',
        'eRoomTypeCodeOption': 'AllCombination',
        'iAdults': adults,
        'iChilds': children,
        'iInfants': 0,
        'eCurrency': 'ILS',
        'bDailyPrice': True,
        'bVerbal': True
    }
    
    try:
        search_response = client.service.AgencyChannels_SearchHotels(search_request)
        search_data = serialize_object(search_response)
        
        # Check for errors
        error = search_data.get('Error', {})
        error_id = error.get('iErrorId', 0)
        
        if error_id != 0:
            return None
            
        if search_data.get('aHotels'):
            hotels = search_data['aHotels'].get('wsSearchHotel', [])
            for hotel in hotels:
                rooms = hotel.get('Rooms')
                if rooms and rooms.get('wsSearchHotelRoom'):
                    room_list = rooms['wsSearchHotelRoom']
                    available_rooms = []
                    for room in room_list:
                        if room.get('iAvailable', 0) > 0:
                            available_rooms.append({
                                'code': room.get('iRoomTypeCode'),
                                'available_count': room.get('iAvailable'),
                                'price': room.get('cPrice'),
                                'board': room.get('eBoardBase', 'BB')
                            })
                    
                    if available_rooms:
                        checkout_date = check_date + timedelta(days=nights)
                        # Format dates better when spanning different months
                        if check_date.month == checkout_date.month:
                            date_formatted = f"{check_date.strftime('%d')}-{checkout_date.strftime('%d')}/{check_date.strftime('%m')}/{check_date.strftime('%Y')}"
                        else:
                            date_formatted = f"{check_date.strftime('%d/%m/%Y')} - {checkout_date.strftime('%d/%m/%Y')}"
                        return {
                            'date': check_date.strftime('%Y-%m-%d'),
                            'date_formatted': date_formatted,
                            'day_name': check_date.strftime('%A'),
                            'rooms': available_rooms
                        }
    except Exception as e:
        print(f"Error checking date {check_date.strftime('%Y-%m-%d')}: {str(e)}")
    
    return None


async def check_single_date_availability_async(executor, semaphore, username, password, check_date, nights, adults, children):
    """
    Async wrapper for check_single_date_availability using ThreadPoolExecutor
    Maintains semaphore to control concurrent connections
    """
    async with semaphore:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            check_single_date_availability,
            username, password, check_date, nights, adults, children
        )
        return result


async def search_availability_range_async(username, password, start_date, end_date, nights=1, adults=2, children=0):
    """
    Async version of search_availability_range - searches multiple dates in parallel
    Maintains all the same functionality and output as the synchronous version
    """
    hotel_id = username

    # Select URL based on system
    if SYSTEM.lower() == "ezgo":
        url = EZGO_URL
    else:
        url = EZGO_URL

    # Create SOAP client for hotel name lookup
    client = Client(url)
    auth = {'sUsrName': username, 'sPwd': password}

    # Get hotel name (same as sync version)
    hotel_name = "Unknown Hotel"
    try:
        hotels_response = client.service.AgencyChannels_HotelsList(auth, 0)
        hotels_data = serialize_object(hotels_response)
        if hotels_data and hotels_data.get('aHotels'):
            hotels = hotels_data['aHotels'].get('wsHotelInfo', [])
            for hotel in hotels:
                if str(hotel.get('iHotelCode')) == str(hotel_id):
                    name_data = hotel.get('Name', {}).get('wsKeyValuePair', [{}])
                    if name_data:
                        hotel_name = name_data[0].get('Value', 'Unknown Hotel')
                    break
    except Exception:
        pass

    print(f"\nSearching availability for: {hotel_name} (Hotel ID: {hotel_id})")
    last_checkin_date = end_date - timedelta(days=nights)
    print(f"Check-in date range: {start_date.strftime('%Y-%m-%d')} to {last_checkin_date.strftime('%Y-%m-%d')}")
    print(f"Stay duration: {nights} night(s), {adults} adult(s), {children} child(ren)")
    print(f"Last possible checkout: {end_date.strftime('%Y-%m-%d')}")
    print("=" * 70)

    # Create executor and semaphore for controlled concurrency
    executor = ThreadPoolExecutor(max_workers=10)
    semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests

    # Create all tasks for parallel execution
    tasks = []
    dates_to_check = []
    current_date = start_date

    while current_date <= last_checkin_date:
        task = check_single_date_availability_async(
            executor, semaphore, username, password,
            current_date, nights, adults, children
        )
        tasks.append(task)
        dates_to_check.append(current_date)
        current_date += timedelta(days=1)

    print(f"Checking {len(tasks)} dates in parallel...")

    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks)

    # Process results and print them (maintaining same output format)
    available_dates = []
    for i, (date, result) in enumerate(zip(dates_to_check, results)):
        if result:
            # Result has availability
            checkout_date = date + timedelta(days=nights)
            if date.month == checkout_date.month:
                date_formatted = f"{date.strftime('%d')}-{checkout_date.strftime('%d')}/{date.strftime('%m')}/{date.strftime('%Y')}"
            else:
                date_formatted = f"{date.strftime('%d/%m/%Y')} - {checkout_date.strftime('%d/%m/%Y')}"

            date_info = {
                'date': date.strftime('%Y-%m-%d'),
                'date_formatted': date_formatted,
                'day_name': date.strftime('%A'),
                'available': True,
                'rooms': result['rooms']
            }

            print(f"\n[AVAILABLE] {date_formatted} ({date.strftime('%A')})")
            for room in result['rooms']:
                print(f"  - Room {room['code']}: {room['available_count']} available @ {format_price(room['price'])} ILS ({room['board']})")
            available_dates.append(date_info)
        else:
            # No availability
            checkout_date = date + timedelta(days=nights)
            if date.month == checkout_date.month:
                date_formatted = f"{date.strftime('%d')}-{checkout_date.strftime('%d')}/{date.strftime('%m')}/{date.strftime('%Y')}"
            else:
                date_formatted = f"{date.strftime('%d/%m/%Y')} - {checkout_date.strftime('%d/%m/%Y')}"
            print(f"[NO ROOMS ] {date_formatted} ({date.strftime('%A')})")

    # Summary (same as sync version)
    print("\n" + "=" * 70)
    print("SUMMARY")
    print(f"Total dates checked: {(last_checkin_date - start_date).days + 1}")
    print(f"Dates with availability: {len(available_dates)}")

    if available_dates:
        print("\nAvailable dates:")
        for date_info in available_dates:
            print(f"  - {date_info['date_formatted']} ({date_info['day_name']}):")
            for room in date_info['rooms']:
                print(f"    • Room {room['code']}: {room['available_count']} available @ {format_price(room['price'])} ILS")

    # Clean up executor
    executor.shutdown(wait=False)

    return available_dates


def search_availability_range(username, password, start_date, end_date, nights=1, adults=2, children=0):
    """
    Search for room availability across a date range
    NOTE: This is the synchronous version, kept for backward compatibility.
    The async version (search_availability_range_async) is used by default for better performance.

    Args:
        username: EZGO username
        password: EZGO password
        start_date: Starting date for search (datetime object)
        end_date: Ending date for search (datetime object)
        nights: Number of nights per stay (default 1)
        adults: Number of adults (default 2)
        children: Number of children (default 0)
    """

    hotel_id = username
    
    # Select URL based on system
    if SYSTEM.lower() == "ezgo":
        url = EZGO_URL
    else:
        # Default to EZGO for now as it's the only supported system
        url = EZGO_URL

    # Create SOAP client
    client = Client(url)
    auth = {'sUsrName': username, 'sPwd': password}

    # Get hotel name
    hotel_name = "Unknown Hotel"
    try:
        hotels_response = client.service.AgencyChannels_HotelsList(auth, 0)
        hotels_data = serialize_object(hotels_response)
        if hotels_data and hotels_data.get('aHotels'):
            hotels = hotels_data['aHotels'].get('wsHotelInfo', [])
            for hotel in hotels:
                if str(hotel.get('iHotelCode')) == str(hotel_id):
                    name_data = hotel.get('Name', {}).get('wsKeyValuePair', [{}])
                    if name_data:
                        hotel_name = name_data[0].get('Value', 'Unknown Hotel')
                    break
    except Exception:
        pass

    print(f"\nSearching availability for: {hotel_name} (Hotel ID: {hotel_id})")
    # Calculate the last possible check-in date based on the end_date being the last checkout
    last_checkin_date = end_date - timedelta(days=nights)
    print(f"Check-in date range: {start_date.strftime('%Y-%m-%d')} to {last_checkin_date.strftime('%Y-%m-%d')}")
    print(f"Stay duration: {nights} night(s), {adults} adult(s), {children} child(ren)")
    print(f"Last possible checkout: {end_date.strftime('%Y-%m-%d')}")
    print("=" * 70)

    available_dates = []
    current_date = start_date

    while current_date <= last_checkin_date:
        date_obj = {
            'Year': current_date.year,
            'Month': current_date.month,
            'Day': current_date.day
        }

        search_request = {
            'Id_AgencyChannel': 0,
            'Authentication': auth,
            'Date_Start': date_obj,
            'iNights': nights,
            'Id_Agency': 0,
            'ID_Region': 0,
            'Id_Hotel': hotel_id,
            'iRoomTypeCode': 0,
            'eBoardBase': 'BB',
            'eBoardBaseOption': 'AllCombination',
            'eDomesticIncoming': 'Domestic',
            'eRoomTypeCodeOption': 'AllCombination',
            'iAdults': adults,
            'iChilds': children,
            'iInfants': 0,
            'eCurrency': 'ILS',
            'bDailyPrice': True,
            'bVerbal': True
        }

        try:
            search_response = client.service.AgencyChannels_SearchHotels(search_request)
            search_data = serialize_object(search_response)

            # Check for errors
            error = search_data.get('Error', {})
            error_id = error.get('iErrorId', 0)

            # Initialize date info
            checkout_date = current_date + timedelta(days=nights)
            # Format dates better when spanning different months
            if current_date.month == checkout_date.month:
                date_formatted = f"{current_date.strftime('%d')}-{checkout_date.strftime('%d')}/{current_date.strftime('%m')}/{current_date.strftime('%Y')}"
            else:
                date_formatted = f"{current_date.strftime('%d/%m/%Y')} - {checkout_date.strftime('%d/%m/%Y')}"
            date_info = {
                'date': current_date.strftime('%Y-%m-%d'),
                'date_formatted': date_formatted,
                'day_name': current_date.strftime('%A'),
                'available': False,
                'rooms': [],
                'error': None
            }

            if error_id != 0:
                date_info['error'] = f"Error {error_id}: {error.get('sErrorDescription', 'Unknown error')}"
            elif search_data.get('aHotels'):
                hotels = search_data['aHotels'].get('wsSearchHotel', [])
                for hotel in hotels:
                    rooms = hotel.get('Rooms')
                    if rooms and rooms.get('wsSearchHotelRoom'):
                        room_list = rooms['wsSearchHotelRoom']
                        for room in room_list:
                            if room.get('iAvailable', 0) > 0:
                                date_info['available'] = True
                                date_info['rooms'].append({
                                    'code': room.get('iRoomTypeCode'),
                                    'available_count': room.get('iAvailable'),
                                    'price': room.get('cPrice'),
                                    'board': room.get('eBoardBase', 'BB')
                                })

            # Print result for this date
            if date_info['available']:
                print(f"\n[AVAILABLE] {date_info['date_formatted']} ({date_info['day_name']})")
                for room in date_info['rooms']:
                    print(
                        f"  - Room {room['code']}: {room['available_count']} available @ {format_price(room['price'])} ILS ({room['board']})")
                available_dates.append(date_info)
            else:
                print(f"[NO ROOMS ] {date_info['date_formatted']} ({date_info['day_name']})")
                if date_info['error'] and 'CloseFlag' not in date_info['error']:
                    print(f"  {date_info['error']}")

        except Exception as e:
            print(f"[ERROR    ] {current_date.strftime('%Y-%m-%d')}: {str(e)}")

        # Move to next date
        current_date += timedelta(days=1)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print(f"Total dates checked: {(last_checkin_date - start_date).days + 1}")
    print(f"Dates with availability: {len(available_dates)}")

    if available_dates:
        print("\nAvailable dates:")
        for date_info in available_dates:
            print(f"  - {date_info['date_formatted']} ({date_info['day_name']}):")
            for room in date_info['rooms']:
                print(f"    • Room {room['code']}: {room['available_count']} available @ {format_price(room['price'])} ILS")

    return available_dates


def search_alternatives(username, password, original_start_date, original_end_date, nights, adults, children):
    """
    Search for alternative availability options when original request has no availability
    Priority order:
    1. If weekend: same weekday one week before/after
    2. Shorter stays at original dates
    3. Different dates with same nights
    4. Different duration at original dates
    """
    print("\n" + "=" * 70)
    print("SEARCHING FOR ALTERNATIVES...")
    print("=" * 70)
    
    alternatives = {
        "same_weekend_earlier": [],
        "same_weekend_later": [],
        "shorter_stays": [],
        "earlier_dates": [],
        "later_dates": [],
        "different_nights": []
    }
    
    # Check if it's an Israeli weekend (Thursday, Friday, Saturday)
    is_israeli_weekend = original_start_date.weekday() in [3, 4, 5]
    
    # 1. WEEKEND ALTERNATIVES (if applicable)
    if is_israeli_weekend:
        print(f"\nDetected Israeli weekend request ({original_start_date.strftime('%A')})")
        print("Checking same weekday in different weeks...")
        
        # Try one week earlier
        week_earlier = original_start_date - timedelta(days=7)
        result = check_single_date_availability(username, password, week_earlier, nights, adults, children)
        if result:
            alternatives["same_weekend_earlier"].append(result)
            print(f"  + Found availability: {result['date_formatted']} ({result['day_name']})")
        
        # Try one week later
        week_later = original_start_date + timedelta(days=7)
        result = check_single_date_availability(username, password, week_later, nights, adults, children)
        if result:
            alternatives["same_weekend_later"].append(result)
            print(f"  + Found availability: {result['date_formatted']} ({result['day_name']})")
    
    # 2. SHORTER STAYS (prioritized after weekend check)
    print("\nChecking shorter stays at original dates...")
    # Search down to 50% of requested nights (but minimum 1 night)
    min_nights = max(1, int(nights * 0.5))
    for nights_to_try in range(nights - 1, min_nights - 1, -1):
        result = check_single_date_availability(username, password, original_start_date, nights_to_try, adults, children)
        if result:
            alternatives["shorter_stays"].append({**result, 'nights': nights_to_try})
            print(f"  + Found {nights_to_try} night(s): {result['date_formatted']}")
    
    # 3. EARLIER DATES (same number of nights)
    print("\nChecking earlier dates with same duration...")
    today = datetime.now().date()
    for days_before in [1, 2, 3, 4, 5, 6, 7]:
        earlier_start = original_start_date - timedelta(days=days_before)
        # Skip if the date would be in the past
        if earlier_start.date() < today:
            continue
        result = check_single_date_availability(username, password, earlier_start, nights, adults, children)
        if result:
            alternatives["earlier_dates"].append({**result, 'days_difference': -days_before})
            print(f"  + Found {days_before} days earlier: {result['date_formatted']}")
            break  # One earlier option is enough
    
    # 4. LATER DATES (same number of nights)
    print("\nChecking later dates with same duration...")
    for days_after in [1, 2, 3, 4, 5, 6, 7]:
        later_start = original_start_date + timedelta(days=days_after)
        result = check_single_date_availability(username, password, later_start, nights, adults, children)
        if result:
            alternatives["later_dates"].append({**result, 'days_difference': days_after})
            print(f"  + Found {days_after} days later: {result['date_formatted']}")
            break  # One later option is enough
    
    # 5. DIFFERENT DURATION (last resort)
    print("\nChecking different durations at original dates...")
    for nights_diff in [-1, 1]:
        nights_to_try = nights + nights_diff
        if 1 <= nights_to_try <= 14:  # Reasonable limits
            result = check_single_date_availability(username, password, original_start_date, nights_to_try, adults, children)
            if result:
                alternatives["different_nights"].append({**result, 'nights': nights_to_try, 'nights_difference': nights_diff})
                print(f"  + Found {nights_to_try} night(s): {result['date_formatted']}")
    
    # Count total alternatives
    total_found = sum(len(v) for v in alternatives.values())
    
    if total_found == 0:
        print("\nX No alternative dates found with availability")
    else:
        print(f"\n+ Found {total_found} alternative option(s)")
    
    return alternatives


async def search_alternatives_async(username, password, start_date, end_date, nights, adults, children):
    """
    Async version of alternatives search - runs all alternative searches in parallel
    """
    # Initialize empty alternatives dictionary
    alternatives = {
        "same_weekend_earlier": [],
        "same_weekend_later": [],
        "shorter_stays": [],
        "earlier_dates": [],
        "later_dates": [],
        "different_nights": []
    }

    # Create executor and semaphore for controlled concurrency
    executor = ThreadPoolExecutor(max_workers=15)  # More workers for alternatives
    semaphore = asyncio.Semaphore(15)  # Allow more concurrent requests

    # Collect all tasks with their identifiers
    tasks = []
    task_info = []  # To track what each task is for

    # Check if it's a weekend
    is_weekend = start_date.weekday() in [3, 4, 5]

    # Weekend alternatives
    if is_weekend:
        week_earlier = start_date - timedelta(days=7)
        tasks.append(check_single_date_availability_async(
            executor, semaphore, username, password, week_earlier, nights, adults, children
        ))
        task_info.append(('same_weekend_earlier', None))

        week_later = start_date + timedelta(days=7)
        tasks.append(check_single_date_availability_async(
            executor, semaphore, username, password, week_later, nights, adults, children
        ))
        task_info.append(('same_weekend_later', None))

    # Shorter stays - check ALL dates in range
    min_nights = max(1, int(nights * 0.5))
    for nights_to_try in range(nights - 1, min_nights - 1, -1):
        last_checkin_for_shorter = end_date - timedelta(days=nights_to_try)
        current_check_date = start_date

        while current_check_date <= last_checkin_for_shorter:
            tasks.append(check_single_date_availability_async(
                executor, semaphore, username, password,
                current_check_date, nights_to_try, adults, children
            ))
            task_info.append(('shorter_stays', nights_to_try))
            current_check_date += timedelta(days=1)

    # Earlier dates (1-7 days before)
    today = datetime.now().date()
    for days_before in [1, 2, 3, 4, 5, 6, 7]:
        earlier_start = start_date - timedelta(days=days_before)
        if earlier_start.date() >= today:
            tasks.append(check_single_date_availability_async(
                executor, semaphore, username, password,
                earlier_start, nights, adults, children
            ))
            task_info.append(('earlier_dates', -days_before))

    # Later dates (1-7 days after)
    for days_after in [1, 2, 3, 4, 5, 6, 7]:
        later_start = start_date + timedelta(days=days_after)
        tasks.append(check_single_date_availability_async(
            executor, semaphore, username, password,
            later_start, nights, adults, children
        ))
        task_info.append(('later_dates', days_after))

    # Different duration
    for nights_diff in [-1, 1]:
        nights_to_try = nights + nights_diff
        if 1 <= nights_to_try <= 14:
            tasks.append(check_single_date_availability_async(
                executor, semaphore, username, password,
                start_date, nights_to_try, adults, children
            ))
            task_info.append(('different_nights', nights_to_try))

    if len(tasks) > 0:
        print(f"\nSearching for alternatives ({len(tasks)} checks in parallel)...")

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, (result, (category, extra_info)) in enumerate(zip(results, task_info)):
            if isinstance(result, Exception):
                continue  # Skip errors

            if result:  # Found availability
                if category == 'same_weekend_earlier':
                    alternatives["same_weekend_earlier"].append(result)
                elif category == 'same_weekend_later':
                    alternatives["same_weekend_later"].append(result)
                elif category == 'shorter_stays':
                    # Group shorter stays by nights
                    found = False
                    for alt in alternatives["shorter_stays"]:
                        if alt.get('nights') == extra_info:
                            alt['available_dates'].append(result)
                            found = True
                            break
                    if not found:
                        alternatives["shorter_stays"].append({
                            'nights': extra_info,
                            'available_dates': [result]
                        })
                elif category == 'earlier_dates':
                    if not alternatives["earlier_dates"]:  # Only keep first found
                        alternatives["earlier_dates"].append({
                            **result,
                            'days_difference': extra_info
                        })
                elif category == 'later_dates':
                    if not alternatives["later_dates"]:  # Only keep first found
                        alternatives["later_dates"].append({
                            **result,
                            'days_difference': extra_info
                        })
                elif category == 'different_nights':
                    alternatives["different_nights"].append({
                        **result,
                        'nights': extra_info,
                        'nights_difference': extra_info - nights
                    })

    # Clean up executor
    executor.shutdown(wait=False)

    # Count and report
    total_found = sum(len(v) for v in alternatives.values())
    if total_found > 0:
        print(f"Found {total_found} alternative option(s)")

    return alternatives


def search_all_parallel(username, password, start_date, end_date, nights, adults, children):
    """
    Search main dates first, then alternatives in parallel.
    Returns: (main_results, alternatives_dict)
    """

    # Run the main search using async for massive speedup
    main_results = asyncio.run(search_availability_range_async(
        username, password, start_date, end_date, nights, adults, children
    ))

    # If we found availability in main search, skip alternatives for speed
    if main_results and len(main_results) > 0:
        print("\nAvailability found in requested dates - skipping alternative search")
        # Return empty alternatives
        alternatives = {
            "same_weekend_earlier": [],
            "same_weekend_later": [],
            "shorter_stays": [],
            "earlier_dates": [],
            "later_dates": [],
            "different_nights": []
        }
        return main_results, alternatives

    # No availability in main search, run alternatives search using async
    alternatives = asyncio.run(search_alternatives_async(
        username, password, start_date, end_date, nights, adults, children
    ))

    return main_results, alternatives


def main(use_ai=None, direct_prompt=None):
    """Main function that uses AI or manual configuration"""
    
    # Make these global so we can modify them
    global START_DATE, END_DATE, NUM_NIGHTS, NUM_ADULTS, NUM_CHILDREN
    
    # Determine if we should use AI
    use_ai_mode = USE_AI_PROMPT if use_ai is None else use_ai
    
    # Try to use AI prompt if enabled
    if use_ai_mode:
        prompt = direct_prompt if direct_prompt else read_ai_prompt()
        
        if prompt:
            print("=" * 70)
            print("AI MODE: Natural Language Hotel Search")
            print("=" * 70)
            print(f"Your request: {prompt}")
            print("\nParsing with AI...")
            
            try:
                result = parse_prompt_with_ai(prompt)

                if result:
                    params = result['params']
                    holiday_info = result['holiday_info']

                    # Update configuration from AI response
                    if 'start_date' in params:
                        # Validate and override if holiday date is wrong
                        if holiday_info and params['start_date'] != holiday_info['start_date']:
                            print(f"WARNING: AI used wrong date {params['start_date']}, correcting to {holiday_info['start_date']}")
                            params['start_date'] = holiday_info['start_date']
                        START_DATE = datetime.strptime(params['start_date'], '%Y-%m-%d')
                    if 'num_nights' in params:
                        NUM_NIGHTS = int(params['num_nights'])
                    if 'num_adults' in params:
                        NUM_ADULTS = int(params['num_adults'])
                    if 'num_children' in params:
                        NUM_CHILDREN = int(params['num_children'])
                    if 'search_days' in params:
                        search_days = int(params['search_days'])
                        if search_days == 1:
                            # For specific date requests, search just that date
                            END_DATE = START_DATE + timedelta(days=NUM_NIGHTS)
                        else:
                            # For date range searches
                            END_DATE = START_DATE + timedelta(days=search_days)
                    else:
                        END_DATE = START_DATE + timedelta(days=7)
                    
                    print("\nAI Parsed Parameters:")
                    print(f"  Check-in: {START_DATE.strftime('%Y-%m-%d (%A)')}")
                    print(f"  Search until: {END_DATE.strftime('%Y-%m-%d')}")
                    print(f"  Nights: {NUM_NIGHTS}")
                    print(f"  Guests: {NUM_ADULTS} adults, {NUM_CHILDREN} children")
                    print("=" * 70)
                else:
                    print("AI parsing failed. Using default configuration...")
                    
            except Exception as e:
                print(f"Error using AI: {e}")
                print("Using default configuration...")
        else:
            if not direct_prompt:
                print("No ai_prompt.txt file found. Using default configuration...")

    print(f"\n{SYSTEM.upper()} Hotel Availability Scanner (Parallel Search)")
    print("=" * 70)
    print(f"System: {SYSTEM}")
    print(f"Date Range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"Stay Duration: {NUM_NIGHTS} nights")
    print(f"Guests: {NUM_ADULTS} adults, {NUM_CHILDREN} children")
    print("=" * 70)
    
    print("\nSearching for availability...")

    # Perform parallel search - main dates and all alternatives at once
    main_results, alternatives = search_all_parallel(
        username=USERNAME,
        password=PASSWORD,
        start_date=START_DATE,
        end_date=END_DATE,
        nights=NUM_NIGHTS,
        adults=NUM_ADULTS,
        children=NUM_CHILDREN
    )

    # Display results based on what was found
    # Note: search_availability_range already printed detailed results above
    # We just need to handle the alternatives display if no main availability
    if not main_results or len(main_results) == 0:
        # No main availability - show alternatives
        print("\n" + "=" * 70)
        print("NO AVAILABILITY IN REQUESTED DATES")
        print("Showing alternative options found...")
        print("=" * 70)
        
        # Display alternatives summary
        total_alternatives = sum(len(v) for v in alternatives.values())
        
        if total_alternatives == 0:
            print("\nX No alternative dates found with availability either")
        else:
            print(f"\n+ Found {total_alternatives} alternative option(s)")
            
            # Weekend alternatives (highest priority)
            if alternatives["same_weekend_earlier"] or alternatives["same_weekend_later"]:
                print("\n> SAME WEEKEND, DIFFERENT WEEK:")
                for alt in alternatives["same_weekend_earlier"]:
                    print(f"  * Week earlier: {alt['date_formatted']} ({alt['day_name']})")
                    for room in alt['rooms']:
                        print(f"    - Room {room['code']}: {room['available_count']} available @ {format_price(room['price'])} ILS")
                for alt in alternatives["same_weekend_later"]:
                    print(f"  * Week later: {alt['date_formatted']} ({alt['day_name']})")
                    for room in alt['rooms']:
                        print(f"    - Room {room['code']}: {room['available_count']} available @ {format_price(room['price'])} ILS")
            
            # Shorter stays
            if alternatives["shorter_stays"]:
                print("\n> SHORTER STAYS AT REQUESTED DATES:")
                for alt in alternatives["shorter_stays"]:
                    nights_count = alt['nights']
                    dates_list = alt.get('available_dates', [])
                    if dates_list:
                        print(f"  * {nights_count} night(s) available on:")
                        for date_info in dates_list:
                            print(f"    - {date_info['date_formatted']} ({date_info['day_name']})")
                            # Show first date's room details as example
                            if date_info == dates_list[0]:
                                for room in date_info['rooms'][:3]:  # Show first 3 rooms
                                    print(f"      • Room {room['code']}: {room['available_count']} available @ {format_price(room['price'])} ILS")
                                if len(date_info['rooms']) > 3:
                                    print(f"      • ... and {len(date_info['rooms']) - 3} more room types")
            
            # Different dates
            if alternatives["earlier_dates"] or alternatives["later_dates"]:
                print("\n> DIFFERENT DATES, SAME DURATION:")
                for alt in alternatives["earlier_dates"]:
                    print(f"  * {abs(alt['days_difference'])} days earlier: {alt['date_formatted']}")
                    for room in alt['rooms']:
                        print(f"    - Room {room['code']}: {room['available_count']} available @ {format_price(room['price'])} ILS")
                for alt in alternatives["later_dates"]:
                    print(f"  * {alt['days_difference']} days later: {alt['date_formatted']}")
                    for room in alt['rooms']:
                        print(f"    - Room {room['code']}: {room['available_count']} available @ {format_price(room['price'])} ILS")
            
            # Different duration
            if alternatives["different_nights"]:
                print("\n> DIFFERENT DURATION AT REQUESTED DATES:")
                for alt in alternatives["different_nights"]:
                    print(f"  * {alt['nights']} night(s): {alt['date_formatted']}")
                    for room in alt['rooms']:
                        print(f"    - Room {room['code']}: {room['available_count']} available @ {format_price(room['price'])} ILS")

    print("\nScan complete!")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Hotel Availability Scanner with AI")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI prompt parsing, use manual config")
    parser.add_argument("--prompt", type=str, help="Provide prompt directly instead of reading from file")
    parser.add_argument("--prompt-file", type=str, default="ai_prompt.txt", help="Path to prompt file (default: ai_prompt.txt)")
    
    args = parser.parse_args()
    
    # Handle arguments
    use_ai = not args.no_ai
    
    # If prompt provided directly, use it
    if args.prompt:
        main(use_ai=True, direct_prompt=args.prompt)
    else:
        # Update the prompt file location if specified
        if args.prompt_file != "ai_prompt.txt":
            # Read from custom file
            custom_prompt = read_ai_prompt(args.prompt_file)
            if custom_prompt:
                main(use_ai=True, direct_prompt=custom_prompt)
            else:
                print(f"Could not read prompt from {args.prompt_file}")
                main(use_ai=False)
        else:
            main(use_ai=use_ai)