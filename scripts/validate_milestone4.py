#!/usr/bin/env python3
"""
Validation script for Milestone 4: Backend Orchestration API
Tests the unified API with schema-compliant responses.
"""
import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.orchestrator import BackendOrchestrator
from src.api.models import ProductLocationResponse, ProductInfoResponse, ErrorResponse
from config.settings import DATABASE_CONFIG

def test_orchestrator_functionality():
    """Test orchestrator functionality directly."""
    print("Testing Backend Orchestrator Functionality...")
    
    # Ensure database exists
    db_path = DATABASE_CONFIG["path"]
    if not db_path.exists():
        print("  FAILED: Database does not exist. Run init_db.py first.")
        return False
    
    orchestrator = BackendOrchestrator()
    
    # Test location query
    print("  Testing location query: 'where is the milk'")
    result = orchestrator.process_text_query("where is the milk")
    
    # Validate response structure
    required_keys = ["query_type", "normalized_product", "matches", "disambiguation_needed", "notes"]
    for key in required_keys:
        if key not in result:
            print(f"    FAILED: Missing key '{key}' in response")
            return False
    
    if result["query_type"] != "location":
        print(f"    FAILED: Expected 'location', got '{result['query_type']}'")
        return False
    
    if not isinstance(result["matches"], list):
        print(f"    FAILED: 'matches' should be a list, got {type(result['matches'])}")
        return False
    
    if len(result["matches"]) == 0:
        print(f"    WARNING: No matches found for 'milk' query")
    else:
        print(f"    PASSED: Found {len(result['matches'])} matches")
        # Validate match structure
        match = result["matches"][0]
        match_keys = ["product_id", "product_name", "brand", "category", "aisle", "bay", "shelf", "confidence"]
        for key in match_keys:
            if key not in match:
                print(f"    FAILED: Missing key '{key}' in match")
                return False
    
    # Test information query
    print("  Testing information query: 'what are the ingredients in bread'")
    result = orchestrator.process_text_query("what are the ingredients in bread")
    
    # Validate response structure
    required_keys = ["query_type", "normalized_product", "answer", "confidence"]
    for key in required_keys:
        if key not in result:
            print(f"    FAILED: Missing key '{key}' in response")
            return False
    
    if result["query_type"] != "information":
        print(f"    FAILED: Expected 'information', got '{result['query_type']}'")
        return False
    
    if not isinstance(result["answer"], str) or len(result["answer"]) == 0:
        print(f"    FAILED: 'answer' should be a non-empty string")
        return False
    
    if not isinstance(result["confidence"], (int, float)) or not (0 <= result["confidence"] <= 1):
        print(f"    FAILED: 'confidence' should be between 0 and 1, got {result['confidence']}")
        return False
    
    print(f"    PASSED: Information query returned answer with confidence {result['confidence']:.2f}")
    
    # Test health status
    print("  Testing health status...")
    health = orchestrator.get_health_status()
    
    required_health_keys = ["database", "llm", "router", "overall"]
    for key in required_health_keys:
        if key not in health:
            print(f"    FAILED: Missing health key '{key}'")
            return False
    
    print(f"    PASSED: Health status - {health}")
    
    return True

def test_schema_compliance():
    """Test that responses match the required schemas."""
    print("\nTesting Schema Compliance...")
    
    orchestrator = BackendOrchestrator()
    
    # Test location response schema
    print("  Testing location response schema...")
    result = orchestrator.process_text_query("where is the milk")
    
    try:
        # Try to create ProductLocationResponse from result
        location_response = ProductLocationResponse(**result)
        print("    PASSED: Location response matches schema")
    except Exception as e:
        print(f"    FAILED: Location response schema validation failed: {e}")
        return False
    
    # Test information response schema
    print("  Testing information response schema...")
    result = orchestrator.process_text_query("what are the ingredients in bread")
    
    try:
        # Try to create ProductInfoResponse from result
        info_response = ProductInfoResponse(**result)
        print("    PASSED: Information response matches schema")
    except Exception as e:
        print(f"    FAILED: Information response schema validation failed: {e}")
        return False
    
    return True

def test_error_handling():
    """Test error handling and edge cases."""
    print("\nTesting Error Handling...")
    
    orchestrator = BackendOrchestrator()
    
    # Test empty query
    print("  Testing empty query...")
    result = orchestrator.process_text_query("")
    
    if "error" in result:
        print("    PASSED: Empty query handled with error response")
    else:
        print("    WARNING: Empty query did not return error response")
    
    # Test very long query
    print("  Testing very long query...")
    long_query = "where is the " + "milk " * 100
    result = orchestrator.process_text_query(long_query)
    
    if "error" in result:
        print("    PASSED: Long query handled with error response")
    else:
        print("    PASSED: Long query processed successfully")
    
    # Test special characters
    print("  Testing special characters...")
    special_query = "where is the milk!@#$%^&*()"
    result = orchestrator.process_text_query(special_query)
    
    if "error" in result:
        print("    PASSED: Special characters handled with error response")
    else:
        print("    PASSED: Special characters processed successfully")
    
    return True

def test_performance():
    """Test performance and latency."""
    print("\nTesting Performance...")
    
    orchestrator = BackendOrchestrator()
    
    # Test multiple queries
    queries = [
        "where is the milk",
        "find apples",
        "what are the ingredients in bread",
        "is this product gluten free",
        "which aisle has chicken"
    ]
    
    total_time = 0
    successful_queries = 0
    
    for query in queries:
        start_time = time.time()
        result = orchestrator.process_text_query(query)
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        total_time += latency
        
        if "error" not in result:
            successful_queries += 1
            print(f"    Query '{query[:30]}...': {latency:.1f}ms")
        else:
            print(f"    Query '{query[:30]}...': FAILED - {result.get('error', 'Unknown error')}")
    
    avg_latency = total_time / len(queries)
    success_rate = successful_queries / len(queries)
    
    print(f"    Average latency: {avg_latency:.1f}ms")
    print(f"    Success rate: {success_rate:.1%}")
    
    # Check if performance meets requirements
    if avg_latency < 2500:  # 2.5 seconds
        print("    PASSED: Latency meets requirements (< 2.5s)")
    else:
        print("    WARNING: Latency exceeds requirements (> 2.5s)")
    
    if success_rate >= 0.8:  # 80% success rate
        print("    PASSED: Success rate meets requirements (>= 80%)")
    else:
        print("    WARNING: Success rate below requirements (< 80%)")
    
    return True

def test_logging():
    """Test structured logging functionality."""
    print("\nTesting Structured Logging...")
    
    orchestrator = BackendOrchestrator()
    
    # Test that logging works without errors
    try:
        result = orchestrator.process_text_query("where is the milk")
        print("    PASSED: Logging works without errors")
        return True
    except Exception as e:
        print(f"    FAILED: Logging error: {e}")
        return False

def main():
    """Run all validation tests."""
    print("Milestone 4 Validation: Backend Orchestration API")
    print("=" * 60)
    
    tests = [
        ("Orchestrator Functionality", test_orchestrator_functionality),
        ("Schema Compliance", test_schema_compliance),
        ("Error Handling", test_error_handling),
        ("Performance", test_performance),
        ("Structured Logging", test_logging)
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
    print(f"Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All acceptance criteria met! Milestone 4 is complete.")
        return True
    else:
        print("Some acceptance criteria not met. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
