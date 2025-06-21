#!/usr/bin/env bash

# Run the Streamlit application
# This script sets up and runs the Streamlit app
# Updated to use the Python launcher script for proper module imports

# Set default Python path
PYTHON_PATH="python3"

# Check if Python 3.12 is available
if command -v python3.12 &> /dev/null; then
    PYTHON_PATH="python3.12"
fi

# Display Python version
echo "Using Python: $($PYTHON_PATH --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_PATH -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if ! pip show streamlit &> /dev/null; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file with your credentials."
fi

# Start PostgreSQL if not running
if ! docker ps | grep -q finops-postgres; then
    echo "Starting PostgreSQL database..."
    docker compose up -d
fi

# Run the Streamlit app
echo "Starting Streamlit app..."
python3 launch_app.py
