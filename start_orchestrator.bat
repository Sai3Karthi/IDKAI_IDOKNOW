@echo off
echo Starting Module1 & Module3 Orchestrator...
echo.
echo Make sure you have:
echo 1. Installed Python dependencies: pip install -r Module1/requirements.txt
echo 2. Set up API keys in Module1/.env file
echo 3. Installed frontend dependencies: npm install (in frontend folder)
echo.
echo Starting orchestrator on http://localhost:8000
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"
python orchestrator.py