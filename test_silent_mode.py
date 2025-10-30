#!/usr/bin/env python3
"""
Test script to verify silent mode works correctly.

Expected output in silent mode (using echo and timeout):
- ONLY bot responses
- NO logs
- NO debug output
- NO progress messages
"""

import subprocess
import sys

def test_silent_mode():
    """Test that silent mode only shows bot responses"""

    print("=" * 70)
    print("SILENT MODE TEST")
    print("=" * 70)
    print("\nThis test will:")
    print("1. Start cli_interactive.py in silent mode")
    print("2. Send a test message")
    print("3. Wait 10 seconds for response")
    print("4. Check if ANY unwanted output appears")
    print("\nExpected: ONLY the bot response should appear")
    print("=" * 70)
    print()

    # Test command: echo message, wait, then quit
    test_message = "Do you have availability for tomorrow?"

    cmd = f'(echo "{test_message}" && sleep 10 && echo "quit") | timeout 15 python3 cli_interactive.py -s'

    print("Running test command...")
    print(f"Command: {cmd}")
    print("=" * 70)
    print()

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=20
        )

        output = result.stdout
        errors = result.stderr

        print("CAPTURED OUTPUT:")
        print("=" * 70)
        print(output)
        print("=" * 70)
        print()

        if errors:
            print("CAPTURED ERRORS:")
            print("=" * 70)
            print(errors)
            print("=" * 70)
            print()

        # Check for unwanted output patterns
        unwanted_patterns = [
            "[Runtime]",
            "[Orchestrator]",
            "[SessionManager]",
            "[Tool]",
            "RESPONSE GENERATOR PROMPT",
            "===",
            "🔄",
            "⚙️",
            "Wave",
            "INFO:",
            "DEBUG:",
            "WARNING:",
            "processing",
            "executing",
            "tool_",
            "Completed",
        ]

        issues_found = []
        for pattern in unwanted_patterns:
            if pattern in output or pattern in errors:
                issues_found.append(pattern)

        print("=" * 70)
        print("TEST RESULTS")
        print("=" * 70)

        if issues_found:
            print("❌ FAILED - Found unwanted output patterns:")
            for pattern in issues_found:
                print(f"  - {pattern}")
        else:
            print("✅ PASSED - Only bot response appears (no logs/debug output)")

        print("=" * 70)

        return len(issues_found) == 0

    except subprocess.TimeoutExpired:
        print("❌ TEST TIMED OUT")
        return False
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        return False


if __name__ == "__main__":
    success = test_silent_mode()
    sys.exit(0 if success else 1)
