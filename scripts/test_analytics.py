#!/usr/bin/env python3
"""
Test script to generate analytics data by making API calls.
"""
import requests
import json
import time
import random

# Test queries to generate analytics data
test_queries = [
    "Where can I find milk?",
    "Where are the bananas?", 
    "Where is bread located?",
    "Where can I find cheese?",
    "Where are the apples?",
    "Where is pasta?",
    "Where can I find yogurt?",
    "Where are the tomatoes?",
    "Where is coffee?",
    "Where can I find chicken?",
    "What is the nutritional value of bananas?",
    "How many calories are in an apple?",
    "What are the ingredients in bread?",
    "How do I store milk properly?",
    "What's the best way to cook chicken?"
]

def test_api_calls():
    """Make test API calls to generate analytics data."""
    base_url = "http://localhost:8000/api/v1"
    
    print("Starting analytics test...")
    
    for i, query in enumerate(test_queries):
        try:
            # Make API call
            response = requests.post(
                f"{base_url}/ask",
                json={"query": query, "session_id": f"test_session_{random.randint(1, 5)}"},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✓ Query {i+1}: {query}")
                result = response.json()
                if "matches" in result:
                    print(f"  Found {len(result['matches'])} matches")
                elif "answer" in result:
                    print(f"  Info response: {result['answer'][:50]}...")
            else:
                print(f"✗ Query {i+1} failed: {response.status_code}")
            
            # Small delay between requests
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Error with query {i+1}: {e}")
    
    print(f"\nCompleted {len(test_queries)} test queries!")
    print("Analytics data should now be available at: http://localhost:8000/analytics")

if __name__ == "__main__":
    test_api_calls()