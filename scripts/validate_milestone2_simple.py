#!/usr/bin/env python3
"""
Simple validation script for Milestone 2: Build and Seed SQLite Product Database
Tests all acceptance criteria and requirements.
"""
import time
import sqlite3
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.db_queries import DatabaseService
from config.settings import DATABASE_CONFIG

def test_database_build_time():
    """Test that database builds in under 10 seconds."""
    print("Testing database build time...")
    
    # Remove existing database
    db_path = DATABASE_CONFIG["path"]
    if db_path.exists():
        db_path.unlink()
    
    start_time = time.time()
    
    # Import and run the database generation
    from database.seed_data import ProductDataGenerator
    generator = ProductDataGenerator(seed=42)
    generator.generate_database(str(db_path), num_products=2000)
    
    build_time = time.time() - start_time
    
    print(f"  Database build time: {build_time:.2f} seconds")
    
    if build_time < 10.0:
        print("  PASSED: Database builds in under 10 seconds")
        return True
    else:
        print("  FAILED: Database build time exceeds 10 seconds")
        return False

def test_find_product_locations():
    """Test find_product_locations returns structured candidates with confidence scores."""
    print("\nTesting find_product_locations function...")
    
    db_path = DATABASE_CONFIG["path"]
    if not db_path.exists():
        print("  FAILED: Database does not exist")
        return False
    
    service = DatabaseService(str(db_path))
    
    # Test various queries
    test_queries = ["apple", "milk", "chicken", "coca cola", "organic", "frozen"]
    
    all_passed = True
    
    for query in test_queries:
        print(f"  Testing query: '{query}'")
        matches = service.find_product_locations(query, limit=5)
        
        if not matches:
            print(f"    Warning: No matches found for '{query}'")
            continue
        
        # Check structure
        for i, match in enumerate(matches):
            # Check required fields
            required_fields = ['product_id', 'product_name', 'brand', 'category', 'aisle', 'bay', 'shelf', 'confidence']
            missing_fields = [field for field in required_fields if not hasattr(match, field)]
            
            if missing_fields:
                print(f"    FAILED: Missing fields {missing_fields} in match {i}")
                all_passed = False
                continue
            
            # Check confidence score
            if not (0.0 <= match.confidence <= 1.0):
                print(f"    FAILED: Invalid confidence score {match.confidence} in match {i}")
                all_passed = False
                continue
        
        print(f"    Found {len(matches)} matches with valid structure")
    
    if all_passed:
        print("  PASSED: find_product_locations returns structured candidates with confidence scores")
    else:
        print("  FAILED: find_product_locations has structural issues")
    
    return all_passed

def test_categories_and_brands():
    """Test that at least 15 categories and 50+ brands are represented."""
    print("\nTesting categories and brands requirements...")
    
    db_path = DATABASE_CONFIG["path"]
    if not db_path.exists():
        print("  FAILED: Database does not exist")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Count categories
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        print(f"  Categories: {category_count}")
        
        # Count brands
        cursor.execute("SELECT COUNT(*) FROM brands")
        brand_count = cursor.fetchone()[0]
        print(f"  Brands: {brand_count}")
        
        category_ok = category_count >= 15
        brand_ok = brand_count >= 50
        
        if category_ok and brand_ok:
            print("  PASSED: Meets category and brand requirements")
            return True
        else:
            print(f"  FAILED: Category requirement ({category_count}/15), Brand requirement ({brand_count}/50)")
            return False
    
    finally:
        conn.close()

def test_database_schema():
    """Test that database schema is properly created."""
    print("\nTesting database schema...")
    
    db_path = DATABASE_CONFIG["path"]
    if not db_path.exists():
        print("  FAILED: Database does not exist")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check required tables
        required_tables = [
            'products', 'categories', 'brands', 'inventory_locations',
            'product_synonyms', 'product_keywords', 'product_popularity'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"  FAILED: Missing tables: {missing_tables}")
            return False
        
        print("  PASSED: Database schema is properly created")
        return True
    
    finally:
        conn.close()

def test_query_functions():
    """Test that all required query functions work."""
    print("\nTesting query functions...")
    
    db_path = DATABASE_CONFIG["path"]
    if not db_path.exists():
        print("  FAILED: Database does not exist")
        return False
    
    service = DatabaseService(str(db_path))
    
    # Test find_product_locations
    try:
        matches = service.find_product_locations("milk", limit=3)
        print("  find_product_locations works")
    except Exception as e:
        print(f"  FAILED: find_product_locations error: {e}")
        return False
    
    # Test find_candidates_by_synonym
    try:
        matches = service.find_candidates_by_synonym("coke", limit=3)
        print("  find_candidates_by_synonym works")
    except Exception as e:
        print(f"  FAILED: find_candidates_by_synonym error: {e}")
        return False
    
    # Test normalize_product_name
    try:
        normalized = service.normalize_product_name("Fresh Organic Milk")
        assert normalized == "fresh organic milk"
        print("  normalize_product_name works")
    except Exception as e:
        print(f"  FAILED: normalize_product_name error: {e}")
        return False
    
    print("  PASSED: All query functions work correctly")
    return True

def test_database_content():
    """Test that database has sufficient content."""
    print("\nTesting database content...")
    
    db_path = DATABASE_CONFIG["path"]
    if not db_path.exists():
        print("  FAILED: Database does not exist")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check product count
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        print(f"  Products: {product_count:,}")
        
        # Check that we have products with locations
        cursor.execute("""
            SELECT COUNT(*) FROM products p
            JOIN inventory_locations il ON p.id = il.product_id
        """)
        products_with_locations = cursor.fetchone()[0]
        print(f"  Products with locations: {products_with_locations:,}")
        
        if product_count >= 1000 and products_with_locations >= 1000:
            print("  PASSED: Database has sufficient content")
            return True
        else:
            print(f"  FAILED: Insufficient content (products: {product_count}, with locations: {products_with_locations})")
            return False
    
    finally:
        conn.close()

def main():
    """Run all validation tests."""
    print("Milestone 2 Validation: Build and Seed SQLite Product Database")
    print("=" * 70)
    
    tests = [
        ("Database Build Time", test_database_build_time),
        ("Find Product Locations", test_find_product_locations),
        ("Categories and Brands", test_categories_and_brands),
        ("Database Schema", test_database_schema),
        ("Query Functions", test_query_functions),
        ("Database Content", test_database_content)
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
        print("All acceptance criteria met! Milestone 2 is complete.")
        return True
    else:
        print("Some acceptance criteria not met. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
