#!/bin/bash

# CalDAV Migration Web Interface Startup Script

echo "================================"
echo "CalDAV Migration Web Interface"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
pip install -q -r requirements-web.txt

# Run database migration if needed
echo "Checking database migration..."
python3 migrate_db.py

echo ""
echo "Starting web server..."
echo "================================"
echo "Access the interface at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo "================================"
echo ""

# Run the Flask app
python3 app.py
