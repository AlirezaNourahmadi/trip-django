#!/usr/bin/env python
"""
Trip-Django Setup Verification Script
=====================================
This script verifies that all components are working correctly.
"""

import os
import sys
import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

def test_database():
    """Test database connection"""
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Database connection: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ Database connection: FAILED - {e}")
        return False

def test_models():
    """Test Django models"""
    try:
        from home.models import Destination, ChatMessage, User
        dest_count = Destination.objects.count()
        print(f"✅ Models: SUCCESS - {dest_count} destinations loaded")
        return True
    except Exception as e:
        print(f"❌ Models: FAILED - {e}")
        return False

def test_openai():
    """Test OpenAI integration"""
    try:
        from home.services import ai_service
        response = ai_service.generate_response("Hello, test message")
        print("✅ OpenAI GPT-4: SUCCESS")
        print(f"   Sample response: {response[:60]}...")
        return True
    except Exception as e:
        print(f"❌ OpenAI GPT-4: FAILED - {e}")
        return False

def test_environment():
    """Test environment variables"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key.startswith('sk-'):
            print("✅ Environment variables: SUCCESS")
            return True
        else:
            print("❌ Environment variables: FAILED - API key not found")
            return False
    except Exception as e:
        print(f"❌ Environment variables: FAILED - {e}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 Trip-Django Setup Verification")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_database,
        test_models,
        test_openai
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ {test.__name__}: FAILED - {e}")
            results.append(False)
        print()
    
    # Summary
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    if all(results):
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your Trip-Django application is ready to use!")
        print("🚀 Run: python manage.py runserver")
        print("🌐 Visit: http://127.0.0.1:8000/chatbot/")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("💡 Make sure all dependencies are installed and configured.")

if __name__ == "__main__":
    main()
