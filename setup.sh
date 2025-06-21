#!/bin/bash

# Identity Circuit Factory - Quick Setup Script
# Run this after cloning the repository: ./setup.sh

set -e  # Exit on any error

echo "🚀 Identity Circuit Factory - Quick Setup"
echo "=========================================="

# Check Python 3.12
echo "📋 Checking Python 3.12..."
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 not found. Please install Python 3.12 first."
    exit 1
fi

python3.12 --version
echo "✅ Python 3.12 found"

# Create virtual environment
echo ""
echo "🐍 Creating clean virtual environment..."
rm -rf .venv  # Remove any existing environment
python3.12 -m venv .venv
echo "✅ Virtual environment created"

# Activate environment
echo ""
echo "🔧 Activating environment and upgrading tools..."
source .venv/bin/activate

# Upgrade core tools
pip install --upgrade pip setuptools wheel

# Install project
echo ""
echo "📦 Installing Identity Circuit Factory..."
pip install -e ".[dev]"

# Verify installation
echo ""
echo "🧪 Verifying installation..."
python -c "
import identity_factory
from identity_factory.api.server import run_server
from sat_revsynth.circuit.circuit import Circuit
print('✅ All imports successful!')
"

# Test SAT synthesis
python -c "
from sat_revsynth.circuit.circuit import Circuit
c = Circuit(3)
c.x(0).cx(0, 1).mcx([0, 1], 2)
print(f'✅ SAT synthesis works: {len(c)} gates')
"

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "Next steps:"
echo "  1. Activate environment: source .venv/bin/activate"
echo "  2. Start API server: python start_api.py"
echo "  3. Test API: curl http://localhost:8000/health"
echo "  4. View docs: http://localhost:8000/docs"
echo ""
echo "For detailed instructions, see INSTALL.txt" 