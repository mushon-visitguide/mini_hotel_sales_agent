#!/bin/bash
# Test runner script for MiniHotel API integration

echo "MiniHotel API Test Suite"
echo "========================"
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
venv/bin/python -m pytest src/tests/test_minihotel.py -v "$@"
