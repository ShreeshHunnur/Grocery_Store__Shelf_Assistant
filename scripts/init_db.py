#!/usr/bin/env python3
"""
Initialize the Retail Shelf Assistant database.
Creates the database schema and populates it with sample data.
"""
import os
import sys
import time
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.seed_data import ProductDataGenerator
from config.settings import DATABASE_CONFIG

def create_database():
    """Create and populate the database."""
    print("Initializing Retail Shelf Assistant Database...")
    print("=" * 60)
    
    # Ensure data directory exists
    db_path = DATABASE_CONFIG["path"]
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing database if it exists
    if db_path.exists():
        print(f"Removing existing database: {db_path}")
        db_path.unlink()
    
    # Record start time
    start_time = time.time()
    
    try:
        # Generate database with 2000 products
        print(f"Generating database with 2000 products...")
        generator = ProductDataGenerator(seed=42)
        generator.generate_database(str(db_path), num_products=2000)
        
        # Calculate generation time
        generation_time = time.time() - start_time
        
        print(f"\n+ Database generation completed in {generation_time:.2f} seconds")
        
        # Verify database contents
        verify_database(db_path)
        
        print(f"\n+ Database ready at: {db_path}")
        print(f"+ Generation time: {generation_time:.2f} seconds")
        
        if generation_time < 10.0:
            print("+ Meets performance requirement (< 10 seconds)")
        else:
            print("Warning: Generation time exceeds 10 seconds")
        
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

def verify_database(db_path: Path):
    """Verify database contents and structure."""
    print("\nVerifying database contents...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check table counts
        tables = [
            'products', 'categories', 'brands', 'inventory_locations',
            'product_synonyms', 'product_keywords', 'product_popularity'
        ]
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} records")
        
        # Check categories
        cursor.execute("SELECT name FROM categories ORDER BY name")
        categories = [row[0] for row in cursor.fetchall()]
        print(f"\n  Categories ({len(categories)}): {', '.join(categories[:10])}{'...' if len(categories) > 10 else ''}")
        
        # Check brands
        cursor.execute("SELECT name FROM brands ORDER BY name")
        brands = [row[0] for row in cursor.fetchall()]
        print(f"  Brands ({len(brands)}): {', '.join(brands[:10])}{'...' if len(brands) > 10 else ''}")
        
        # Check sample products
        cursor.execute("""
            SELECT p.name, b.name as brand, c.name as category, il.aisle, il.bay, il.shelf
            FROM products p
            JOIN brands b ON p.brand_id = b.id
            JOIN categories c ON p.category_id = c.id
            LEFT JOIN inventory_locations il ON p.id = il.product_id
            LIMIT 5
        """)
        
        print(f"\n  Sample products:")
        for row in cursor.fetchall():
            print(f"    {row[0]} ({row[1]}) - {row[2]} - Aisle {row[3]}, Bay {row[4]}, {row[5]}")
        
        # Check indices
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indices = [row[0] for row in cursor.fetchall()]
        print(f"\n  Database indices: {len(indices)} created")
        
        # Check views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        print(f"  Database views: {len(views)} created")
        
    finally:
        conn.close()

def test_database_queries(db_path: Path):
    """Test database query functions."""
    print("\nTesting database queries...")
    
    try:
        from src.services.db_queries import DatabaseService
        
        service = DatabaseService(str(db_path))
        
        # Test queries
        test_queries = [
            "apple",
            "milk",
            "chicken",
            "coca cola",
            "organic",
            "frozen",
            "gluten free"
        ]
        
        for query in test_queries:
            print(f"\n  Testing query: '{query}'")
            matches = service.find_product_locations(query, limit=3)
            
            if matches:
                print(f"    Found {len(matches)} matches:")
                for match in matches:
                    print(f"      - {match.product_name} ({match.brand}) - Aisle {match.aisle}, Bay {match.bay}, {match.shelf} (confidence: {match.confidence:.2f})")
            else:
                print(f"    No matches found")
        
        # Test database stats
        stats = service.get_database_stats()
        print(f"\n  Database statistics:")
        for key, value in stats.items():
            print(f"    {key}: {value:,}")
        
    except Exception as e:
        print(f"  Error testing queries: {e}")

if __name__ == "__main__":
    create_database()
    
    # Test queries if database was created successfully
    db_path = DATABASE_CONFIG["path"]
    if db_path.exists():
        test_database_queries(db_path)
    
    print(f"\nDatabase initialization complete!")
