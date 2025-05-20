Air Quality Analysis in Lombardy

Project Overview

This project analyzes air quality data from Dati Lombardia to assess pollution levels and trends within the Lombardy region in Italy. Using interactive Jupyter Notebooks and custom Python modules, the analysis visualizes pollutant distributions, evaluates exposure risks, and highlights long-term trends, providing insights to support decision-makers such as environmental agencies and public health organizations.

Key Functionalities:

Visualize air quality measurements (e.g., PM2.5, NO₂) over time and geography.

Assess population exposure risks based on pollutant concentration.

Identify and compare pollution trends across different monitoring stations.

Export summary reports and charts for stakeholder presentations.

Getting Started

Follow these instructions to set up and run the project on macOS, Linux, or Windows.

Prerequisites

Git

Python 3.8 or higher

pip (Python package installer)

Clone the Repository

git clone https://github.com/your-username/lombardy-air-quality.git
cd lombardy-air-quality

Initial Setup (First Time Only)

macOS / Linux

# Make sure the setup script is executable
chmod +x setup_env_mac_linux.sh
# Run environment setup
./setup_env_mac_linux.sh

Windows

# Run the Windows setup batch file
setup_env_windows.bat

These scripts will:

Create a virtual environment in .venv/.

Activate the virtual environment.

Install dependencies from requirements.txt.

Launching the Project

Once the environment is ready:

# Activate environment (see Virtual Environment Management below)
source .venv/bin/activate   # macOS/Linux
.\.venv\Scripts\activate  # Windows

# Start Jupyter Notebook
jupyter notebook

Open notebooks/air_quality_analysis.ipynb to begin.

Subsequent Runs

After the initial setup, to run the project again:

Navigate to the project directory:

cd lombardy-air-quality

Activate the virtual environment:

source .venv/bin/activate   # macOS/Linux
.\.venv\Scripts\activate  # Windows

(Optional) Install new dependencies if added:

pip install <package-name>
pip freeze > requirements.txt

Launch Jupyter Notebook:

jupyter notebook

Virtual Environment Management

Activating / Deactivating Environment

macOS / Linux:

source .venv/bin/activate

Windows:

.\.venv\Scripts\activate

Deactivate (all OS):

deactivate

Installing Additional Packages

Activate the environment.

Install the package:

pip install <package-name>

Update requirements.txt:

pip freeze > requirements.txt

Commit changes:

git add requirements.txt
git commit -m "Update dependencies"

Project Structure

├── notebooks/               # Jupyter notebooks for analysis and visualization
│   └── air_quality_analysis.ipynb
├── src/                     # Python modules for data processing
│   ├── data_loader.py
│   ├── visualization.py
│   └── utils.py
├── data/                    # PLACEHOLDER for local datasets (excluded from Git)
├── .venv/                   # Virtual environment (excluded from Git)
├── requirements.txt         # Python dependencies
├── setup_env_mac_linux.sh   # Setup script for macOS/Linux
├── setup_env_windows.bat    # Setup script for Windows
└── README.md                # Project documentation

Note: Ensure data/ and .venv/ are listed in .gitignore.

Requirements

Python >= 3.8

pip

All project-specific packages listed in requirements.txt

Updating the Environment

To add new dependencies:

Activate the virtual environment.

Install the new package:

pip install <package-name>

Update dependencies list:

pip freeze > requirements.txt

Commit the update:

git add requirements.txt
git commit -m "Add <package-name> to dependencies"

Troubleshooting

Missing Dependencies:

Error: ModuleNotFoundError or ImportError.

Solution: Ensure the virtual environment is activated, then run pip install -r requirements.txt.

Environment Activation Issues:

macOS/Linux: Verify the script has execute permissions (chmod +x setup_env_mac_linux.sh).

Windows: Run setup_env_windows.bat from Command Prompt (not PowerShell) if activation fails.

Jupyter Notebook Won't Start:

Check that the environment is activated.

Verify Jupyter is installed (pip show notebook).

Reinstall with pip install notebook.

Git Errors When Committing:

Ensure files requirements.txt and README.md are staged: git add <file>.

Check for unmerged changes or conflicts: git status.

License

This project is licensed under the MIT License. See the LICENSE file for details.

Happy analyzing!

