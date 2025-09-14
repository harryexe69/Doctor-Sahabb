#!/usr/bin/env python3
"""
Test script to verify Doctor Sahab setup is working correctly.
"""

import sys
import subprocess
import time
import requests
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported."""
    print("🧪 Testing package imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import pandas
        print("✅ Pandas imported successfully")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        import numpy
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    return True

def test_backend_startup():
    """Test if backend can start successfully."""
    print("\n🚀 Testing backend startup...")
    
    try:
        # Start backend in background
        process = subprocess.Popen([
            sys.executable, "main.py"
        ], cwd="backend", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for startup
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Backend started successfully")
            
            # Test health endpoint
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Health endpoint responding")
                    print(f"   Response: {response.json()}")
                else:
                    print(f"❌ Health endpoint returned status {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Health endpoint test failed: {e}")
            
            # Kill the process
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Backend failed to start")
            print(f"   stdout: {stdout.decode()}")
            print(f"   stderr: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Backend startup test failed: {e}")
        return False

def test_database():
    """Test database initialization."""
    print("\n🗄️  Testing database initialization...")
    
    try:
        # Run database initialization
        result = subprocess.run([
            sys.executable, "db_init.py"
        ], cwd="backend", capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Database initialized successfully")
            return True
        else:
            print(f"❌ Database initialization failed")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_frontend_dependencies():
    """Test if frontend dependencies are installed."""
    print("\n🎨 Testing frontend dependencies...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("❌ Node modules not found. Run 'npm install' in frontend directory")
        return False
    
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json not found")
        return False
    
    print("✅ Frontend dependencies found")
    return True

def main():
    """Run all tests."""
    print("🏥 Doctor Sahab Setup Test")
    print("=" * 40)
    
    tests = [
        ("Package Imports", test_imports),
        ("Database Initialization", test_database),
        ("Frontend Dependencies", test_frontend_dependencies),
        ("Backend Startup", test_backend_startup),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Results:")
    print("-" * 40)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Doctor Sahab is ready to run!")
        print("\nNext steps:")
        print("1. Start backend: python start_backend.py")
        print("2. Start frontend: start_frontend.bat")
        print("3. Open http://localhost:3000")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed")
        print("2. Check the WINDOWS_SETUP.md guide")
        print("3. Try the alternative installation methods")

if __name__ == "__main__":
    main()


