#!/usr/bin/env python3
"""
Interactive Hotel Sales AI Agent

Simple interface to test the LLM-based tool planning system.
"""
import asyncio
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from agent.core.orchestrator import Orchestrator
from src.conversation import ContextManager

# ANSI Color codes for terminal output
class Colors:
    HEADER = '\033[95m'      # Magenta
    BLUE = '\033[94m'        # Blue
    CYAN = '\033[96m'        # Cyan
    GREEN = '\033[92m'       # Green
    YELLOW = '\033[93m'      # Yellow
    RED = '\033[91m'         # Red
    BOLD = '\033[1m'         # Bold
    UNDERLINE = '\033[4m'    # Underline
    END = '\033[0m'          # Reset

    # Combinations
    BOLD_GREEN = '\033[1m\033[92m'
    BOLD_CYAN = '\033[1m\033[96m'
    BOLD_YELLOW = '\033[1m\033[93m'
    BOLD_RED = '\033[1m\033[91m'
    BOLD_BLUE = '\033[1m\033[94m'


def colorize_json(data, indent_level=0):
    """Pretty print JSON with colors"""
    from datetime import date, datetime
    indent = "    " * indent_level

    if isinstance(data, dict):
        lines = [f"{Colors.CYAN}{{{Colors.END}"]
        items = list(data.items())
        for i, (key, value) in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            key_str = f'{indent}    {Colors.BOLD_YELLOW}"{key}":{Colors.END} '

            if isinstance(value, (dict, list)):
                lines.append(key_str)
                lines.append(colorize_json(value, indent_level + 1) + comma)
            elif isinstance(value, (date, datetime)):
                # Handle datetime/date objects as strings
                lines.append(f'{key_str}{Colors.GREEN}"{str(value)}"{Colors.END}{comma}')
            elif isinstance(value, str):
                lines.append(f'{key_str}{Colors.GREEN}"{value}"{Colors.END}{comma}')
            elif isinstance(value, bool):
                lines.append(f'{key_str}{Colors.BOLD_BLUE}{str(value).lower()}{Colors.END}{comma}')
            elif value is None:
                lines.append(f'{key_str}{Colors.RED}null{Colors.END}{comma}')
            else:
                lines.append(f'{key_str}{Colors.CYAN}{value}{Colors.END}{comma}')

        lines.append(f"{indent}{Colors.CYAN}}}{Colors.END}")
        return "\n".join(lines)

    elif isinstance(data, list):
        from datetime import date, datetime
        if not data:
            return f"{Colors.CYAN}[]{Colors.END}"

        lines = [f"{Colors.CYAN}[{Colors.END}"]
        for i, item in enumerate(data):
            comma = "," if i < len(data) - 1 else ""

            if isinstance(item, (dict, list)):
                lines.append(f"{indent}    " + colorize_json(item, indent_level + 1) + comma)
            elif isinstance(item, (date, datetime)):
                lines.append(f'{indent}    {Colors.GREEN}"{str(item)}"{Colors.END}{comma}')
            elif isinstance(item, str):
                lines.append(f'{indent}    {Colors.GREEN}"{item}"{Colors.END}{comma}')
            elif isinstance(item, bool):
                lines.append(f'{indent}    {Colors.BOLD_BLUE}{str(item).lower()}{Colors.END}{comma}')
            elif item is None:
                lines.append(f'{indent}    {Colors.RED}null{Colors.END}{comma}')
            else:
                lines.append(f'{indent}    {Colors.CYAN}{item}{Colors.END}{comma}')

        lines.append(f"{indent}{Colors.CYAN}]{Colors.END}")
        return "\n".join(lines)

    else:
        return str(data)


# Load environment variables
load_dotenv()

# Hotel credentials - Using MiniHotel for Oreldi71
PMS_TYPE = "minihotel"
PMS_USERNAME = os.getenv("MINIHOTEL_USERNAME", "visitguide")
PMS_PASSWORD = os.getenv("MINIHOTEL_PASSWORD", "visg#!71R")
HOTEL_ID = "wayinn"  # Hotel GDS code
URL_CODE = "oreldirot"  # URL code for MiniHotel booking links
USE_SANDBOX = False


