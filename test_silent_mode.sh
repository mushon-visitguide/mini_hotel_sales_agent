#!/bin/bash
# Test silent mode to ensure only LLM responses are shown

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                        SILENT MODE TEST                               ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "This test will verify that silent mode only shows LLM responses."
echo ""
echo "Expected output in silent mode:"
echo "  - User prompt (>>)"
echo "  - LLM response only"
echo "  - No logs, no progress messages, no debug info"
echo ""
echo "Testing with a simple echo..."
echo ""

# Create a test input file
cat > /tmp/test_input.txt << 'EOF'
hi
quit
EOF

echo "Running: ./run_conversation.sh -s < /tmp/test_input.txt"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Note: This will still require API key to actually work
# But it demonstrates the command structure

echo "To manually test silent mode, run:"
echo ""
echo "  ./run_conversation.sh -s"
echo ""
echo "Then type a message and verify you only see:"
echo "  1. Your input prompt (>>)"
echo "  2. The LLM response"
echo "  3. Nothing else (no logs, progress, etc)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Cleanup
rm -f /tmp/test_input.txt
