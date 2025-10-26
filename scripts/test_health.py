#!/usr/bin/env python3
"""
Test script to verify the health endpoint works correctly.
"""
import requests
import json
import sys

def test_health_endpoint():
    """Test the /health endpoint."""
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("Health check passed!")
            print(f"Status: {data.get('status')}")
            print(f"Version: {data.get('version')}")
            print(f"Components: {json.dumps(data.get('components'), indent=2)}")
            return True
        else:
            print(f"Health check failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Could not connect to server. Make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"Error testing health endpoint: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint."""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("Root endpoint working!")
            print(f"Message: {data.get('message')}")
            return True
        else:
            print(f"Root endpoint failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error testing root endpoint: {e}")
        return False

if __name__ == "__main__":
    print("Testing Retail Shelf Assistant API...")
    print("=" * 50)
    
    # Test root endpoint
    root_ok = test_root_endpoint()
    print()
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    
    print("=" * 50)
    if root_ok and health_ok:
        print("All tests passed! API is working correctly.")
        sys.exit(0)
    else:
        print("Some tests failed. Check the output above.")
        sys.exit(1)