async def main():
    """Main interactive loop"""
    print(f"{Colors.BOLD_CYAN}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD_CYAN}🏨 Hotel Sales AI Agent - Interactive Mode{Colors.END}")
    print(f"{Colors.BOLD_CYAN}{'=' * 70}{Colors.END}")
    print()
    print(f"{Colors.YELLOW}Initializing orchestrator and conversation state...{Colors.END}")

    # Create orchestrator with optional calendar pre-run optimization
    prerun_calendar = os.getenv("PRERUN_CALENDAR_TOOL", "false").lower() == "true"
    orchestrator = Orchestrator.create_default(prerun_calendar_tool=prerun_calendar)

    if prerun_calendar:
        print(f"{Colors.GREEN}⚡ Calendar pre-run optimization: ENABLED{Colors.END}")

    # Create conversation state with session ID
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    context_manager = ContextManager.create(
        session_id=session_id,
        hotel_id=HOTEL_ID,
        pms_type=PMS_TYPE
    )

    print(f"{Colors.BOLD_GREEN}✓ Orchestrator ready!{Colors.END}")
    print(f"{Colors.BOLD_GREEN}✓ Conversation state initialized (session: {session_id}){Colors.END}")
    print()
    print(f"{Colors.CYAN}Type your message to see how the LLM plans tool execution.{Colors.END}")
    print(f"{Colors.CYAN}Type 'quit' or 'exit' to stop.{Colors.END}")
    print(f"{Colors.CYAN}Type 'status' to see booking context status.{Colors.END}")
    print(f"{Colors.CYAN}Type 'reset' to start a new conversation session.{Colors.END}")
    print()
    print(f"{Colors.BLUE}{'-' * 70}{Colors.END}")
    print()

    while True:
        # Get user input
        try:
            message = input(f"{Colors.BOLD_BLUE}You: {Colors.END}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")
            break

        if not message:
            continue

        if message.lower() in ['quit', 'exit', 'q']:
            print(f"\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")
            break

        # Handle special commands
        if message.lower() == 'status':
            booking_status = context_manager.get_booking_status()
            context_stats = context_manager.get_context_stats()

            print(f"\n{Colors.BOLD_CYAN}📊 SESSION STATUS{Colors.END}")
            print(f"{Colors.CYAN}Session ID: {session_id}{Colors.END}")
            print(f"{Colors.CYAN}Total turns: {context_stats['total_turns']}{Colors.END}")
            print(f"{Colors.CYAN}Total messages: {context_stats['total_messages']}{Colors.END}")
            print(f"{Colors.CYAN}Total tools executed: {context_stats['total_tool_executions']}{Colors.END}")
            print()
            print(f"{Colors.BOLD_CYAN}📝 BOOKING STATUS{Colors.END}")
            print(f"{Colors.YELLOW}Ready for booking: {booking_status['ready_for_booking']}{Colors.END}")
            if booking_status['missing_info']:
                print(f"{Colors.RED}Missing: {', '.join(booking_status['missing_info'])}{Colors.END}")
            print()
            print(f"{Colors.BOLD_CYAN}🎫 BOOKING CONTEXT{Colors.END}")
            print(colorize_json(booking_status['booking_context'], indent_level=0))
            print()
            continue

        if message.lower() == 'reset':
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
            context_manager = ContextManager.create(
                session_id=session_id,
                hotel_id=HOTEL_ID,
                pms_type=PMS_TYPE
            )
            print(f"\n{Colors.BOLD_GREEN}✓ Started new session: {session_id}{Colors.END}\n")
            continue

        print()
        print(f"{Colors.BOLD_YELLOW}{'=' * 70}{Colors.END}")
        print(f"{Colors.BOLD_YELLOW}📋 PLANNING & EXECUTION{Colors.END}")
        print(f"{Colors.BOLD_YELLOW}{'=' * 70}{Colors.END}")

        try:
            # Process message with debug output and conversation state
            result = await orchestrator.process_message(
                message=message,
                pms_type=PMS_TYPE,
                pms_username=PMS_USERNAME,
                pms_password=PMS_PASSWORD,
                hotel_id=HOTEL_ID,
                pms_use_sandbox=USE_SANDBOX,
                pms_url_code=URL_CODE,
                context_manager=context_manager,
                debug=True
            )

            # Display natural language response
            print()
            print(f"{Colors.BOLD_GREEN}{'=' * 70}{Colors.END}")
            print(f"{Colors.BOLD_GREEN}💬 ASSISTANT RESPONSE{Colors.END}")
            print(f"{Colors.BOLD_GREEN}{'=' * 70}{Colors.END}")
            print()

            # Display the generated response
            if result.get('response'):
                print(f"{Colors.CYAN}{result['response']}{Colors.END}")
            else:
                # Fallback if no response was generated
                print(f"{Colors.YELLOW}{result['action']}{Colors.END}")

            print()

            # Show booking progress if making progress
            booking_status = context_manager.get_booking_status()
            if booking_status['booking_context']['check_in'] or booking_status['booking_context']['selected_room_code']:
                print(f"{Colors.BOLD_CYAN}🎫 Booking Progress:{Colors.END}")
                if booking_status['ready_for_booking']:
                    print(f"  {Colors.BOLD_GREEN}✓ Ready to book!{Colors.END}")
                else:
                    print(f"  {Colors.YELLOW}Still collecting information...{Colors.END}")
                    if booking_status['missing_info']:
                        print(f"  {Colors.YELLOW}Missing: {', '.join(booking_status['missing_info'])}{Colors.END}")
                print()

            # Technical details (collapsed by default)
            print(f"{Colors.BOLD_CYAN}📊 Technical Details:{Colors.END}")
            print(f"  {Colors.YELLOW}Tools executed: {len(result['tools'])}{Colors.END}")
            print(f"  {Colors.CYAN}Action: {result['action']}{Colors.END}")

        except Exception as e:
            print(f"\n{Colors.BOLD_RED}❌ Error: {e}{Colors.END}")
            import traceback
            print(f"{Colors.RED}", end="")
            traceback.print_exc()
            print(f"{Colors.END}", end="")

        print()
        print(f"{Colors.BLUE}{'-' * 70}{Colors.END}")
        print()


if __name__ == "__main__":
    print()
    asyncio.run(main())
