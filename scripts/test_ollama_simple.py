#!/usr/bin/env python3
"""
Simple test to check Ollama connectivity and basic LLM functionality.
"""
import sys
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_ollama_connection():
    """Test basic Ollama connection."""
    print("Testing Ollama Connection...")
    
    try:
        # Test if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"+ Ollama is running! Found {len(models)} models:")
            
            for model in models:
                print(f"  - {model.get('name', 'Unknown')}")
            
            # Check if phi3 is available
            phi3_available = any("phi3" in model.get("name", "").lower() for model in models)
            
            if phi3_available:
                print("+ Phi3 model is available!")
                return True
            else:
                print("- Phi3 model not found. Please run: ollama pull phi3")
                return False
        else:
            print(f"- Ollama API error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("- Cannot connect to Ollama. Please make sure Ollama is running:")
        print("  1. Install Ollama from https://ollama.ai/download")
        print("  2. Run: ollama pull phi3")
        print("  3. Run: ollama serve")
        return False
    except Exception as e:
        print(f"- Error: {e}")
        return False

def test_simple_generation():
    """Test simple text generation."""
    print("\nTesting Simple Text Generation...")
    
    try:
        # Test simple generation
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3",
                "prompt": "What are the ingredients in milk?",
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 100
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("response", "")
            print(f"+ Generated response: {answer[:100]}...")
            return True
        else:
            print(f"- Generation failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"- Generation error: {e}")
        return False

def main():
    """Run simple tests."""
    print("Simple Ollama Integration Test")
    print("=" * 40)
    
    # Test connection
    connection_ok = test_ollama_connection()
    
    if connection_ok:
        # Test generation
        generation_ok = test_simple_generation()
        
        if generation_ok:
            print("\n+ All tests passed! Ollama integration is working.")
            return True
        else:
            print("\n- Generation test failed.")
            return False
    else:
        print("\n- Connection test failed. Please set up Ollama first.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
