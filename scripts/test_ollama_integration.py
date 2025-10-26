#!/usr/bin/env python3
"""
Test script to verify Ollama integration with Phi3.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.llm_service import LLMService

def test_ollama_connection():
    """Test basic Ollama connection."""
    print("Testing Ollama Connection...")
    
    service = LLMService()
    
    # Test health status
    health = service.get_health_status()
    print(f"Health Status: {health}")
    
    if health.get("status") == "healthy":
        print("+ Ollama is running and Phi3 model is available")
        return True
    else:
        print(f"- Ollama health check failed: {health.get('error', 'Unknown error')}")
        return False

def test_llm_generation():
    """Test LLM text generation."""
    print("\nTesting LLM Generation...")
    
    service = LLMService()
    
    # Test simple generation
    try:
        response = service.generate_info_answer(
            product="milk",
            question="what are the ingredients in milk"
        )
        
        print(f"Product: {response.normalized_product}")
        print(f"Answer: {response.answer}")
        print(f"Confidence: {response.confidence}")
        print(f"Caveats: {response.caveats}")
        
        if response.answer and len(response.answer) > 10:
            print("+ LLM generation working correctly")
            return True
        else:
            print("- LLM generation failed or returned empty response")
            return False
            
    except Exception as e:
        print(f"- LLM generation failed: {e}")
        return False

def test_different_question_types():
    """Test different types of questions."""
    print("\nTesting Different Question Types...")
    
    service = LLMService()
    
    test_cases = [
        ("milk", "what are the ingredients in milk"),
        ("yogurt", "how many calories in yogurt"),
        ("cheese", "what is the price of cheese"),
        ("bread", "is this product gluten free"),
        ("cereal", "tell me about this product")
    ]
    
    passed = 0
    total = len(test_cases)
    
    for product, question in test_cases:
        try:
            response = service.generate_info_answer(product, question)
            
            if response.answer and len(response.answer) > 10:
                print(f"+ {question[:30]}... - Generated response")
                passed += 1
            else:
                print(f"- {question[:30]}... - Empty or invalid response")
                
        except Exception as e:
            print(f"- {question[:30]}... - Error: {e}")
    
    success_rate = passed / total
    print(f"\nSuccess Rate: {passed}/{total} ({success_rate:.1%})")
    
    return success_rate >= 0.8

def test_no_location_leakage():
    """Test that responses don't contain location information."""
    print("\nTesting No Location Leakage...")
    
    service = LLMService()
    
    test_questions = [
        "what are the ingredients in milk",
        "how many calories in yogurt",
        "what is the price of cheese",
        "is this product gluten free",
        "tell me about this product"
    ]
    
    violations = 0
    total = len(test_questions)
    
    for question in test_questions:
        try:
            response = service.generate_info_answer("test product", question)
            answer_lower = response.answer.lower()
            
            location_words = ["aisle", "section", "shelf", "bay", "where", "located", "find", "near"]
            for word in location_words:
                if word in answer_lower:
                    print(f"- Location word '{word}' found in: {response.answer}")
                    violations += 1
                    break
            else:
                print(f"+ No location leakage in: {response.answer[:50]}...")
                
        except Exception as e:
            print(f"- Error testing {question}: {e}")
            violations += 1
    
    violation_rate = violations / total
    print(f"\nViolation Rate: {violations}/{total} ({violation_rate:.1%})")
    
    return violation_rate == 0

def main():
    """Run all tests."""
    print("Ollama Integration Test with Phi3")
    print("=" * 40)
    
    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("LLM Generation", test_llm_generation),
        ("Different Question Types", test_different_question_types),
        ("No Location Leakage", test_no_location_leakage)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  FAILED")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("+ All tests passed! Ollama integration is working correctly.")
        return True
    else:
        print("- Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
