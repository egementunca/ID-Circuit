@echo off
echo 🧹 Starting clean installation of Identity Circuit Factory...

REM Clean old installations
if exist .venv rmdir /s /q .venv
if exist __pycache__ rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
for /d /r . %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"

echo Creating fresh virtual environment...
python -m venv .venv

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip and setuptools...
pip install --upgrade pip setuptools wheel

echo Installing project in development mode...
pip install -e .

echo Installing development dependencies...
pip install -e ".[dev]"

echo Verifying installation...
python -c "import identity_factory; print('✅ identity_factory imported successfully')"
python -c "import sat_revsynth; print('✅ sat_revsynth imported successfully')"

echo 🎉 Clean installation complete!
echo 📋 Next steps:
echo    1. Activate environment: .venv\Scripts\activate.bat
echo    2. Test CLI: python -m identity_factory --help
echo    3. Start API: python start_api.py
pause