#!/bin/bash

# This script is for setting up the virtual environment and installing dependencies on macOS/Linux

echo "🔧 Creating virtual environment (.venv)..."
python3 -m venv .venv # This creates a new virtual environment in the .venv folder
source .venv/bin/activate # Activates the environment

# Install the required dependencies from requirements.txt
echo "📦 Installing dependencies from requirements.txt..."
pip install --upgrade pip # Upgrade pip to the latest version
pip install -r requirements.txt # Install all the dependencies listed in requirements.txt

echo "✅ Setup complete!"
echo "👉 To activate the environment later, run:"
echo "source .venv/bin/activate"
