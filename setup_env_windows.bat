@echo off

:: This script is for setting up the virtual environment and installing dependencies on Windows

echo 🔧 Creating virtual environment (.venv)...
python -m venv .venv # This creates a virtual environment
call .venv\Scripts\activate.bat # Activates the environment

:: Install the required dependencies from requirements.txt
echo 📦 Installing dependencies from requirements.txt...
python -m pip install --upgrade pip # Upgrade pip to the latest version
pip install -r requirements.txt # Install all the dependencies listed in requirements.txt

echo ✅ Setup complete!
echo 👉 To activate the environment later, run:
echo .venv\Scripts\activate
pause
