#!/bin/bash
# Setup script for creating Python 3.12 virtual environment on macOS/Linux

echo "========================================"
echo "SmartSpendGrocery - Virtual Environment Setup"
echo "========================================"
echo ""

# Check if Python 3.12 is available
if ! command -v python3.12 &> /dev/null; then
    echo "ERROR: Python 3.12 not found!"
    echo ""
    echo "Please install Python 3.12:"
    echo "  macOS: brew install python@3.12"
    echo "  Linux: sudo apt-get install python3.12"
    echo "  Or download from https://www.python.org/downloads/"
    echo ""
    exit 1
fi

echo "Python 3.12 found!"
echo ""

# Remove old virtual environment if it exists
if [ -d "adkapp" ]; then
    echo "Removing old virtual environment..."
    rm -rf adkapp
    echo "Old virtual environment removed."
    echo ""
fi

# Create new virtual environment
echo "Creating new virtual environment with Python 3.12..."
python3.12 -m venv adkapp
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment!"
    exit 1
fi
echo "Virtual environment created successfully!"
echo ""

# Activate and upgrade pip
echo "Activating virtual environment and upgrading pip..."
source adkapp/bin/activate
python -m pip install --upgrade pip
echo ""

# Install requirements
echo "Installing project dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "WARNING: Some packages may have failed to install."
    echo "Please check the output above."
    echo ""
else
    echo ""
    echo "========================================"
    echo "Setup completed successfully!"
    echo "========================================"
    echo ""
    echo "To activate the virtual environment in the future, run:"
    echo "  source adkapp/bin/activate"
    echo ""
    echo "To run the application:"
    echo "  streamlit run main.py"
    echo ""
fi




