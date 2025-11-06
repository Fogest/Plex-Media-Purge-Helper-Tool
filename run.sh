#!/bin/bash
# Run script for Plex Media Purge Helper Tool (Linux/Mac)

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment and run the tool
source venv/bin/activate
python main.py "$@"
