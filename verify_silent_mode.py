#!/usr/bin/env python3
"""
Verify that silent mode is properly configured.
This script checks for any print statements or logs that bypass silent mode.
"""
import subprocess
import sys

def check_file_for_unwanted_prints(filepath, allowed_patterns=None):
    """
    Check a file for print statements that don't check silent_mode or debug flags.

    Args:
        filepath: Path to the file to check
        allowed_patterns: List of patterns that are OK (e.g., ["if debug:", "if not silent_mode:"])
    """
    allowed_patterns = allowed_patterns or ["if debug:", "if not silent_mode:"]

    issues = []

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        in_guarded_block = False
        indent_level = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track if we're inside a guarded block
            if any(pattern in line for pattern in allowed_patterns):
                in_guarded_block = True
                indent_level = len(line) - len(line.lstrip())
                continue

            # Check if we've exited the guarded block
            if in_guarded_block:
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and stripped and not stripped.startswith('#'):
                    in_guarded_block = False

            # Check for print statements
            if 'print(' in stripped and not stripped.startswith('#'):
                # Ignore if inside a guarded block
                if in_guarded_block:
                    continue

                # Ignore if it's a comment
                if '#' in line:
                    comment_pos = line.index('#')
                    print_pos = line.index('print(')
                    if comment_pos < print_pos:
                        continue

                issues.append({
                    'line': i,
                    'content': line.rstrip(),
                    'type': 'unguarded_print'
                })

    except FileNotFoundError:
        return [{'type': 'file_not_found', 'line': 0, 'content': f'File not found: {filepath}'}]

    return issues


def main():
    """Run verification checks"""
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║                     SILENT MODE VERIFICATION                             ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()

    files_to_check = [
        'cli_interactive.py',
        'agent/llm/responder.py',
        'agent/core/orchestrator.py',
    ]

    all_passed = True

    for filepath in files_to_check:
        print(f"Checking: {filepath}")
        issues = check_file_for_unwanted_prints(filepath)

        if issues:
            all_passed = False
            print(f"  ❌ Found {len(issues)} issue(s):")
            for issue in issues:
                if issue['type'] == 'file_not_found':
                    print(f"     {issue['content']}")
                else:
                    print(f"     Line {issue['line']}: {issue['content']}")
        else:
            print(f"  ✅ No issues found")
        print()

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if all_passed:
        print("✅ VERIFICATION PASSED")
        print()
        print("Silent mode should now show ONLY:")
        print("  - User input prompt (>>)")
        print("  - Bot responses")
        print()
        print("To test manually:")
        print("  ./run_conversation.sh -s")
        print()
        return 0
    else:
        print("❌ VERIFICATION FAILED")
        print()
        print("Some files still have unguarded print statements.")
        print("These will show up even in silent mode.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
