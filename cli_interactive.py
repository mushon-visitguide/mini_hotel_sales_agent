#!/usr/bin/env python3
"""
Interactive CLI with interruption support.

Simple wrapper that adds non-blocking input to the existing agent.
Run: python3 cli_interactive.py
      python3 cli_interactive.py -s  (silent mode - only responses)
"""
import asyncio
import os
import uuid
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

from agent.core.orchestrator import Orchestrator
from agent.core.session_manager import SessionManager
from agent.core.intent_classifier import IntentClassifier
from agent.core.progress_notifier import ProgressNotifier
from agent.core.hooks import setup_all_hooks
from src.conversation import ContextManager

# Load environment
load_dotenv()

# ANSI Colors
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    BOLD_CYAN = '\033[1m\033[96m'
    BOLD_GREEN = '\033[1m\033[92m'
    END = '\033[0m'

# Hotel credentials
PMS_TYPE = "minihotel"
PMS_USERNAME = os.getenv("MINIHOTEL_USERNAME", "visitguide")
PMS_PASSWORD = os.getenv("MINIHOTEL_PASSWORD", "visg#!71R")
HOTEL_ID = "wayinn"
URL_CODE = "oreldirot"
USE_SANDBOX = False
DEFAULT_PHONE_NUMBER = "052-123-4567"


async def async_input(prompt=""):
    """
    Non-blocking async input using executor.
    Based on: https://stackoverflow.com/a/65439376
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


async def main_interactive(silent_mode=False):
    """Main loop with interruption support"""

    # Configure logging based on mode
    if silent_mode:
        # Silent mode: suppress all logs except CRITICAL errors
        logging.basicConfig(level=logging.CRITICAL)
        # Also suppress logs from all modules
        for logger_name in ['agent', 'src', 'httpx', 'httpcore']:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    else:
        # Normal mode: show INFO and above
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if not silent_mode:
        print(f"\n{Colors.BOLD_CYAN}{'─' * 70}{Colors.END}")
        print(f"{Colors.BOLD_CYAN}🏨 Hotel AI - Interactive CLI{Colors.END}")
        print(f"{Colors.BOLD_CYAN}{'─' * 70}{Colors.END}\n")

    # Setup
    setup_all_hooks(verbose=False, enable_performance_monitoring=True)

    orchestrator = Orchestrator.create_default(prerun_calendar_tool=True)
    intent_classifier = IntentClassifier()
    session_manager = SessionManager(intent_classifier=intent_classifier)

    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    context_manager = ContextManager.create(
        session_id=session_id,
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE,
        phone_number=DEFAULT_PHONE_NUMBER
    )

    # Progress notifier (only if not silent mode)
    async def send_progress(user_id: str, text: str):
        if not silent_mode:
            print(f"\n{Colors.YELLOW}🔄 {text}{Colors.END}")

    progress_notifier = ProgressNotifier(
        send_message=lambda text: send_progress(DEFAULT_PHONE_NUMBER, text)
    )
    progress_notifier.setup()
    orchestrator.progress_notifier = progress_notifier

    if not silent_mode:
        print(f"{Colors.BOLD_GREEN}✅ Ready!{Colors.END}")
        print(f"{Colors.BOLD_GREEN}✨ You can type while processing - messages will interrupt!{Colors.END}")
        print(f"{Colors.CYAN}Type 'quit' to exit, 'reset' for new session{Colors.END}")
        print(f"{Colors.CYAN}{'─' * 70}{Colors.END}\n")

    # PMS credentials
    pms_creds = {
        'pms_type': PMS_TYPE,
        'pms_username': PMS_USERNAME,
        'pms_password': PMS_PASSWORD,
        'hotel_id': HOTEL_ID,
        'pms_use_sandbox': USE_SANDBOX,
        'pms_url_code': URL_CODE
    }

    async def send_msg(user_id: str, text: str):
        if not silent_mode:
            print(f"\n{Colors.YELLOW}💬 {text}{Colors.END}\n")

    async def process_in_background(message: str):
        """Process message in background - doesn't block input"""
        try:
            if not silent_mode:
                print(f"\n{Colors.YELLOW}{'─' * 70}{Colors.END}")
                print(f"{Colors.YELLOW}⚙️  Processing...{Colors.END}")
                print(f"{Colors.YELLOW}{'─' * 70}{Colors.END}")

            result = await session_manager.process_message(
                user_id=DEFAULT_PHONE_NUMBER,
                message=message,
                orchestrator=orchestrator,
                send_message=send_msg,
                pms_credentials=pms_creds,
                context_manager=context_manager,
                debug=not silent_mode  # Only debug in non-silent mode
            )

            if not silent_mode:
                print(f"\n{Colors.BOLD_GREEN}{'─' * 70}{Colors.END}")
                print(f"{Colors.BOLD_GREEN}🤖 ASSISTANT{Colors.END}")
                print(f"{Colors.BOLD_GREEN}{'─' * 70}{Colors.END}")

            if result.get('status_check'):
                if not silent_mode:
                    print(f"{Colors.CYAN}(Status check - operation continues){Colors.END}")
            elif result.get('cancelled'):
                if not silent_mode:
                    print(f"{Colors.YELLOW}⚠️  Cancelled - processing new request{Colors.END}")
            elif result.get('response'):
                # Always print response (even in silent mode)
                print(f"{Colors.CYAN}{result['response']}{Colors.END}")

            if not silent_mode:
                print(f"{Colors.CYAN}{'─' * 70}{Colors.END}\n")

        except Exception as e:
            if not silent_mode:
                print(f"\n{Colors.RED}❌ Error: {e}{Colors.END}\n")

    # Main input loop - always available for typing
    try:
        while True:
            # Get input (this waits for user but doesn't block)
            # Note: Colors only apply to >> itself, not to user's typed text
            message = await async_input(f"\n{Colors.BOLD_CYAN}>> {Colors.END}")

            if not message or not message.strip():
                continue

            message = message.strip()

            # Handle quit
            if message.lower() in ['quit', 'exit', 'q']:
                if not silent_mode:
                    print(f"\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")
                break

            # Handle reset
            if message.lower() == 'reset':
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
                context_manager = ContextManager.create(
                    session_id=session_id,
                    hotel_id=HOTEL_ID,
                    pms_type=PMS_TYPE,
                    phone_number=DEFAULT_PHONE_NUMBER
                )
                if not silent_mode:
                    print(f"\n{Colors.BOLD_GREEN}{'─' * 70}{Colors.END}")
                    print(f"{Colors.BOLD_GREEN}🔄 New session started{Colors.END}")
                    print(f"{Colors.BOLD_GREEN}{'─' * 70}{Colors.END}\n")
                continue

            # Process in background - DON'T await, so prompt returns immediately!
            # This allows typing the next message while processing
            asyncio.create_task(process_in_background(message))

    except KeyboardInterrupt:
        if not silent_mode:
            print(f"\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Hotel AI Agent - Interactive CLI with interruption support"
    )
    parser.add_argument(
        "-s", "--silent",
        action="store_true",
        help="Silent mode - only show LLM responses, no extra output"
    )
    args = parser.parse_args()

    try:
        asyncio.run(main_interactive(silent_mode=args.silent))
    except KeyboardInterrupt:
        if not silent_mode:
            print(f"\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")
