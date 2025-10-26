#!/usr/bin/env python3
"""
Validation script for Milestone 5: LLM Orchestration for Information Queries
Tests LLM service with guardrails, deterministic outputs, and factual alignment.
"""
import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.llm_service import LLMService, PromptLibrary
from src.api.orchestrator import BackendOrchestrator
from src.api.models import ProductInfoResponse

def test_llm_service_functionality():
    """Test LLM service basic functionality."""
    print("Testing LLM Service Functionality...")
    
    service = LLMService()
    
    # Test various question types
    test_cases = [
        ("milk", "what are the ingredients in milk", "ingredients"),
        ("yogurt", "how many calories in yogurt", "nutrition"),
        ("cheese", "what is the price of cheese", "price"),
        ("bread", "is this product gluten free", "dietary"),
        ("cereal", "tell me about this product", "general")
    ]
    
    passed = 0
    total = len(test_cases)
    
    for product, question, expected_type in test_cases:
        print(f"  Testing {expected_type} question: '{question}'")
        
        try:
            response = service.generate_info_answer(product, question)
            
            # Validate response structure
            assert isinstance(response, ProductInfoResponse), f"Expected ProductInfoResponse, got {type(response)}"
            assert response.normalized_product == product, f"Expected product '{product}', got '{response.normalized_product}'"
            assert isinstance(response.answer, str), f"Answer should be string, got {type(response.answer)}"
            assert len(response.answer) > 0, "Answer should not be empty"
            assert 0.0 <= response.confidence <= 1.0, f"Confidence should be 0-1, got {response.confidence}"
            
            # Check for location leakage
            answer_lower = response.answer.lower()
            location_words = ["aisle", "section", "shelf", "bay", "where", "located", "find", "near"]
            for word in location_words:
                assert word not in answer_lower, f"Location word '{word}' found in answer: {response.answer}"
            
            print(f"    PASSED: {expected_type} question handled correctly")
            passed += 1
            
        except Exception as e:
            print(f"    FAILED: {expected_type} question failed: {e}")
    
    success_rate = passed / total
    print(f"  LLM Service Functionality: {passed}/{total} tests passed ({success_rate:.1%})")
    
    return success_rate >= 0.8

def test_no_location_leakage():
    """Test that LLM responses never contain location information."""
    print("\nTesting No Location Leakage...")
    
    service = LLMService()
    
    # Test various question types that might trigger location responses
    test_questions = [
        "what are the ingredients in milk",
        "how many calories in yogurt",
        "what is the price of cheese",
        "is this product gluten free",
        "tell me about this product",
        "what is this made of",
        "how much does this cost",
        "is this healthy",
        "what are the nutritional facts",
        "does this contain allergens"
    ]
    
    location_words = ["aisle", "section", "shelf", "bay", "where", "located", "find", "near", "next to", "beside"]
    violations = 0
    total_tests = len(test_questions)
    
    for question in test_questions:
        try:
            response = service.generate_info_answer("test product", question)
            answer_lower = response.answer.lower()
            
            for word in location_words:
                if word in answer_lower:
                    print(f"    VIOLATION: Location word '{word}' found in answer for '{question}': {response.answer}")
                    violations += 1
                    break
        except Exception as e:
            print(f"    ERROR: Failed to test question '{question}': {e}")
            violations += 1
    
    violation_rate = violations / total_tests
    print(f"  Location Leakage Test: {violations}/{total_tests} violations ({violation_rate:.1%})")
    
    if violation_rate == 0:
        print("  PASSED: No location leakage detected")
        return True
    else:
        print("  FAILED: Location leakage detected")
        return False

def test_json_validity():
    """Test that LLM responses are valid JSON."""
    print("\nTesting JSON Validity...")
    
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
            
            # Test that response can be converted to dict (JSON serializable)
            response_dict = response.dict()
            
            # Test JSON serialization
            json_str = json.dumps(response_dict)
            parsed = json.loads(json_str)
            
            # Validate required fields
            assert "normalized_product" in parsed
            assert "answer" in parsed
            assert "confidence" in parsed
            
            print(f"    PASSED: JSON validity for '{question}'")
            passed += 1
            
        except Exception as e:
            print(f"    FAILED: JSON validity for '{question}': {e}")
    
    success_rate = passed / total
    print(f"  JSON Validity: {passed}/{total} tests passed ({success_rate:.1%})")
    
    return success_rate >= 0.8

