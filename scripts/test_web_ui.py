#!/usr/bin/env python3
"""
Test script for the Voice Web UI.
"""
import sys
import time
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_server_health():
    """Test if the server is running and healthy."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"+ Server is running - Status: {data.get('status')}")
            return True
        else:
            print(f"- Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("- Server is not running")
        return False
    except Exception as e:
        print(f"- Error checking server: {e}")
        return False

def test_web_ui_files():
    """Test if web UI files exist."""
    web_dir = Path("web")
    
    files_to_check = ["index.html", "styles.css", "app.js"]
    all_exist = True
    
    for file_name in files_to_check:
        file_path = web_dir / file_name
        if file_path.exists():
            print(f"+ {file_name} exists")
        else:
            print(f"- {file_name} missing")
            all_exist = False
    
    return all_exist

def test_static_file_serving():
    """Test if static files are being served."""
    try:
        # Test if we can access the web UI
        response = requests.get("http://localhost:8000/ui", timeout=5)
        if response.status_code == 200:
            content = response.text
            if "Retail Shelf Assistant" in content:
                print("+ Web UI is accessible")
                return True
            else:
                print("- Web UI content seems incorrect")
                return False
        else:
            print(f"- Web UI not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"- Error accessing web UI: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints."""
    try:
        # Test text endpoint
        response = requests.post(
            "http://localhost:8000/api/v1/ask",
            json={"query": "where is the milk", "session_id": "test"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("+ Text API endpoint working")
        else:
            print(f"- Text API endpoint failed: {response.status_code}")
            return False
        
        # Test voice endpoint (with mock data)
        files = {"audio_file": ("test.webm", b"mock audio data", "audio/webm")}
        data = {"session_id": "test", "return_audio": "false"}
        
        response = requests.post(
            "http://localhost:8000/api/v1/ask-voice",
            files=files,
            data=data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("+ Voice API endpoint working")
            return True
        else:
            print(f"- Voice API endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"- Error testing API endpoints: {e}")
        return False

def main():
    """Run all tests."""
    print("Voice Web UI Test")
    print("=" * 30)
    
    tests = [
        ("Web UI Files", test_web_ui_files),
        ("Server Health", test_server_health),
        ("Static File Serving", test_static_file_serving),
        ("API Endpoints", test_api_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"+ {test_name}: PASSED")
            else:
                print(f"- {test_name}: FAILED")
                
        except Exception as e:
            print(f"X {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 30)
    print("TEST SUMMARY")
    print("=" * 30)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("+ All tests passed! Voice Web UI is ready.")
        print("\nAccess the web UI at: http://localhost:8000/ui")
        print("Or directly at: http://localhost:8000/static/index.html")
        return True
    else:
        print("- Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
