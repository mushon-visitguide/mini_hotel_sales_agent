#!/usr/bin/env python3
"""
Batch Conversation Runner

Runs sample conversations from chat_conversations.md and generates:
1. conversation_history.txt - Human-readable chat log
2. detailed_log.txt - Technical details, tools, errors

Usage:
    python batch_conversation.py [conversation_number]

Examples:
    python batch_conversation.py 1        # Run conversation 1
    python batch_conversation.py all      # Run all conversations
"""
import asyncio
import os
import sys
import re
from datetime import datetime
from dotenv import load_dotenv
from agent.core.orchestrator import Orchestrator
from src.conversation import ContextManager

# Load environment variables
load_dotenv()

# Hotel credentials
PMS_TYPE = "minihotel"
PMS_USERNAME = os.getenv("MINIHOTEL_USERNAME", "visitguide")
PMS_PASSWORD = os.getenv("MINIHOTEL_PASSWORD", "visg#!71R")
HOTEL_ID = "wayinn"
URL_CODE = "oreldirot"
USE_SANDBOX = False
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


class ConversationLogger:
    """Manages output to both history and detailed log files"""

    def __init__(self, conversation_num: int, output_dir: str = "logs"):
        self.conversation_num = conversation_num
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.history_file = os.path.join(output_dir, f"conv{conversation_num}_history_{timestamp}.txt")
        self.log_file = os.path.join(output_dir, f"conv{conversation_num}_log_{timestamp}.txt")

        # Initialize files with headers
        with open(self.history_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"CONVERSATION {conversation_num} - HISTORY\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"CONVERSATION {conversation_num} - DETAILED LOG\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

    def log_user_message(self, message: str):
        """Log user message to history file"""
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(f"[USER]\n{message}\n\n")

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("-" * 80 + "\n")
            f.write(f"[USER MESSAGE]\n{message}\n")
            f.write("-" * 80 + "\n\n")

    def log_assistant_response(self, response: str):
        """Log assistant response to history file"""
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(f"[ASSISTANT]\n{response}\n\n")

    def log_planning(self, plan_data: dict):
        """Log tool planning details to log file"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("[PLANNING]\n")
            tools = plan_data.get('tools', [])
            f.write(f"Tools to execute: {len(tools)}\n")
            for tool in tools:
                # Handle both string and dict tool entries
                if isinstance(tool, dict):
                    tool_name = tool.get('tool', 'unknown')
                else:
                    tool_name = str(tool)
                f.write(f"  - {tool_name}\n")
            f.write("\n")

    def log_tool_execution(self, tool_name: str, args: dict, result: any):
        """Log tool execution details to log file"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[TOOL EXECUTION: {tool_name}]\n")
            f.write(f"Arguments:\n")
            for key, value in args.items():
                f.write(f"  {key}: {value}\n")
            f.write(f"\nResult:\n{str(result)[:500]}...\n")  # Truncate long results
            f.write("\n")

    def log_response_generation(self, response: str, result_data: dict):
        """Log response generation to log file"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("[RESPONSE GENERATION]\n")
            f.write(f"Action: {result_data.get('action', 'unknown')}\n")
            f.write(f"Tools executed: {len(result_data.get('tools', []))}\n")
            f.write(f"Response length: {len(response)} chars\n")
            f.write(f"\nResponse:\n{response}\n\n")

    def log_error(self, error: Exception, context: str = ""):
        """Log error to both files"""
        error_msg = f"ERROR: {str(error)}"
        if context:
            error_msg = f"ERROR in {context}: {str(error)}"

        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(f"[ERROR]\n{error_msg}\n\n")

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[ERROR]\n{error_msg}\n")
            import traceback
            f.write(f"\nTraceback:\n{traceback.format_exc()}\n\n")

    def log_summary(self, stats: dict):
        """Log final summary to log file"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("[SUMMARY]\n")
            f.write(f"Total turns: {stats.get('turns', 0)}\n")
            f.write(f"Total tools executed: {stats.get('tools_executed', 0)}\n")
            f.write(f"Errors: {stats.get('errors', 0)}\n")
            f.write(f"Duration: {stats.get('duration', 0):.2f}s\n")
            f.write("=" * 80 + "\n")

    def print_summary(self):
        """Print summary of generated files"""
        print(f"\n{'=' * 80}")
        print(f"✓ Conversation {self.conversation_num} completed!")
        print(f"{'=' * 80}")
        print(f"\nGenerated files:")
        print(f"  📝 History: {self.history_file}")
        print(f"  🔍 Log:     {self.log_file}")
        print(f"\nView with:")
        print(f"  cat {self.history_file}")
        print(f"  cat {self.log_file}")
        print()


