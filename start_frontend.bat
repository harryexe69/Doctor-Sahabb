@echo off
echo 🏥 Doctor Sahab Frontend Startup
echo ========================================

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js found

REM Check if frontend directory exists
if not exist "frontend" (
    echo ❌ Frontend directory not found
    pause
    exit /b 1
)

echo ✅ Frontend directory found

REM Navigate to frontend directory
cd frontend

REM Check if package.json exists
if not exist "package.json" (
    echo ❌ package.json not found in frontend directory
    pause
    exit /b 1
)

echo ✅ package.json found

REM Check if node_modules exists, if not install dependencies
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
) else (
    echo ✅ Dependencies already installed
)

REM Check if .env file exists in frontend
if not exist ".env" (
    echo 📝 Creating .env file...
    echo REACT_APP_API_URL=http://localhost:8000 > .env
    echo ✅ .env file created
)

echo 🚀 Starting Doctor Sahab frontend...
echo 📍 Frontend will be available at: http://localhost:3000
echo 🛑 Press Ctrl+C to stop the server
echo ----------------------------------------

REM Start the development server
npm start

pause


