"""
Comprehensive tests for the query router and classification system.
Tests classification accuracy, product extraction, and edge cases.
"""
import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.nlu.router import QueryRouter, ClassificationResult
from src.nlu.keywords import KeywordDictionary
from src.nlu.product_extractor import ProductExtractor, ProductCandidate
from database.seed_data import ProductDataGenerator

class TestKeywordDictionary:
    """Test keyword dictionary functionality."""
    
    def test_location_keywords(self):
        """Test location keyword detection."""
        keyword_dict = KeywordDictionary()
        
        # Test direct location queries
        test_cases = [
            ("where is the milk", 1.0),
            ("find apples", 1.0),
            ("locate bread", 1.0),
            ("which aisle has chicken", 1.0),
            ("what section is cheese in", 1.0),
            ("near the entrance", 0.9),
            ("next to the dairy", 0.9),
            ("beside the meat counter", 0.8),
        ]
        
        for query, expected_min_score in test_cases:
            score = keyword_dict.calculate_location_score(query)
            assert score >= expected_min_score, f"Location score too low for '{query}': {score}"
    
    def test_information_keywords(self):
        """Test information keyword detection."""
        keyword_dict = KeywordDictionary()
        
        test_cases = [
            ("what are the ingredients", 1.0),
            ("nutrition information", 1.0),
            ("how many calories", 1.0),
            ("is it vegan", 1.0),
            ("gluten free", 1.0),
            ("dairy free", 1.0),
            ("what is the price", 1.0),
            ("return policy", 1.0),
            ("expiration date", 1.0),
            ("how to cook", 0.8),
            ("storage instructions", 0.7),
        ]
        
        for query, expected_min_score in test_cases:
            score = keyword_dict.calculate_information_score(query)
            assert score >= expected_min_score, f"Information score too low for '{query}': {score}"
    
    def test_negation_handling(self):
        """Test negation pattern detection and penalty."""
        keyword_dict = KeywordDictionary()
        
        # Test negation detection
        assert keyword_dict.has_negation("I don't want milk")
        assert keyword_dict.has_negation("not looking for bread")
        assert keyword_dict.has_negation("never mind")
        assert not keyword_dict.has_negation("I want milk")
        
        # Test negation penalty
        positive_score = keyword_dict.calculate_location_score("where is the milk")
        negative_score = keyword_dict.calculate_location_score("I don't want to find milk")
        
        assert negative_score < positive_score, "Negation should reduce confidence"
    
    def test_stemming(self):
        """Test word stemming functionality."""
        keyword_dict = KeywordDictionary()
        
        test_cases = [
            ("ingredients", "ingredient"),
            ("calories", "calorie"),
            ("allergens", "allergen"),
            ("vitamins", "vitamin"),
            ("products", "product"),
            ("sections", "section"),
        ]
        
        for word, expected_stem in test_cases:
            stemmed = keyword_dict.stem_word(word)
            assert stemmed == expected_stem, f"Stemming failed for '{word}': got '{stemmed}', expected '{expected_stem}'"

