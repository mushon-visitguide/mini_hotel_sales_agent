#!/usr/bin/env python3
"""
Interactive Hotel Sales AI Agent

Simple interface to test the LLM-based tool planning system.
"""
import asyncio
import os
import json
from dotenv import load_dotenv
from agent.core.orchestrator import Orchestrator

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
HOTEL_ID = "Oreldi71"  # Hotel GDS code
URL_CODE = "oreldirot"  # URL code for MiniHotel booking links
USE_SANDBOX = False


async def main():
    """Main interactive loop"""
    print(f"{Colors.BOLD_CYAN}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD_CYAN}🏨 Hotel Sales AI Agent - Interactive Mode{Colors.END}")
    print(f"{Colors.BOLD_CYAN}{'=' * 70}{Colors.END}")
    print()
    print(f"{Colors.YELLOW}Initializing orchestrator...{Colors.END}")

    # Create orchestrator
    orchestrator = Orchestrator.create_default()

    print(f"{Colors.BOLD_GREEN}✓ Orchestrator ready!{Colors.END}")
    print()
    print(f"{Colors.CYAN}Type your message to see how the LLM plans tool execution.{Colors.END}")
    print(f"{Colors.CYAN}Type 'quit' or 'exit' to stop.{Colors.END}")
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

        print()
        print(f"{Colors.BOLD_YELLOW}{'=' * 70}{Colors.END}")
        print(f"{Colors.BOLD_YELLOW}📋 PLANNING & EXECUTION{Colors.END}")
        print(f"{Colors.BOLD_YELLOW}{'=' * 70}{Colors.END}")

        try:
            # Process message with debug output
            result = await orchestrator.process_message(
                message=message,
                pms_type=PMS_TYPE,
                pms_username=PMS_USERNAME,
                pms_password=PMS_PASSWORD,
                hotel_id=HOTEL_ID,
                pms_use_sandbox=USE_SANDBOX,
                pms_url_code=URL_CODE,
                debug=True
            )

            # Print summary
            print()
            print(f"{Colors.BOLD_GREEN}{'=' * 70}{Colors.END}")
            print(f"{Colors.BOLD_GREEN}📊 RESULT SUMMARY{Colors.END}")
            print(f"{Colors.BOLD_GREEN}{'=' * 70}{Colors.END}")
            print(f"\n{Colors.BOLD_CYAN}🎯 Action:{Colors.END} {Colors.YELLOW}{result['action']}{Colors.END}")
            print(f"\n{Colors.BOLD_CYAN}💭 Reasoning:{Colors.END} {Colors.CYAN}{result['reasoning']}{Colors.END}")

            print(f"\n{Colors.BOLD_CYAN}🔧 Tools Executed:{Colors.END} {Colors.YELLOW}{len(result['tools'])}{Colors.END}")
            for tool_id in result['tools']:
                if tool_id in result['results']:
                    print(f"  {Colors.GREEN}✅ {tool_id}{Colors.END}")
                else:
                    print(f"  {Colors.RED}❌ {tool_id}{Colors.END}")

            print(f"\n{Colors.BOLD_CYAN}📦 Slots Extracted:{Colors.END}")
            for key, value in result['slots'].items():
                if value and value != [] and value != 2:  # Skip empty/default values
                    print(f"  {Colors.YELLOW}- {key}:{Colors.END} {Colors.CYAN}{value}{Colors.END}")

            print(f"\n{Colors.BOLD_CYAN}📋 Results:{Colors.END}")
            for tool_id, tool_result in result['results'].items():
                if isinstance(tool_result, dict) and 'error' in tool_result:
                    print(f"\n  {Colors.RED}❌ {tool_id}:{Colors.END}")
                    print(f"    {Colors.BOLD_RED}{tool_result['error']}{Colors.END}")
                else:
                    # Show full result with pretty formatting
                    print(f"\n  {Colors.GREEN}✅ {Colors.BOLD_GREEN}{tool_id}:{Colors.END}")
                    if isinstance(tool_result, dict):
                        print(colorize_json(tool_result, indent_level=1))
                    elif isinstance(tool_result, list):
                        print(colorize_json(tool_result, indent_level=1))
                    else:
                        print(f"    {Colors.CYAN}{tool_result}{Colors.END}")

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
