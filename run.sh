#!/bin/bash
# ============================================================
# Intelligent Bug Diagnosis Platform — One-Command Startup Script
# ============================================================

set -e

echo "Starting Intelligent Bug Diagnosis Platform..."

# Check Python 3 availability
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 could not be found. Please install Python 3.8+."
    exit 1
fi

# Set up virtual environment if not present
if [ ! -d "venv" ]; then
    echo "Creating virtual environment 'venv'..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies from requirements.txt..."
pip install -q -r requirements.txt

# Ensure database directory exists
mkdir -p database

# Seed database
echo "Seeding database..."
python3 -m backend.app.seed

# Start FastAPI application
echo "Launching FastAPI server on http://localhost:8000 ..."
python3 -m backend.app.main
