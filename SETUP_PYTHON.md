# Python Version Setup

This project requires **Python 3.12** (or Python 3.11 as fallback).

## Current Status

The virtual environment (`adkapp`) is currently using Python 3.9.13, which is past its end of life and may cause compatibility issues with Google API libraries.

## Upgrading to Python 3.12

### Step 1: Install Python 3.12

If you don't have Python 3.12 installed:

**Windows:**
- Download from [python.org](https://www.python.org/downloads/)
- Or use `winget install Python.Python.3.12`

**macOS:**
- `brew install python@3.12`
- Or download from python.org

**Linux:**
- `sudo apt-get install python3.12` (Ubuntu/Debian)
- Or use your distribution's package manager

### Step 2: Verify Python 3.12 Installation

```bash
python3.12 --version
# Should output: Python 3.12.x
```

### Step 3: Recreate Virtual Environment

**Option A: Delete and recreate (recommended)**

```bash
# Delete the old virtual environment
rm -rf adkapp  # On Windows: rmdir /s adkapp

# Create new virtual environment with Python 3.12
python3.12 -m venv adkapp

# Activate the virtual environment
# On Windows:
adkapp\Scripts\activate
# On macOS/Linux:
source adkapp/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

**Option B: Use existing venv with new Python**

```bash
# Deactivate current environment if active
deactivate

# Remove old venv
rm -rf adkapp  # On Windows: rmdir /s adkapp

# Create new venv pointing to Python 3.12
python3.12 -m venv adkapp

# Activate and install
adkapp\Scripts\activate  # Windows
# OR
source adkapp/bin/activate  # macOS/Linux

pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
# Check Python version in venv
python --version
# Should show: Python 3.12.x

# Verify packages are installed
pip list
```

### Step 5: Test the Application

```bash
# Run Streamlit app
streamlit run main.py
```

## Why Python 3.12?

- **Better Performance**: Python 3.12 includes performance optimizations
- **Modern Features**: Better type hints, improved error messages
- **Library Compatibility**: Google Generative AI and ADK work best with Python 3.11+
- **Future-Proof**: Python 3.9 is end-of-life, 3.12 is actively maintained

## Fallback: Python 3.11

If you encounter issues with Python 3.12, Python 3.11 is also supported:

```bash
python3.11 -m venv adkapp
```

## Troubleshooting

### "python3.12: command not found"
- Make sure Python 3.12 is installed and in your PATH
- On Windows, you may need to use `py -3.12` instead of `python3.12`

### Package installation errors
- Make sure you're using the latest pip: `pip install --upgrade pip`
- Some packages may need to be updated for Python 3.12 compatibility

### Google API errors
- Python 3.12 should resolve the `importlib.metadata` warnings
- If issues persist, check your `GOOGLE_API_KEY` is set correctly




