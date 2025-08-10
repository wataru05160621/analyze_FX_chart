#!/bin/bash
# Local run script for FX Analysis

set -e

echo "==================================="
echo "FX Analysis - Local Run"
echo "==================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and fill in your credentials"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Environment loaded"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run smoke test first
echo ""
echo "Running smoke tests..."
python scripts/smoke_test.py

if [ $? -ne 0 ]; then
    echo "❌ Smoke tests failed"
    exit 1
fi

# Run main application
echo ""
echo "Running FX Analysis..."
python -m src.runner.main

echo ""
echo "==================================="
echo "Analysis complete!"
echo "===================================" 