def parse_conversations(md_file: str = "docs/chat_conversations.md") -> dict:
    """Parse conversations from markdown file"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by conversation sections
    conversations = {}

    # Pattern to match conversation sections
    pattern = r'## Chat Conversation (\d+):(.*?)\n\n(.*?)(?=\n---\n|\Z)'
    matches = re.finditer(pattern, content, re.DOTALL)

    for match in matches:
        conv_num = int(match.group(1))
        title = match.group(2).strip()
        conv_content = match.group(3).strip()

        # Parse guest/agent messages
        messages = []
        lines = conv_content.split('\n')
        current_role = None
        current_message = []

        for line in lines:
            if line.startswith('**Guest:**'):
                if current_role and current_message:
                    messages.append({
                        'role': current_role,
                        'content': ' '.join(current_message)
                    })
                current_role = 'user'
                current_message = [line.replace('**Guest:**', '').strip()]
            elif line.startswith('**Agent:**'):
                if current_role and current_message:
                    messages.append({
                        'role': current_role,
                        'content': ' '.join(current_message)
                    })
                current_role = 'assistant'
                current_message = [line.replace('**Agent:**', '').strip()]
            elif line.strip() and current_role:
                current_message.append(line.strip())

        # Add last message
        if current_role and current_message:
            messages.append({
                'role': current_role,
                'content': ' '.join(current_message)
            })

        conversations[conv_num] = {
            'title': title,
            'messages': messages
        }

    return conversations


async def run_conversation(conversation_num: int, messages: list):
    """Run a single conversation through the orchestrator"""
    print(f"\n{'=' * 80}")
    print(f"Running Conversation {conversation_num}")
    print(f"{'=' * 80}\n")

    logger = ConversationLogger(conversation_num)

    # Initialize orchestrator and context
    orchestrator = Orchestrator.create_default(prerun_calendar_tool=False)
    session_id = f"batch_conv{conversation_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    context_manager = ContextManager.create(
        session_id=session_id,
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE,
        phone_number=DEFAULT_PHONE_NUMBER,
        host_guidance_prompt=DEFAULT_HOST_GUIDANCE
    )

    # Initialize with default guest information
    context_manager.update_booking_context({
        "guest_first_name": DEFAULT_FIRST_NAME,
        "guest_last_name": DEFAULT_LAST_NAME,
        "guest_phone": DEFAULT_PHONE_NUMBER
    })

    stats = {
        'turns': 0,
        'tools_executed': 0,
        'errors': 0,
        'start_time': datetime.now()
    }

    # Process each user message (skip assistant messages from reference)
    for msg in messages:
        if msg['role'] == 'user':
            stats['turns'] += 1
            user_message = msg['content']

            print(f"Turn {stats['turns']}: {user_message[:60]}...")
            logger.log_user_message(user_message)

            try:
                # Process message
                result = await orchestrator.process_message(
                    message=user_message,
                    pms_type=PMS_TYPE,
                    pms_username=PMS_USERNAME,
                    pms_password=PMS_PASSWORD,
                    hotel_id=HOTEL_ID,
                    pms_use_sandbox=USE_SANDBOX,
                    pms_url_code=URL_CODE,
                    context_manager=context_manager,
                    debug=False  # Set to True for more verbose logging
                )

                # Log planning
                logger.log_planning(result)

                # Log tool executions
                for tool in result.get('tools', []):
                    stats['tools_executed'] += 1
                    # Note: We'd need to capture individual tool results from orchestrator
                    # For now, just log that tools were executed

                # Log response
                response = result.get('response', result.get('action', 'No response'))
                logger.log_assistant_response(response)
                logger.log_response_generation(response, result)

                print(f"  ✓ Response generated ({len(response)} chars)")

            except Exception as e:
                stats['errors'] += 1
                print(f"  ✗ Error: {str(e)}")
                logger.log_error(e, f"Turn {stats['turns']}")

    # Calculate duration and log summary
    stats['duration'] = (datetime.now() - stats['start_time']).total_seconds()
    logger.log_summary(stats)
    logger.print_summary()

    return stats


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python batch_conversation.py [conversation_number|all]")
        print("\nExamples:")
        print("  python batch_conversation.py 1       # Run conversation 1")
        print("  python batch_conversation.py all     # Run all conversations")
        sys.exit(1)

    arg = sys.argv[1]

    # Parse all conversations
    print("Parsing conversations from docs/chat_conversations.md...")
    conversations = parse_conversations()
    print(f"Found {len(conversations)} conversations\n")

    if arg.lower() == 'all':
        # Run all conversations
        for conv_num in sorted(conversations.keys()):
            conv_data = conversations[conv_num]
            print(f"\nConversation {conv_num}: {conv_data['title']}")
            await run_conversation(conv_num, conv_data['messages'])
    else:
        # Run specific conversation
        try:
            conv_num = int(arg)
            if conv_num not in conversations:
                print(f"Error: Conversation {conv_num} not found")
                print(f"Available: {sorted(conversations.keys())}")
                sys.exit(1)

            conv_data = conversations[conv_num]
            print(f"Conversation {conv_num}: {conv_data['title']}")
            await run_conversation(conv_num, conv_data['messages'])

        except ValueError:
            print(f"Error: Invalid conversation number '{arg}'")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
