#!/usr/bin/env python3
"""
End-to-end demo script for the Retail Shelf Assistant.
Provides a CLI loop for quick testing of the complete system.
"""
import requests
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_api_connection(base_url: str = "http://localhost:8000") -> bool:
    """Test if the API is running and accessible."""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"+ API is running - Status: {data.get('status')}")
            print(f"  Components: {json.dumps(data.get('components'), indent=2)}")
            return True
        else:
            print(f"- API health check failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("- Cannot connect to API. Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"- Error connecting to API: {e}")
        return False

def test_text_query(base_url: str, query: str) -> dict:
    """Test a text query through the API."""
    try:
        response = requests.post(
            f"{base_url}/api/v1/ask",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": "Request failed", "details": str(e)}

def test_voice_query(base_url: str, audio_file_path: str) -> dict:
    """Test a voice query through the API."""
    try:
        if not os.path.exists(audio_file_path):
            return {"error": "Audio file not found", "details": f"File: {audio_file_path}"}
        
        with open(audio_file_path, 'rb') as f:
            files = {'audio_file': f}
            response = requests.post(
                f"{base_url}/api/v1/ask-voice",
                files=files,
                timeout=10
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": "Request failed", "details": str(e)}

def format_response(response: dict) -> str:
    """Format API response for display."""
    if "error" in response:
        return f"X Error: {response['error']}\n   Details: {response.get('details', 'N/A')}"
    
    if response.get("query_type") == "location":
        matches = response.get("matches", [])
        product = response.get("normalized_product", "Unknown")
        disambiguation = response.get("disambiguation_needed", False)
        notes = response.get("notes", "")
        
        result = f"[LOCATION] Location Query Results:\n"
        result += f"   Product: {product}\n"
        result += f"   Matches: {len(matches)}\n"
        result += f"   Disambiguation needed: {disambiguation}\n"
        
        if matches:
            result += f"   Top matches:\n"
            for i, match in enumerate(matches[:3], 1):
                result += f"     {i}. {match.get('product_name', 'Unknown')} ({match.get('brand', 'Unknown')})\n"
                result += f"        Aisle: {match.get('aisle', 'Unknown')}, Bay: {match.get('bay', 'Unknown')}, Shelf: {match.get('shelf', 'Unknown')}\n"
                result += f"        Confidence: {match.get('confidence', 0):.2f}\n"
        
        if notes:
            result += f"   Notes: {notes}\n"
        
        return result
    
    elif response.get("query_type") == "information":
        product = response.get("normalized_product", "Unknown")
        answer = response.get("answer", "No answer provided")
        confidence = response.get("confidence", 0)
        caveats = response.get("caveats", "")
        
        result = f"[INFO] Information Query Results:\n"
        result += f"   Product: {product}\n"
        result += f"   Answer: {answer}\n"
        result += f"   Confidence: {confidence:.2f}\n"
        
        if caveats:
            result += f"   Caveats: {caveats}\n"
        
        return result
    
    else:
        return f"? Unknown response type: {json.dumps(response, indent=2)}"

def run_demo_loop(base_url: str = "http://localhost:8000"):
    """Run the interactive demo loop."""
    print("Retail Shelf Assistant - End-to-End Demo")
    print("=" * 50)
    print("Commands:")
    print("  text <query>     - Test text query")
    print("  voice <file>     - Test voice query with audio file")
    print("  health          - Check API health")
    print("  examples        - Show example queries")
    print("  quit/exit       - Exit demo")
    print("=" * 50)
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            elif command.lower() == 'health':
                if test_api_connection(base_url):
                    print("+ API is healthy")
                else:
                    print("- API is not accessible")
            
            elif command.lower() == 'examples':
                print("\nExample Queries:")
                print("  Text queries:")
                print("    where is the milk")
                print("    find apples")
                print("    which aisle has chicken")
                print("    what are the ingredients in bread")
                print("    is this product gluten free")
                print("    what is the price of cheese")
                print("    nutrition information for yogurt")
                print("\n  Voice queries:")
                print("    voice sample.wav")
                print("    voice test.mp3")
            
            elif command.startswith('text '):
                query = command[5:].strip()
                if not query:
                    print("X Please provide a query")
                    continue
                
                print(f"Processing text query: '{query}'")
                response = test_text_query(base_url, query)
                print(format_response(response))
            
            elif command.startswith('voice '):
                file_path = command[6:].strip()
                if not file_path:
                    print("X Please provide an audio file path")
                    continue
                
                print(f"Processing voice query: '{file_path}'")
                response = test_voice_query(base_url, file_path)
                print(format_response(response))
            
            else:
                print("X Unknown command. Type 'examples' for help or 'quit' to exit.")
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"X Error: {e}")

def run_automated_tests(base_url: str = "http://localhost:8000"):
    """Run automated tests on the API."""
    print("Running Automated Tests")
    print("=" * 30)
    
    # Test cases
    test_cases = [
        ("where is the milk", "location"),
        ("find apples", "location"),
        ("which aisle has chicken", "location"),
        ("what are the ingredients in bread", "information"),
        ("is this product gluten free", "information"),
        ("what is the price of cheese", "information"),
        ("nutrition information for yogurt", "information"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for query, expected_type in test_cases:
        print(f"\nTesting: '{query}'")
        response = test_text_query(base_url, query)
        
        if "error" in response:
            print(f"X Failed: {response['error']}")
        else:
            actual_type = response.get("query_type", "unknown")
            if actual_type == expected_type:
                print(f"+ Passed: {actual_type}")
                passed += 1
            else:
                print(f"X Failed: Expected {expected_type}, got {actual_type}")
    
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("All tests passed!")
    else:
        print("Some tests failed")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Retail Shelf Assistant Demo')
    parser.add_argument('--url', default='http://localhost:8000', help='API base URL')
    parser.add_argument('--test', action='store_true', help='Run automated tests instead of interactive demo')
    
    args = parser.parse_args()
    
    # Check if API is accessible
    if not test_api_connection(args.url):
        print("\nTo start the API server, run:")
        print("   python scripts/start_server.py")
        print("   or")
        print("   uvicorn src.api.main:app --host 127.0.0.1 --port 8000")
        sys.exit(1)
    
    if args.test:
        run_automated_tests(args.url)
    else:
        run_demo_loop(args.url)

if __name__ == "__main__":
    main()
