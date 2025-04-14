# Backend Service

A Flask-based backend service for mass spectrometry data processing.

## Requirements

- Python 3.8
- Required Python packages (install via pip)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:
- On Windows:
```bash
venv\Scripts\activate
```
- On Unix or MacOS:
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

If the requirements.txt file is not available, install the following packages:
```bash
pip install flask pandas numpy spectral_entropy joblib tqdm
```

## Starting the Server

### Method 1: Direct Python Command

Run the application with:
```bash
python app.py
```

The server will start on `http://0.0.0.0:5000` with debug mode enabled.

### Method 2: One-Click Start on Windows

For Windows users, a batch script is provided for one-click startup:

1. Simply double-click the `run_flask_server.bat` file in the project root directory.
2. This script will:
   - Install required dependencies using the Tsinghua University PyPI mirror
   - Start the Flask server on port 5000
   - Keep the console window open to view server logs

## API Endpoints

The service provides the following REST API endpoints:

- `/api/v1/id` (POST): Process mass spectrometry data for identification
- `/api/v1/finder` (POST): Find peaks and analyze mass spectrometry data

For detailed API documentation, refer to the API documentation (not included in this README). 