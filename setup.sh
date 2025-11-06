#!/bin/bash
# Setup script for Plex Media Purge Helper Tool (Linux/Mac)

echo "============================================"
echo "Plex Media Purge Helper - Setup"
echo "============================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

echo "[1/4] Python found"
python3 --version
echo

# Create virtual environment
echo "[2/4] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping creation"
else
    python3 -m venv venv
    echo "Virtual environment created successfully"
fi
echo

# Activate virtual environment and install dependencies
echo "[3/4] Installing dependencies..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo

# Copy config template if config.py doesn't exist
echo "[4/4] Setting up configuration..."
if [ -f "config.py" ]; then
    echo "config.py already exists, skipping"
else
    cp config.example.py config.py
    echo "config.py created from template"
    echo
    echo "IMPORTANT: Edit config.py and add your Plex and Tautulli credentials!"
fi
echo

echo "============================================"
echo "Setup complete!"
echo "============================================"
echo
echo "Next steps:"
echo "1. Edit config.py and add your API credentials"
echo "2. Run: ./run.sh"
echo
echo "Or manually:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run the tool: python main.py"
echo
