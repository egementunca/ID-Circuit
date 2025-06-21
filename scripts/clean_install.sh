#!/bin/bash
set -e

echo "🧹 Starting clean installation of Identity Circuit Factory..."

# Function to print colored output
print_status() {
    echo -e "\033[1;32m[INFO]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# Check Python version
if ! python3 --version | grep -q "Python 3\.[8-9]\|Python 3\.1[0-9]"; then
    print_error "Python 3.8+ required"
    exit 1
fi

print_status "Cleaning old installations..."

# Remove old environment and caches
rm -rf .venv
rm -rf __pycache__
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

print_status "Creating fresh virtual environment..."
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

print_status "Upgrading pip and setuptools..."
pip install --upgrade pip setuptools wheel

print_status "Installing project in development mode..."
pip install -e .

print_status "Installing development dependencies..."
pip install -e ".[dev]"

print_status "Verifying installation..."

# Test imports
python -c "import identity_factory; print('✅ identity_factory imported successfully')"
python -c "import sat_revsynth; print('✅ sat_revsynth imported successfully')"
python -c "from identity_factory import IdentityFactory; print('✅ IdentityFactory imported successfully')"

print_status "Running quick tests..."
python -m pytest tests/ -v --tb=short || print_error "Some tests failed (this might be expected)"

echo ""
echo "🎉 Clean installation complete!"
echo "📋 Next steps:"
echo "   1. Activate environment: source .venv/bin/activate"
echo "   2. Test CLI: python -m identity_factory --help"
echo "   3. Start API: python start_api.py"
echo "   4. Run tests: pytest"
