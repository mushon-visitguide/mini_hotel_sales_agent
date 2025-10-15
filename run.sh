#!/bin/bash

# Hotel Sales AI Agent - Run Script
# This script sets up the environment and runs the interactive agent

set -e  # Exit on error

echo "🏨 Hotel Sales AI Agent"
echo "======================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: python3 -m venv venv"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Please create .env with required credentials"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Load environment variables
echo "🔑 Loading environment variables..."
source .env

# Set PYTHONPATH
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set in .env!"
    echo "   Please add: export OPENAI_API_KEY=sk-..."
    exit 1
fi

echo "✅ Environment ready!"
echo ""

# Run the interactive agent
python main.py
