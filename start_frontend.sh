#!/bin/bash

echo "🏥 Doctor Sahab Frontend Startup"
echo "========================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed or not in PATH"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found"
    exit 1
fi

echo "✅ Frontend directory found"

# Navigate to frontend directory
cd frontend

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found in frontend directory"
    exit 1
fi

echo "✅ package.json found"

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "✅ Dependencies already installed"
fi

# Check if .env file exists in frontend
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    echo "REACT_APP_API_URL=http://localhost:8000" > .env
    echo "✅ .env file created"
fi

echo "🚀 Starting Doctor Sahab frontend..."
echo "📍 Frontend will be available at: http://localhost:3000"
echo "🛑 Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Start the development server
npm start