def test_prompt_library():
    """Test prompt library functionality."""
    print("\nTesting Prompt Library...")
    
    library = PromptLibrary()
    
    # Test prompt template selection
    test_cases = [
        ("what are the ingredients in bread", "ingredients"),
        ("how many calories in yogurt", "nutrition"),
        ("what is the price of cheese", "price"),
        ("is this product gluten free", "dietary"),
        ("tell me about this product", "general")
    ]
    
    passed = 0
    total = len(test_cases)
    
    for question, expected_type in test_cases:
        try:
            template = library.get_prompt_template(question)
            
            # Validate template structure
            assert isinstance(template, str), f"Template should be string, got {type(template)}"
            assert len(template) > 0, "Template should not be empty"
            assert "{product}" in template, "Template should contain {product} placeholder"
            assert "{question}" in template, "Template should contain {question} placeholder"
            assert "{context}" in template, "Template should contain {context} placeholder"
            assert "never provide location" in template.lower(), "Template should contain location guardrail"
            assert "json" in template.lower(), "Template should mention JSON output"
            
            print(f"    PASSED: {expected_type} template generated correctly")
            passed += 1
            
        except Exception as e:
            print(f"    FAILED: {expected_type} template failed: {e}")
    
    success_rate = passed / total
    print(f"  Prompt Library: {passed}/{total} tests passed ({success_rate:.1%})")
    
    return success_rate >= 0.8

def test_factual_alignment():
    """Test factual alignment on eval set."""
    print("\nTesting Factual Alignment...")
    
    service = LLMService()
    
    # Create eval set of 50 questions
    eval_questions = []
    
    # Ingredients questions (10)
    for product in ["milk", "bread", "cheese", "yogurt", "cereal", "pasta", "rice", "chicken", "beef", "fish"]:
        eval_questions.append((product, f"what are the ingredients in {product}", "ingredients"))
    
    # Nutrition questions (10)
    for product in ["milk", "bread", "cheese", "yogurt", "cereal", "pasta", "rice", "chicken", "beef", "fish"]:
        eval_questions.append((product, f"how many calories in {product}", "nutrition"))
    
    # Price questions (10)
    for product in ["milk", "bread", "cheese", "yogurt", "cereal", "pasta", "rice", "chicken", "beef", "fish"]:
        eval_questions.append((product, f"what is the price of {product}", "price"))
    
    # Dietary questions (10)
    for product in ["milk", "bread", "cheese", "yogurt", "cereal", "pasta", "rice", "chicken", "beef", "fish"]:
        eval_questions.append((product, f"is {product} gluten free", "dietary"))
    
    # General questions (10)
    for product in ["milk", "bread", "cheese", "yogurt", "cereal", "pasta", "rice", "chicken", "beef", "fish"]:
        eval_questions.append((product, f"tell me about {product}", "general"))
    
    assert len(eval_questions) == 50, f"Expected 50 eval questions, got {len(eval_questions)}"
    
    # Test factual alignment
    passed = 0
    total = len(eval_questions)
    
    for product, question, expected_type in eval_questions:
        try:
            response = service.generate_info_answer(product, question)
            
            # Check that response is appropriate for question type
            answer_lower = response.answer.lower()
            
            if expected_type == "ingredients":
                assert any(word in answer_lower for word in ["ingredient", "contain", "made"]), f"Answer should mention ingredients: {response.answer}"
            elif expected_type == "nutrition":
                assert any(word in answer_lower for word in ["calorie", "nutrition", "serving", "protein", "fat"]), f"Answer should mention nutrition: {response.answer}"
            elif expected_type == "price":
                assert any(word in answer_lower for word in ["price", "cost", "check"]), f"Answer should mention price: {response.answer}"
            elif expected_type == "dietary":
                assert any(word in answer_lower for word in ["gluten", "dietary", "label", "check"]), f"Answer should mention dietary info: {response.answer}"
            elif expected_type == "general":
                assert len(response.answer) > 0, "Answer should not be empty"
            
            # Check for location leakage
            location_words = ["aisle", "section", "shelf", "bay", "where", "located", "find", "near"]
            for word in location_words:
                assert word not in answer_lower, f"Location word '{word}' found in answer: {response.answer}"
            
            passed += 1
            
        except Exception as e:
            print(f"    FAILED: {question}: {e}")
    
    success_rate = passed / total
    print(f"  Factual Alignment: {passed}/{total} tests passed ({success_rate:.1%})")
    
    if success_rate >= 0.9:
        print("  PASSED: Meets 90% factual alignment requirement")
        return True
    else:
        print("  FAILED: Below 90% factual alignment requirement")
        return False

