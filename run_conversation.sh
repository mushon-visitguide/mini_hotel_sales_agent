#!/bin/bash
# Activate virtual environment and run interactive agent with interruption support
#
# Usage:
#   ./run_conversation.sh           # Normal mode with debug info
#   ./run_conversation.sh -s        # Silent mode - only LLM responses
#   ./run_conversation.sh --silent  # Silent mode - only LLM responses

source venv/bin/activate
python3 cli_interactive.py "$@"
