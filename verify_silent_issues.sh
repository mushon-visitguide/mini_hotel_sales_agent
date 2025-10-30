#!/bin/bash
# Quick verification script to check for unconditional print statements

echo "=========================================="
echo "SILENT MODE ISSUE VERIFICATION"
echo "=========================================="
echo ""
echo "Checking for unconditional print statements..."
echo ""

# CRITICAL: agent/llm/responder.py
echo "🔴 CRITICAL: agent/llm/responder.py"
echo "Line 63-70: Unconditional print statements"
grep -n "print(" agent/llm/responder.py | grep -v "if debug" | head -10
echo ""

# Check if debug parameter exists in generate_response
echo "Checking if 'debug' parameter exists in generate_response():"
grep -A 5 "def generate_response" agent/llm/responder.py | grep "debug"
if [ $? -eq 0 ]; then
    echo "✅ debug parameter found"
else
    echo "❌ debug parameter MISSING"
fi
echo ""

# MEDIUM: cli_interactive.py goodbye messages
echo "🟡 MEDIUM: cli_interactive.py"
echo "Lines with 'Goodbye' that might ignore silent mode:"
grep -n "Goodbye" cli_interactive.py
echo ""

echo "Lines with error prints that might ignore silent mode:"
grep -n "Colors.RED.*Error" cli_interactive.py
echo ""

# Check orchestrator.py passes debug to responder
echo "Checking if orchestrator passes debug to responder:"
grep -A 10 "responder.generate_response" agent/core/orchestrator.py | grep "debug="
if [ $? -eq 0 ]; then
    echo "✅ debug flag passed to responder"
else
    echo "❌ debug flag NOT passed to responder"
fi
echo ""

echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""
echo "Issues to fix:"
echo "1. 🔴 agent/llm/responder.py: Add debug parameter and wrap prints"
echo "2. 🔴 agent/core/orchestrator.py: Pass debug=debug to responder"
echo "3. 🟡 cli_interactive.py: Check silent_mode for error/goodbye messages"
echo ""
echo "See SILENT_MODE_ISSUES.md for detailed fix instructions"
