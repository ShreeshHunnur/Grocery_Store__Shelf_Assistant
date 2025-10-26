#!/usr/bin/env python3
"""
Test script to verify API contracts compile correctly.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported."""
    try:
        from src.api.main import app
        print("+ FastAPI app imported successfully")
        
        from src.api.models import (
            ProductLocationResponse, 
            ProductInfoResponse, 
            TextQueryRequest,
            HealthResponse,
            ErrorResponse
        )
        print("+ Pydantic models imported successfully")
        
        from config.settings import get_config
        print("+ Configuration imported successfully")
        
        return True
    except Exception as e:
        print(f"- Import failed: {e}")
        return False

def test_pydantic_models():
    """Test that Pydantic models work correctly."""
    try:
        from src.api.models import ProductLocationResponse, ProductInfoResponse
        
        # Test ProductLocationResponse
        location_response = ProductLocationResponse(
            normalized_product="test product",
            matches=[],
            disambiguation_needed=False
        )
        print("+ ProductLocationResponse model works")
        
        # Test ProductInfoResponse
        info_response = ProductInfoResponse(
            normalized_product="test product",
            answer="test answer",
            confidence=0.8
        )
        print("+ ProductInfoResponse model works")
        
        return True
    except Exception as e:
        print(f"- Pydantic model test failed: {e}")
        return False

def test_config():
    """Test that configuration loads correctly."""
    try:
        from config.settings import get_config
        
        config = get_config()
        required_keys = ['audio', 'database', 'llm', 'classification', 'api', 'logging', 'performance']
        
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing config key: {key}")
        
        print("+ Configuration structure is correct")
        return True
    except Exception as e:
        print(f"- Configuration test failed: {e}")
        return False

def test_fastapi_app():
    """Test that FastAPI app can be created."""
    try:
        from src.api.main import app
        
        # Check that the app has the expected routes
        routes = [route.path for route in app.routes]
        expected_routes = ['/', '/health', '/api/v1/ask', '/api/v1/ask-voice']
        
        for expected_route in expected_routes:
            if expected_route not in routes:
                print(f"Warning: Route {expected_route} not found in {routes}")
        
        print("+ FastAPI app created successfully")
        print(f"  Available routes: {routes}")
        return True
    except Exception as e:
        print(f"- FastAPI app test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Retail Shelf Assistant API Contracts...")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Pydantic Models Test", test_pydantic_models),
        ("Configuration Test", test_config),
        ("FastAPI App Test", test_fastapi_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  FAILED")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All API contracts compile successfully!")
        sys.exit(0)
    else:
        print("Some tests failed. Check the output above.")
        sys.exit(1)