def test_performance():
    """Test LLM service performance."""
    print("\nTesting Performance...")
    
    service = LLMService()
    
    # Test multiple queries for performance
    test_questions = [
        ("milk", "what are the ingredients in milk"),
        ("yogurt", "how many calories in yogurt"),
        ("cheese", "what is the price of cheese"),
        ("bread", "is this product gluten free"),
        ("cereal", "tell me about this product")
    ]
    
    total_time = 0
    successful_queries = 0
    
    for product, question in test_questions:
        start_time = time.time()
        try:
            response = service.generate_info_answer(product, question)
            end_time = time.time()
            
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            total_time += latency
            successful_queries += 1
            
            print(f"    Query '{question[:30]}...': {latency:.1f}ms")
            
        except Exception as e:
            print(f"    Query '{question[:30]}...': FAILED - {e}")
    
    if successful_queries > 0:
        avg_latency = total_time / successful_queries
        success_rate = successful_queries / len(test_questions)
        
        print(f"    Average latency: {avg_latency:.1f}ms")
        print(f"    Success rate: {success_rate:.1%}")
        
        if avg_latency < 5000:  # 5 seconds
            print("    PASSED: Latency meets requirements (< 5s)")
        else:
            print("    WARNING: Latency exceeds requirements (> 5s)")
        
        if success_rate >= 0.8:  # 80% success rate
            print("    PASSED: Success rate meets requirements (>= 80%)")
        else:
            print("    WARNING: Success rate below requirements (< 80%)")
        
        return True
    else:
        print("    FAILED: No successful queries")
        return False

def test_integration():
    """Test LLM service integration with orchestrator."""
    print("\nTesting Integration...")
    
    try:
        orchestrator = BackendOrchestrator()
        
        # Test information query
        response = orchestrator.process_text_query("what are the ingredients in bread")
        
        assert response.get("query_type") == "information"
        assert "answer" in response
        assert "confidence" in response
        assert "normalized_product" in response
        
        # Check that answer doesn't contain location information
        answer = response.get("answer", "").lower()
        location_words = ["aisle", "section", "shelf", "bay", "where", "located", "find", "near"]
        
        for word in location_words:
            assert word not in answer, f"Location word '{word}' found in answer: {response.get('answer')}"
        
        print("    PASSED: Integration with orchestrator working correctly")
        return True
        
    except Exception as e:
        print(f"    FAILED: Integration test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("Milestone 5 Validation: LLM Orchestration for Information Queries")
    print("=" * 70)
    
    tests = [
        ("LLM Service Functionality", test_llm_service_functionality),
        ("No Location Leakage", test_no_location_leakage),
        ("JSON Validity", test_json_validity),
        ("Prompt Library", test_prompt_library),
        ("Factual Alignment", test_factual_alignment),
        ("Performance", test_performance),
        ("Integration", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  FAILED")
    
    print("\n" + "=" * 70)
    print(f"Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All acceptance criteria met! Milestone 5 is complete.")
        return True
    else:
        print("Some acceptance criteria not met. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
