"""
Tests for LLM Service.
Verifies JSON validity, no location leakage, and factual alignment.
"""
import pytest
import json
from unittest.mock import Mock, patch

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.llm_service import LLMService, PromptLibrary
from src.api.models import ProductInfoResponse

class TestLLMService:
    """Test LLM service functionality."""
    
    def test_llm_service_initialization(self):
        """Test LLM service initialization."""
        service = LLMService()
        assert service.model_name == "phi3"
        assert service.temperature == 0.3
        assert service.max_tokens == 200
        assert service.timeout == 30
    
    def test_generate_info_answer_ingredients(self):
        """Test generating answer for ingredients question."""
        service = LLMService()
        
        response = service.generate_info_answer(
            product="milk",
            question="what are the ingredients in milk"
        )
        
        assert isinstance(response, ProductInfoResponse)
        assert response.normalized_product == "milk"
        assert isinstance(response.answer, str)
        assert len(response.answer) > 0
        assert 0.0 <= response.confidence <= 1.0
        assert "ingredient" in response.answer.lower()
    
    def test_generate_info_answer_nutrition(self):
        """Test generating answer for nutrition question."""
        service = LLMService()
        
        response = service.generate_info_answer(
            product="yogurt",
            question="how many calories in yogurt"
        )
        
        assert isinstance(response, ProductInfoResponse)
        assert response.normalized_product == "yogurt"
        assert isinstance(response.answer, str)
        assert len(response.answer) > 0
        assert 0.0 <= response.confidence <= 1.0
        assert any(word in response.answer.lower() for word in ["calorie", "nutrition", "serving"])
    
    def test_generate_info_answer_price(self):
        """Test generating answer for price question."""
        service = LLMService()
        
        response = service.generate_info_answer(
            product="cheese",
            question="what is the price of cheese"
        )
        
        assert isinstance(response, ProductInfoResponse)
        assert response.normalized_product == "cheese"
        assert isinstance(response.answer, str)
        assert len(response.answer) > 0
        assert 0.0 <= response.confidence <= 1.0
        assert any(word in response.answer.lower() for word in ["price", "cost", "check"])
    
    def test_generate_info_answer_dietary(self):
        """Test generating answer for dietary question."""
        service = LLMService()
        
        response = service.generate_info_answer(
            product="bread",
            question="is this product gluten free"
        )
        
        assert isinstance(response, ProductInfoResponse)
        assert response.normalized_product == "bread"
        assert isinstance(response.answer, str)
        assert len(response.answer) > 0
        assert 0.0 <= response.confidence <= 1.0
        assert any(word in response.answer.lower() for word in ["gluten", "dietary", "label"])
    
    def test_generate_info_answer_with_db_attributes(self):
        """Test generating answer with database attributes."""
        service = LLMService()
        
        db_attributes = {
            "brand": "Organic Valley",
            "category": "Dairy",
            "price": "4.99"
        }
        
        response = service.generate_info_answer(
            product="milk",
            question="what is the price of milk",
            db_attributes=db_attributes
        )
        
        assert isinstance(response, ProductInfoResponse)
        assert response.normalized_product == "milk"
        assert isinstance(response.answer, str)
        assert len(response.answer) > 0
        assert 0.0 <= response.confidence <= 1.0
    
    def test_no_location_leakage(self):
        """Test that answers never contain location information."""
        service = LLMService()
        
        # Test various question types
        questions = [
            "what are the ingredients in milk",
            "how many calories in yogurt",
            "what is the price of cheese",
            "is this product gluten free",
            "tell me about this product"
        ]
        
        for question in questions:
            response = service.generate_info_answer(
                product="test product",
                question=question
            )
            
            # Check that answer doesn't contain location-related words
            location_words = ["aisle", "section", "shelf", "bay", "where", "located", "find", "near"]
            answer_lower = response.answer.lower()
            
            for word in location_words:
                assert word not in answer_lower, f"Location word '{word}' found in answer: {response.answer}"
    
    def test_json_validity(self):
        """Test that LLM responses are valid JSON."""
        service = LLMService()
        
        # Test that the service handles JSON parsing correctly
        response = service.generate_info_answer(
            product="milk",
            question="what are the ingredients in milk"
        )
        
        # The response should be a valid ProductInfoResponse
        assert isinstance(response, ProductInfoResponse)
        assert response.normalized_product == "milk"
        assert isinstance(response.answer, str)
        assert 0.0 <= response.confidence <= 1.0
    
    def test_fallback_response(self):
        """Test fallback response when LLM fails."""
        service = LLMService()
        
        # Mock the LLM call to fail
        with patch.object(service, '_call_llm', side_effect=Exception("LLM failed")):
            response = service.generate_info_answer(
                product="milk",
                question="what are the ingredients in milk"
            )
            
            assert isinstance(response, ProductInfoResponse)
            assert response.normalized_product == "milk"
            assert "sorry" in response.answer.lower() or "unavailable" in response.answer.lower()
            assert response.confidence < 0.5
            assert response.caveats is not None
    
    def test_health_status(self):
        """Test health status check."""
        service = LLMService()
        
        health = service.get_health_status()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert "model" in health
        assert "base_url" in health
        assert health["model"] == "phi3"
    
    def test_caveats_determination(self):
        """Test caveats determination logic."""
        service = LLMService()
        
        # Test low confidence caveat
        response = service.generate_info_answer(
            product="unknown product",
            question="what is this"
        )
        
        # Should have caveats for low confidence or missing product info
        if response.caveats:
            assert isinstance(response.caveats, str)
            assert len(response.caveats) > 0