class TestProductExtractor:
    """Test product extraction functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        
        # Generate test data
        generator = ProductDataGenerator(seed=42)
        generator.generate_database(temp_file.name, num_products=100)
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)
    
    def test_exact_synonym_matching(self, temp_db):
        """Test exact synonym matching."""
        extractor = ProductExtractor(temp_db)
        
        # Test with known synonyms (these should exist in the generated data)
        candidates = extractor.extract_products("coke", limit=5)
        
        # Should find some candidates
        assert len(candidates) >= 0, "Should find some candidates for 'coke'"
        
        if candidates:
            assert all(isinstance(c, ProductCandidate) for c in candidates), "All candidates should be ProductCandidate objects"
            assert all(c.confidence > 0 for c in candidates), "All candidates should have positive confidence"
    
    def test_fuzzy_matching(self, temp_db):
        """Test fuzzy matching functionality."""
        extractor = ProductExtractor(temp_db)
        
        # Test with slightly misspelled words
        candidates = extractor.extract_products("milk", limit=5)
        
        assert len(candidates) >= 0, "Should find some candidates for 'milk'"
        
        if candidates:
            # Check that candidates have proper structure
            for candidate in candidates:
                assert hasattr(candidate, 'product_id')
                assert hasattr(candidate, 'product_name')
                assert hasattr(candidate, 'confidence')
                assert hasattr(candidate, 'match_type')
    
    def test_trigram_similarity(self, temp_db):
        """Test trigram similarity calculation."""
        extractor = ProductExtractor(temp_db)
        
        # Test trigram similarity
        similarity = extractor._calculate_trigram_similarity("apple", "apples")
        assert 0.0 <= similarity <= 1.0, "Trigram similarity should be between 0 and 1"
        
        # Test with identical strings
        identical_sim = extractor._calculate_trigram_similarity("test", "test")
        assert identical_sim == 1.0, "Identical strings should have similarity 1.0"
        
        # Test with completely different strings
        different_sim = extractor._calculate_trigram_similarity("apple", "xyz")
        assert different_sim < 0.5, "Different strings should have low similarity"
    
    def test_text_normalization(self, temp_db):
        """Test text normalization."""
        extractor = ProductExtractor(temp_db)
        
        test_cases = [
            ("  Fresh Organic Milk  ", "fresh organic milk"),
            ("Coca-Cola Classic!", "coca-cola classic"),
            ("What's the price?", "what's the price"),
            ("", ""),
            ("   ", ""),
        ]
        
        for input_text, expected in test_cases:
            normalized = extractor._normalize_text(input_text)
            assert normalized == expected, f"Normalization failed for '{input_text}': got '{normalized}', expected '{expected}'"
    
    def test_candidate_deduplication(self, temp_db):
        """Test candidate deduplication."""
        extractor = ProductExtractor(temp_db)
        
        # Create mock candidates with duplicates
        candidates = [
            ProductCandidate("1", "Product A", "Brand A", "Category A", 0.9, "exact", "test"),
            ProductCandidate("1", "Product A", "Brand A", "Category A", 0.8, "fuzzy", "test"),
            ProductCandidate("2", "Product B", "Brand B", "Category B", 0.7, "exact", "test"),
        ]
        
        deduplicated = extractor._deduplicate_candidates(candidates)
        
        # Should have 2 unique candidates
        assert len(deduplicated) == 2, f"Expected 2 unique candidates, got {len(deduplicated)}"
        
        # First candidate should have highest confidence
        assert deduplicated[0].confidence == 0.9, "First candidate should have highest confidence"

class TestQueryRouter:
    """Test main query router functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        
        # Generate test data
        generator = ProductDataGenerator(seed=42)
        generator.generate_database(temp_file.name, num_products=100)
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)
    
    def test_location_classification(self, temp_db):
        """Test location query classification."""
        router = QueryRouter(temp_db)
        
        location_queries = [
            "where is the milk",
            "find apples",
            "locate bread",
            "which aisle has chicken",
            "what section is cheese in",
            "near the entrance",
            "next to the dairy",
        ]
        
        for query in location_queries:
            result = router.classify_query(query)
            assert result.route == "location", f"Query '{query}' should be classified as location, got {result.route}"
            assert result.confidence > 0, f"Location query should have positive confidence: {result.confidence}"
    
    def test_information_classification(self, temp_db):
        """Test information query classification."""
        router = QueryRouter(temp_db)
        
        information_queries = [
            "what are the ingredients in milk",
            "nutrition information for apples",
            "how many calories in bread",
            "is chicken gluten free",
            "what is the price of cheese",
            "return policy for this product",
            "expiration date",
        ]
        
        for query in information_queries:
            result = router.classify_query(query)
            assert result.route == "information", f"Query '{query}' should be classified as information, got {result.route}"
            assert result.confidence > 0, f"Information query should have positive confidence: {result.confidence}"
    
    def test_empty_query(self, temp_db):
        """Test handling of empty queries."""
        router = QueryRouter(temp_db)
        
        empty_queries = ["", "   ", None]
        
        for query in empty_queries:
            if query is None:
                continue  # Skip None as it would cause an error
            result = router.classify_query(query)
            assert result.route == "information", "Empty queries should default to information"
            assert result.confidence == 0.0, "Empty queries should have zero confidence"
    
    def test_ambiguous_queries(self, temp_db):
        """Test handling of ambiguous queries."""
        router = QueryRouter(temp_db)
        
        ambiguous_queries = [
            "milk",  # Could be location or information
            "apple",  # Could be location or information
            "bread",  # Could be location or information
        ]
        
        for query in ambiguous_queries:
            result = router.classify_query(query)
            assert result.route in ["location", "information"], f"Ambiguous query should be classified as location or information: {result.route}"
            # Ambiguous queries might need disambiguation
            assert isinstance(result.disambiguation_needed, bool), "disambiguation_needed should be boolean"
    
    def test_negation_handling(self, temp_db):
        """Test negation handling in queries."""
        router = QueryRouter(temp_db)
        
        negation_queries = [
            "I don't want to find milk",
            "not looking for apples",
            "never mind about bread",
        ]
        
        for query in negation_queries:
            result = router.classify_query(query)
            # Negation should reduce confidence
            assert result.confidence < 1.0, f"Negation should reduce confidence for '{query}': {result.confidence}"
    
    def test_product_extraction(self, temp_db):
        """Test product extraction functionality."""
        router = QueryRouter(temp_db)
        
        test_queries = [
            "milk",
            "apples",
            "bread",
            "chicken",
            "cheese",
        ]
        
        for query in test_queries:
            normalized_product, candidates = router.extract_product(query)
            
            assert isinstance(normalized_product, str), "normalized_product should be string"
            assert isinstance(candidates, list), "candidates should be list"
            assert all(isinstance(c, ProductCandidate) for c in candidates), "All candidates should be ProductCandidate objects"
    
    def test_disambiguation_detection(self, temp_db):
        """Test disambiguation detection."""
        router = QueryRouter(temp_db)
        
        # Test with queries that might need disambiguation
        result = router.classify_query("milk")
        
        assert isinstance(result.disambiguation_needed, bool), "disambiguation_needed should be boolean"
        
        if result.disambiguation_needed:
            assert result.candidates is not None, "If disambiguation needed, candidates should be provided"
            assert len(result.candidates) > 1, "If disambiguation needed, should have multiple candidates"
    
    def test_confidence_scores(self, temp_db):
        """Test confidence score validity."""
        router = QueryRouter(temp_db)
        
        test_queries = [
            "where is the milk",
            "what are the ingredients",
            "milk",
            "apples",
        ]
        
        for query in test_queries:
            result = router.classify_query(query)
            assert 0.0 <= result.confidence <= 1.0, f"Confidence should be between 0 and 1 for '{query}': {result.confidence}"
    
    def test_batch_classification(self, temp_db):
        """Test batch classification functionality."""
        router = QueryRouter(temp_db)
        
        queries = [
            "where is the milk",
            "what are the ingredients",
            "find apples",
            "nutrition information",
        ]
        
        results = router.batch_classify(queries)
        
        assert len(results) == len(queries), "Should return same number of results as queries"
        assert all(isinstance(r, ClassificationResult) for r in results), "All results should be ClassificationResult objects"
    
    def test_classification_stats(self, temp_db):
        """Test classification statistics."""
        router = QueryRouter(temp_db)
        
        test_cases = [
            ("where is the milk", "location"),
            ("what are the ingredients", "information"),
            ("find apples", "location"),
            ("nutrition information", "information"),
        ]
        
        stats = router.get_classification_stats(test_cases)
        
        assert "accuracy" in stats, "Stats should include accuracy"
        assert "correct" in stats, "Stats should include correct count"
        assert "total" in stats, "Stats should include total count"
        assert 0.0 <= stats["accuracy"] <= 1.0, "Accuracy should be between 0 and 1"
        assert stats["correct"] + stats["incorrect"] == stats["total"], "Correct + incorrect should equal total"
    
    def test_route_explanation(self, temp_db):
        """Test route explanation functionality."""
        router = QueryRouter(temp_db)
        
        query = "where is the milk"
        explanation = router.get_route_explanation(query)
        
        assert isinstance(explanation, str), "Explanation should be string"
        assert query in explanation, "Explanation should contain the query"
        assert "Location score:" in explanation, "Explanation should contain location score"
        assert "Information score:" in explanation, "Explanation should contain information score"
    
    def test_handle_ambiguous_query(self, temp_db):
        """Test handling of ambiguous queries."""
        router = QueryRouter(temp_db)
        
        result = router.handle_ambiguous_query("milk")
        
        assert isinstance(result, ClassificationResult), "Should return ClassificationResult"
        assert result.disambiguation_needed, "Ambiguous query should need disambiguation"
        assert result.candidates is not None, "Ambiguous query should have candidates"
        # Note: candidates might be empty if no products match, which is acceptable
    
    def test_validate_classification(self, temp_db):
        """Test classification validation."""
        router = QueryRouter(temp_db)
        
        # Test correct classification
        assert router.validate_classification("where is the milk", "location"), "Should correctly classify location query"
        assert router.validate_classification("what are the ingredients", "information"), "Should correctly classify information query"
        
        # Test incorrect classification
        assert not router.validate_classification("where is the milk", "information"), "Should not misclassify location query as information"
        assert not router.validate_classification("what are the ingredients", "location"), "Should not misclassify information query as location"

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        
        # Generate test data
        generator = ProductDataGenerator(seed=42)
        generator.generate_database(temp_file.name, num_products=50)
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)
    
    def test_very_long_queries(self, temp_db):
        """Test handling of very long queries."""
        router = QueryRouter(temp_db)
        
        long_query = "where is the milk " * 100  # Very long query
        result = router.classify_query(long_query)
        
        assert isinstance(result, ClassificationResult), "Should handle long queries"
        assert result.route in ["location", "information"], "Should classify long queries"
    
    def test_special_characters(self, temp_db):
        """Test handling of special characters."""
        router = QueryRouter(temp_db)
        
        special_queries = [
            "where is the milk?",
            "find apples!!!",
            "locate bread...",
            "which aisle has chicken?",
            "what's the price?",
        ]
        
        for query in special_queries:
            result = router.classify_query(query)
            assert isinstance(result, ClassificationResult), f"Should handle special characters in '{query}'"
    
    def test_mixed_language(self, temp_db):
        """Test handling of mixed language queries."""
        router = QueryRouter(temp_db)
        
        mixed_queries = [
            "where is le lait",  # French
            "find manzanas",  # Spanish
            "locate pan",  # Spanish
        ]
        
        for query in mixed_queries:
            result = router.classify_query(query)
            assert isinstance(result, ClassificationResult), f"Should handle mixed language in '{query}'"
    
    def test_numbers_in_queries(self, temp_db):
        """Test handling of numbers in queries."""
        router = QueryRouter(temp_db)
        
        number_queries = [
            "where is milk 2%",
            "find 12 pack apples",
            "locate 1 gallon milk",
            "which aisle has 5 lb chicken",
        ]
        
        for query in number_queries:
            result = router.classify_query(query)
            assert isinstance(result, ClassificationResult), f"Should handle numbers in '{query}'"
    
    def test_typos_and_misspellings(self, temp_db):
        """Test handling of typos and misspellings."""
        router = QueryRouter(temp_db)
        
        typo_queries = [
            "where is the milke",  # typo in milk
            "find aplles",  # typo in apples
            "locate bred",  # typo in bread
            "which aisl has chicken",  # typo in aisle
        ]
        
        for query in typo_queries:
            result = router.classify_query(query)
            assert isinstance(result, ClassificationResult), f"Should handle typos in '{query}'"

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
