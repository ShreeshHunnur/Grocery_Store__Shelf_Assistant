#!/usr/bin/env python3
"""
Comprehensive test to verify analytics system is working properly.
This script will test all API endpoints and check if analytics are being tracked.
"""
import requests
import json
import time
import sqlite3
from pathlib import Path

def check_server_status():
    """Check if the server is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_text_query():
    """Test text query tracking."""
    print("Testing text query analytics...")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/ask",
            json={"query": "Where can I find milk?", "session_id": "analytics_test_session"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("+ Text query succeeded")
            return True
        else:
            print(f"- Text query failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"- Text query error: {e}")
        return False

def test_analytics_api():
    """Test analytics API endpoints."""
    print("Testing analytics API endpoints...")
    
    endpoints = [
        "/api/v1/analytics/dashboard?days=30",
        "/api/v1/analytics/real-time",
        "/api/v1/analytics/health",
        "/api/v1/analytics/recent?limit=10"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"+ {endpoint}")
                success_count += 1
            else:
                print(f"- {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"- {endpoint} - Error: {e}")
    
    return success_count == len(endpoints)

def check_database_queries():
    """Check if queries are being stored in the database."""
    print("Checking database for analytics data...")
    
    try:
        # Connect to the database
        db_path = Path("d:/grocery_assistant_project/data/products.db")
        if not db_path.exists():
            print(f"- Database file not found at {db_path}")
            return False
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if analytics tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE '%analytics%'
            """)
            tables = cursor.fetchall()
            print(f"Analytics tables found: {[table[0] for table in tables]}")
            
            # Check for recent queries
            cursor.execute("""
                SELECT COUNT(*) FROM query_analytics 
                WHERE timestamp >= datetime('now', '-1 hour')
            """)
            recent_count = cursor.fetchone()[0]
            print(f"Recent queries (last hour): {recent_count}")
            
            # Get sample of recent queries
            cursor.execute("""
                SELECT query_text, query_type, input_method, success, timestamp 
                FROM query_analytics 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            recent_queries = cursor.fetchall()
            
            if recent_queries:
                print("Recent queries:")
                for query in recent_queries:
                    print(f"  - {query[0][:30]}... | Type: {query[1]} | Method: {query[2]} | Success: {query[3]} | Time: {query[4]}")
                return True
            else:
                print("- No queries found in database")
                return False
                
    except Exception as e:
        print(f"- Database check error: {e}")
        return False

def test_analytics_dashboard():
    """Test analytics dashboard accessibility."""
    print("Testing analytics dashboard...")
    try:
        response = requests.get("http://localhost:8000/analytics", timeout=5)
        if response.status_code == 200:
            print("+ Analytics dashboard accessible")
            return True
        else:
            print(f"- Analytics dashboard failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"- Analytics dashboard error: {e}")
        return False

def main():
    """Run all analytics tests."""
    print("=" * 60)
    print("ANALYTICS SYSTEM COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Check server status
    if not check_server_status():
        print("- Server is not running. Please start the server first.")
        return
    
    print("+ Server is running")
    print()
    
    # Run tests
    tests = [
        ("Text Query", test_text_query),
        ("Analytics API", test_analytics_api),
        ("Database Check", check_database_queries),
        ("Dashboard Access", test_analytics_dashboard)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
        print()
    
    # Summary
    print("=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "+ PASS" if result else "- FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All analytics tests passed! The system is working correctly.")
    else:
        print("Some tests failed. Check the analytics integration.")

if __name__ == "__main__":
    main()