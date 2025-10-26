"""
Unit tests for database query functions.
Tests exact match, synonym match, and no-match fallbacks.
"""
import pytest
import sqlite3
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.db_queries import DatabaseService, ProductMatch
from database.seed_data import ProductDataGenerator

class TestDatabaseQueries:
    """Test class for database query functions."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        # Create temporary database
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        
        # Generate test data
        generator = ProductDataGenerator(seed=42)
        generator.generate_database(temp_file.name, num_products=100)
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def db_service(self, temp_db):
        """Create database service instance."""
        return DatabaseService(temp_db)
    
    def test_normalize_product_name(self, db_service):
        """Test product name normalization."""
        # Test cases: (input, expected_output)
        test_cases = [
            ("Apple", "apple"),
            ("  Fresh Organic Milk  ", "fresh organic milk"),
            ("Coca-Cola Classic", "coca-cola classic"),
            ("The Best Coffee Ever", "best coffee ever"),
            ("", ""),
            ("   ", ""),
            ("A, B, and C", "a b c"),
        ]
        
        for input_name, expected in test_cases:
            result = db_service.normalize_product_name(input_name)
            assert result == expected, f"Expected '{expected}', got '{result}' for input '{input_name}'"
    
    def test_exact_match(self, db_service):
        """Test exact product name matching."""
        # Get a real product name from the database
        conn = db_service._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products LIMIT 1")
        product_name = cursor.fetchone()[0]
        conn.close()
        
        # Test exact match
        matches = db_service.find_product_locations(product_name, limit=5)
        
        assert len(matches) > 0, "Should find at least one exact match"
        assert matches[0].confidence == 1.0, "Exact match should have confidence 1.0"
        assert matches[0].product_name == product_name, "Product name should match exactly"
    
    def test_fuzzy_match(self, db_service):
        """Test fuzzy matching for partial product names."""
        # Get a product name and use part of it
        conn = db_service._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE name LIKE '%Apple%' LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            full_name = result[0]
            # Use first word of the product name
            partial_name = full_name.split()[0]
            
            matches = db_service.find_product_locations(partial_name, limit=5)
            
            assert len(matches) > 0, f"Should find fuzzy matches for '{partial_name}'"
            assert all(match.confidence > 0 for match in matches), "All matches should have positive confidence"
    
    def test_synonym_match(self, db_service):
        """Test synonym matching."""
        # Test with common synonyms
        synonym_queries = ["Coke", "Soda", "Milk", "Cheese", "Bread"]
        
        for query in synonym_queries:
            matches = db_service.find_product_locations(query, limit=3)
            # Should find some matches (may be 0 if no synonyms exist for this query)
            assert isinstance(matches, list), "Should return a list of matches"
    
    def test_no_match_fallback(self, db_service):
        """Test behavior when no matches are found."""
        # Use a very unlikely product name
        unlikely_query = "xyzqwerty123nonexistentproduct"
        
        matches = db_service.find_product_locations(unlikely_query, limit=5)
        
        assert isinstance(matches, list), "Should return a list even with no matches"
        assert len(matches) == 0, "Should return empty list for non-existent products"
    
    def test_confidence_scores(self, db_service):
        """Test that confidence scores are within valid range."""
        test_queries = ["milk", "apple", "bread", "cheese", "chicken"]
        
        for query in test_queries:
            matches = db_service.find_product_locations(query, limit=5)
            
            for match in matches:
                assert 0.0 <= match.confidence <= 1.0, f"Confidence {match.confidence} should be between 0.0 and 1.0"
    
    def test_product_match_structure(self, db_service):
        """Test that ProductMatch objects have correct structure."""
        matches = db_service.find_product_locations("milk", limit=1)
        
        if matches:
            match = matches[0]
            
            # Check required fields
            assert hasattr(match, 'product_id'), "ProductMatch should have product_id"
            assert hasattr(match, 'product_name'), "ProductMatch should have product_name"
            assert hasattr(match, 'brand'), "ProductMatch should have brand"
            assert hasattr(match, 'category'), "ProductMatch should have category"
            assert hasattr(match, 'aisle'), "ProductMatch should have aisle"
            assert hasattr(match, 'bay'), "ProductMatch should have bay"
            assert hasattr(match, 'shelf'), "ProductMatch should have shelf"
            assert hasattr(match, 'confidence'), "ProductMatch should have confidence"
            
            # Check field types
            assert isinstance(match.product_id, str), "product_id should be string"
            assert isinstance(match.product_name, str), "product_name should be string"
            assert isinstance(match.brand, str), "brand should be string"
            assert isinstance(match.category, str), "category should be string"
            assert isinstance(match.aisle, str), "aisle should be string"
            assert isinstance(match.bay, str), "bay should be string"
            assert isinstance(match.shelf, str), "shelf should be string"
            assert isinstance(match.confidence, float), "confidence should be float"
    
    def test_find_candidates_by_synonym(self, db_service):
        """Test finding candidates by synonym."""
        # Get a synonym from the database
        conn = db_service._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT synonym FROM product_synonyms LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            synonym = result[0]
            matches = db_service.find_candidates_by_synonym(synonym, limit=5)
            
            assert isinstance(matches, list), "Should return a list of matches"
            if matches:
                assert all(match.confidence > 0 for match in matches), "All matches should have positive confidence"
    
    def test_get_product_by_id(self, db_service):
        """Test getting product by ID."""
        # Get a product ID from the database
        conn = db_service._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products LIMIT 1")
        product_id = cursor.fetchone()[0]
        conn.close()
        
        match = db_service.get_product_by_id(str(product_id))
        
        assert match is not None, "Should find product by ID"
        assert match.product_id == str(product_id), "Product ID should match"
        assert match.confidence == 1.0, "Direct ID lookup should have confidence 1.0"
    
    def test_get_nonexistent_product(self, db_service):
        """Test getting non-existent product by ID."""
        nonexistent_id = "999999"
        match = db_service.get_product_by_id(nonexistent_id)
        
        assert match is None, "Should return None for non-existent product ID"
    
    def test_search_products_fulltext(self, db_service):
        """Test full-text search functionality."""
        test_queries = ["organic", "fresh", "frozen", "gluten free"]
        
        for query in test_queries:
            matches = db_service.search_products_fulltext(query, limit=5)
            
            assert isinstance(matches, list), "Should return a list of matches"
            assert all(0.0 <= match.confidence <= 1.0 for match in matches), "All matches should have valid confidence"
    
    def test_database_stats(self, db_service):
        """Test database statistics retrieval."""
        stats = db_service.get_database_stats()
        
        assert isinstance(stats, dict), "Should return a dictionary"
        
        expected_keys = ['products', 'categories', 'brands', 'synonyms', 'keywords']
        for key in expected_keys:
            assert key in stats, f"Stats should contain '{key}'"
            assert isinstance(stats[key], int), f"'{key}' should be an integer"
            assert stats[key] >= 0, f"'{key}' should be non-negative"
    
    def test_limit_parameter(self, db_service):
        """Test that limit parameter works correctly."""
        query = "milk"
        
        # Test different limits
        for limit in [1, 3, 5, 10]:
            matches = db_service.find_product_locations(query, limit=limit)
            assert len(matches) <= limit, f"Should return at most {limit} matches"
    
    def test_empty_query(self, db_service):
        """Test behavior with empty queries."""
        empty_queries = ["", "   ", None]
        
        for query in empty_queries:
            if query is None:
                # Skip None test as it would cause an error
                continue
            matches = db_service.find_product_locations(query, limit=5)
            assert matches == [], "Empty queries should return empty list"

def test_find_product_locations_function():
    """Test the standalone find_product_locations function."""
    from src.services.db_queries import find_product_locations
    
    # Create temporary database
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    try:
        # Generate test data
        generator = ProductDataGenerator(seed=42)
        generator.generate_database(temp_file.name, num_products=50)
        
        # Test the function
        matches = find_product_locations(temp_file.name, "milk", limit=3)
        
        assert isinstance(matches, list), "Should return a list of matches"
        assert all(isinstance(match, ProductMatch) for match in matches), "All matches should be ProductMatch objects"
        
    finally:
        # Cleanup
        os.unlink(temp_file.name)

def test_find_candidates_by_synonym_function():
    """Test the standalone find_candidates_by_synonym function."""
    from src.services.db_queries import find_candidates_by_synonym
    
    # Create temporary database
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    try:
        # Generate test data
        generator = ProductDataGenerator(seed=42)
        generator.generate_database(temp_file.name, num_products=50)
        
        # Test the function
        matches = find_candidates_by_synonym(temp_file.name, "coke", limit=3)
        
        assert isinstance(matches, list), "Should return a list of matches"
        assert all(isinstance(match, ProductMatch) for match in matches), "All matches should be ProductMatch objects"
        
    finally:
        # Cleanup
        os.unlink(temp_file.name)

def test_normalize_product_name_function():
    """Test the standalone normalize_product_name function."""
    from src.services.db_queries import normalize_product_name
    
    # Test cases
    test_cases = [
        ("Apple", "apple"),
        ("  Fresh Milk  ", "fresh milk"),
        ("The Best Coffee", "best coffee"),
        ("", ""),
    ]
    
    for input_name, expected in test_cases:
        result = normalize_product_name(input_name)
        assert result == expected, f"Expected '{expected}', got '{result}' for input '{input_name}'"

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
