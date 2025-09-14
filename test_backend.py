#!/usr/bin/env python3
"""
Simple test to check if the backend can start.
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, 'backend')

try:
    print("Testing imports...")
    from backend.models import Base
    print("✅ Models imported")
    
    from backend.local_responder import LocalResponder
    print("✅ Local responder imported")
    
    from backend.routes import chat, places
    print("✅ Routes imported")
    
    from backend.main import app
    print("✅ Main app imported")
    
    print("🎉 All imports successful!")
    
    # Test if we can create the app
    print("Testing app creation...")
    print(f"App: {app}")
    print("✅ App created successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()