class TestPromptLibrary:
    """Test prompt library functionality."""
    
    def test_prompt_library_initialization(self):
        """Test prompt library initialization."""
        library = PromptLibrary()
        
        assert hasattr(library, 'templates')
        assert isinstance(library.templates, dict)
        assert len(library.templates) > 0
    
    def test_get_prompt_template_ingredients(self):
        """Test getting ingredients prompt template."""
        library = PromptLibrary()
        
        template = library.get_prompt_template("what are the ingredients in bread")
        
        assert isinstance(template, str)
        assert "ingredient" in template.lower()
        assert "never provide location" in template.lower()
        assert "{product}" in template
        assert "{question}" in template
        assert "{context}" in template
    
    def test_get_prompt_template_nutrition(self):
        """Test getting nutrition prompt template."""
        library = PromptLibrary()
        
        template = library.get_prompt_template("how many calories in yogurt")
        
        assert isinstance(template, str)
        assert "nutrition" in template.lower() or "calorie" in template.lower()
        assert "never provide location" in template.lower()
        assert "{product}" in template
        assert "{question}" in template
        assert "{context}" in template
    
    def test_get_prompt_template_price(self):
        """Test getting price prompt template."""
        library = PromptLibrary()
        
        template = library.get_prompt_template("what is the price of cheese")
        
        assert isinstance(template, str)
        assert "price" in template.lower()
        assert "never provide location" in template.lower()
        assert "{product}" in template
        assert "{question}" in template
        assert "{context}" in template
    
    def test_get_prompt_template_dietary(self):
        """Test getting dietary prompt template."""
        library = PromptLibrary()
        
        template = library.get_prompt_template("is this product gluten free")
        
        assert isinstance(template, str)
        assert "dietary" in template.lower() or "gluten" in template.lower()
        assert "never provide location" in template.lower()
        assert "{product}" in template
        assert "{question}" in template
        assert "{context}" in template
    
    def test_get_prompt_template_general(self):
        """Test getting general prompt template."""
        library = PromptLibrary()
        
        template = library.get_prompt_template("tell me about this product")
        
        assert isinstance(template, str)
        assert "never provide location" in template.lower()
        assert "{product}" in template
        assert "{question}" in template
        assert "{context}" in template
    
    def test_prompt_templates_contain_guardrails(self):
        """Test that all prompt templates contain guardrails."""
        library = PromptLibrary()
        
        test_questions = [
            "what are the ingredients in bread",
            "how many calories in yogurt",
            "what is the price of cheese",
            "is this product gluten free",
            "tell me about this product"
        ]
        
        for question in test_questions:
            template = library.get_prompt_template(question)
            
            # Check for guardrails
            assert "never provide location" in template.lower()
            assert "only answer" in template.lower()
            assert "json" in template.lower()
            assert "confidence" in template.lower()

class TestLLMServiceIntegration:
    """Test LLM service integration with orchestrator."""
    
    def test_llm_service_with_orchestrator(self):
        """Test LLM service integration with orchestrator."""
        from src.api.orchestrator import BackendOrchestrator
        
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
    
    def test_llm_service_health_integration(self):
        """Test LLM service health integration."""
        from src.api.orchestrator import BackendOrchestrator
        
        orchestrator = BackendOrchestrator()
        
        health = orchestrator.get_health_status()
        
        assert "llm" in health
        assert health["llm"] in ["healthy", "unhealthy"]
    
    def test_llm_service_performance(self):
        """Test LLM service performance."""
        import time
        
        service = LLMService()
        
        start_time = time.time()
        response = service.generate_info_answer(
            product="milk",
            question="what are the ingredients in milk"
        )
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert latency < 5000  # Should be under 5 seconds
        assert isinstance(response, ProductInfoResponse)
        assert response.normalized_product == "milk"
        assert len(response.answer) > 0
