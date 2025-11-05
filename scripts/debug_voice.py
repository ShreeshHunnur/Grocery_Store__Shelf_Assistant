#!/usr/bin/env python3
"""
Debug voice endpoint to see exact error
"""
import requests
import sys

def test_voice_endpoint():
    """Test voice endpoint with detailed error reporting."""
    print("🔍 Testing Voice Endpoint...")
    
    base_url = "http://localhost:8000"
    
    # Test with fake audio data
    test_data = b"fake audio data for testing"
    files = {'audio_file': ('test.wav', test_data, 'audio/wav')}
    data = {'session_id': 'debug_test', 'return_audio': 'false'}
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/ask-voice",
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Response JSON: {response_json}")
        except:
            print(f"Response Text: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_voice_endpoint()