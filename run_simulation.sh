#!/bin/bash
# Risk Runners Dental Captive - Simulation Runner

echo "=========================================="
echo "Risk Runners Dental Captive"
echo "Simulation Runner"
echo "=========================================="
echo ""

if ! command -v python3.10 &> /dev/null; then
    echo "❌ Error: Python 3.10 is not installed"
    echo "  macOS: brew install python@3.10"
    echo "  Or download from: https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python found: $(python3.10 --version)"
echo ""

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.10 -m venv venv
    echo "✓ Virtual environment created"
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

echo "=========================================="
echo "Running Simulations"
echo "=========================================="

cd src
python main.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Simulation Complete!"
    echo "=========================================="
    echo ""
    echo "Results saved to:"
    echo "  - docs/assets/  (graphs)"
    echo "  - docs/data/    (JSON policy data)"
    echo "  - data/         (CSV files)"
    echo ""
    echo "To view: open docs/index.html"
else
    echo "❌ Simulation failed."
    exit 1
fi

deactivate
