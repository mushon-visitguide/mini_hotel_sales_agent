#!/usr/bin/env python3
"""
Simulate the Hanukkah pricing issue scenario:
1. Ask about rooms for 2 adults and 3 kids for Hanukkah
2. Ask about amenities (informative)
3. Ask about breakfast options (informative)
4. Ask about check-in time (informative)
5. Ask what if we remove a child, what is the best room?
6. Ask for the price
"""
import asyncio
import os
from dotenv import load_dotenv
from agent.core.orchestrator import Orchestrator
from src.conversation import ContextManager

load_dotenv()

PMS_TYPE = "minihotel"
PMS_USERNAME = os.getenv("MINIHOTEL_USERNAME")
PMS_PASSWORD = os.getenv("MINIHOTEL_PASSWORD")
HOTEL_ID = "wayinn"
URL_CODE = "thewayinn"
DEFAULT_PHONE_NUMBER = "052-123-4567"  # Default guest phone number
DEFAULT_FIRST_NAME = "Test"  # Default guest first name
DEFAULT_LAST_NAME = "Guest"  # Default guest last name

# Host-specific guidance for response generation (HIGHEST PRIORITY)
DEFAULT_HOST_GUIDANCE = """
תענה תמיד בידידותיות ובדרך שתגרום לאורח לקבל תחושה של יחס אישי
אל תשתמש במונח "מלון" אלא "מתחם אירוח"
במידה ושואלים על הזמנת טיפולים\עיסויים תפנה לסוכן שאלות ותשובות


בכל פעם שאתה מציג זמינות בבקשה תוסיף בתשובה שלך שמי שזמין באתר הישיר של המלון מקבל *7 אחוז הנחה* על המחיר הסופי, גם אם יש זמינות וגם אם אין, שים את ההערה ליד הלינק להזמנה בצורה מודגשת עם emoji
וגם אם אין זמינות זה הלינק לאתר, שים את זה כשאתה מציין שיש הנחה באתר - https://thewayinn.co.il/
כשאתה נותן מחירים וזמינות תתן קודם את המחיר ללילה לזוג ותציין בסוגריים את כמות האנשים המקסימלית בכל חדר. במידה ומבקשים יותר מלילה אחד, לאחר שנתת את המחיר ללילה לזוג תסכם כמה סך הכל יצא לכל הלילות כולל המיטות הנוספות על פי הדרישה. לדוגמא:
גבורה (מקסימום זוג) - 1,100 ש"ח ללילה לזוג. סה"כ ל2 לילות: 2,200 ש"ח

במידה ומבקשים חדר ליותר מזוג, לאחר שתציין מה המחיר ללילה לזוג תוסיף את העלות לכל אדם נוסף ללילה ובסוף תחשב את העלות הסופית כולל המיטות הנוספות כפול מספר הלילות. לדוגמא, אם ביקשו סוויטה לזוג + 3:
מלכות (מקסימום זוג +5) - 1,400 ש"ח ללילה לזוג + 200 ש"ח לכל מיטה נוספת. סה"כ 2 לילות ל5 נפשות: 4,000 ש"ח

המחירים שאתה מקבל הם לזוג בלבד ללא ההנחה, אנא ציין זאת, עבור כל מיטה נוספת, ילד או מבוגר תוסיף 200 שח לסכום, כלומר 2 ילדים זה 400 תוספת למשל

תנסה לתת תשובה באורך בינוני קצר
אם אין זמינות, תוסיף שיכול להיות שיש מינימום של 2 לילות ושכדאי לנסות שוב לבדוק זמינות ל2 לילות
רק אם מבקשים זמינות כולל בעל חיים, לדוגמא, כלבה קטנה, אוגר, חתול, חמוס או כל שאר ההולכים על 4 צריך לציין שלצערנו אין אפשרות להכניס בעלי חיים למתחם
הלינה לא כוללת ארוחות והמתחם לא מגיש ארוחות אלא לקבוצות של 25 איש ומעלה בהזמנה מראש

*שים לב אולי זה מבלבל אבל יש לנו חדר אחד מכל סוג, המידע שאתה מקבל מה api של הזמינויות מטעה, יש רק חדר אחד מכל סוג חדר, התאם כמות אנשים בהתאם*
בנוסף שים לב מחירי החדרים המוצעים הם כוללים מע״מ

when you dont know or dont have any tool to use suggest calling the office 052-6881116
"""

async def simulate_conversation():
    """Simulate the Hanukkah pricing scenario"""

    orchestrator = Orchestrator.create_default()
    context = ContextManager.create(
        session_id="hanukkah_pricing_test",
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE,
        phone_number=DEFAULT_PHONE_NUMBER,
        host_guidance_prompt=DEFAULT_HOST_GUIDANCE
    )

    # Initialize with default guest information
    context.update_booking_context({
        "guest_first_name": DEFAULT_FIRST_NAME,
        "guest_last_name": DEFAULT_LAST_NAME,
        "guest_phone": DEFAULT_PHONE_NUMBER
    })

    print("=" * 70)
    print("SIMULATING HANUKKAH PRICING SCENARIO")
    print("=" * 70)
    print()

    questions = [
        "Do you have rooms for 2 adults and 3 kids for Hanukkah?",
        "What amenities are included?",
        "Do you have breakfast options?",
        "What's the check-in time?",
        "What if we remove a child, what is the best room?",
        "What's the price?"
    ]

    for i, question in enumerate(questions, 1):
        print(f"TURN {i}: {question}")
        print("-" * 70)

        result = await orchestrator.process_message(
            message=question,
            pms_type=PMS_TYPE,
            pms_username=PMS_USERNAME,
            pms_password=PMS_PASSWORD,
            hotel_id=HOTEL_ID,
            pms_use_sandbox=False,
            pms_url_code=URL_CODE,
            context_manager=context,
            debug=False
        )

        response = result.get('response', 'NO RESPONSE')
        print(f"User: {question}")
        print(f"Assistant: {response}")
        print()

    print("=" * 70)
    print("ISSUE CHECK - Turn 6 (Price question):")
    print("Does the final response mention actual prices?")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(simulate_conversation())
