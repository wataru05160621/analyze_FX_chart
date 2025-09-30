#!/bin/bash

# FX Filter Analysis Runner
# This script activates the virtual environment and runs the filter analysis

echo "🔍 Starting FX Filter Analysis..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Activate virtual environment
source "${SCRIPT_DIR}/venv/bin/activate"

# Run the analysis
python "${SCRIPT_DIR}/analyze_notion_filters.py"

# Deactivate virtual environment
deactivate

echo "✅ Analysis complete!"