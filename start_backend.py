#!/usr/bin/env python3
"""
Startup script for Doctor Sahab backend.
This script handles environment setup and starts the FastAPI server.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version}")

def check_requirements():
    """Check if requirements.txt exists."""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found.")
        sys.exit(1)
    print("✅ requirements.txt found")

def install_requirements():
    """Install Python requirements."""
    print("📦 Installing requirements...")
    
    # Try minimal requirements first (no pandas/numpy)
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-minimal.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Minimal requirements installed successfully")
        return
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to install minimal requirements: {e}")
        print("🔄 Trying main requirements...")
    
    # Try main requirements
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Requirements installed successfully")
        return
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to install main requirements: {e}")
        print("🔄 Trying Windows-compatible requirements...")
    
    # Try Windows-compatible requirements
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-windows.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Windows-compatible requirements installed successfully")
        return
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install any requirements: {e}")
        print(f"Error output: {e.stderr}")
        print("\n🔧 Troubleshooting suggestions:")
        print("1. Update pip: python -m pip install --upgrade pip")
        print("2. Install Visual Studio Build Tools")
        print("3. Install MinGW-w64 with GCC 8.4+")
        print("4. Use conda instead: conda install pandas numpy")
        sys.exit(1)

def check_env_file():
    """Check if .env file exists, create from example if not."""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 Creating .env file from example...")
            with open(env_example, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ .env file created from example")
            print("⚠️  Please update the .env file with your actual configuration")
        else:
            print("❌ No .env or env.example file found")
            sys.exit(1)
    else:
        print("✅ .env file found")

def initialize_database():
    """Initialize the database."""
    print("🗄️  Initializing database...")
    try:
        # Change to backend directory
        backend_dir = Path("backend")
        if not backend_dir.exists():
            print("❌ Backend directory not found")
            sys.exit(1)
        
        # Try minimal database initialization first
        try:
            result = subprocess.run([sys.executable, "db_init_minimal.py"], 
                                  cwd=backend_dir, check=True, 
                                  capture_output=True, text=True)
            print("✅ Database initialized successfully (minimal version)")
        except subprocess.CalledProcessError:
            # Fallback to regular initialization
            result = subprocess.run([sys.executable, "db_init.py"], 
                                  cwd=backend_dir, check=True, 
                                  capture_output=True, text=True)
            print("✅ Database initialized successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to initialize database: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting Doctor Sahab backend server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API documentation: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Change to backend directory and start server
        backend_dir = Path("backend")
        subprocess.run([sys.executable, "main.py"], cwd=backend_dir)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main startup function."""
    print("🏥 Doctor Sahab Backend Startup")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Check requirements file
    check_requirements()
    
    # Install requirements
    install_requirements()
    
    # Check/create .env file
    check_env_file()
    
    # Initialize database
    initialize_database()
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
