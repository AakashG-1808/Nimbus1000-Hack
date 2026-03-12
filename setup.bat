@echo off
REM UrbanGuard AI System - Setup Script for Windows

echo === UrbanGuard AI System Setup ===
echo.

REM Backend setup
echo Setting up backend...
cd backend

REM Create virtual environment
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo [OK] Python dependencies installed

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo [OK] .env file created - Please edit it with your API keys
) else (
    echo [OK] .env file already exists
)

cd ..

REM Frontend setup
echo.
echo Setting up frontend...
cd frontend

REM Install Node dependencies
if not exist "node_modules" (
    echo Installing Node dependencies...
    call npm install
    echo [OK] Node dependencies installed
) else (
    echo [OK] Node dependencies already installed
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo [OK] .env file created
) else (
    echo [OK] .env file already exists
)

cd ..

echo.
echo === Setup Complete ===
echo.
echo Next steps:
echo 1. Edit backend\.env with your API keys:
echo    - OpenWeatherMap API key
echo    - AWS credentials for Bedrock
echo.
echo 2. Start the backend server:
echo    cd backend
echo    venv\Scripts\activate
echo    python main.py
echo.
echo 3. In a new terminal, start the frontend:
echo    cd frontend
echo    npm start
echo.
echo The backend will run on http://localhost:8000
echo The frontend will run on http://localhost:3000
echo.
pause
