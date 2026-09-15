#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo "Initializing database..."
python3 -m backend.app.seed

echo "🚀 Starting Streamlit Frontend Dashboard for Infosys Bug Intelligence Platform..."
streamlit run app.py
