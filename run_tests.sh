#!/bin/bash
# Test runner script for Hotel Sales AI Agent

echo "Hotel Sales AI Agent - Test Suite"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
venv/bin/pip install -r requirements.txt -q
echo ""

# Run tests
echo "Running tests..."
echo ""

# Default: run all tests
if [ -z "$1" ]; then
    venv/bin/python -m pytest tests/ -v
else
    # Run specific test pattern
    venv/bin/python -m pytest tests/ -v -k "$@"
fi
