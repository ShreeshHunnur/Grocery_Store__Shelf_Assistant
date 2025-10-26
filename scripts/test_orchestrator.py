#!/usr/bin/env python3
"""
Test script to verify orchestrator functionality.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.orchestrator import BackendOrchestrator

def test_orchestrator():
    """Test orchestrator functionality."""
    print("Testing Backend Orchestrator...")
    
    # Create orchestrator
    orchestrator = BackendOrchestrator()
    print(f"Orchestrator created with DB path: {orchestrator.db_path}")
    
    # Test location query
    print("\nTesting location query: 'where is the milk'")
    result = orchestrator.process_text_query("where is the milk")
    print(f"Query type: {result.get('query_type')}")
    print(f"Normalized product: {result.get('normalized_product')}")
    print(f"Matches count: {len(result.get('matches', []))}")
    print(f"Disambiguation needed: {result.get('disambiguation_needed')}")
    
    if result.get('matches'):
        print("Top matches:")
        for i, match in enumerate(result.get('matches', [])[:3], 1):
            print(f"  {i}. {match.get('product_name')} - {match.get('brand')} - Aisle {match.get('aisle')}")
    
    # Test information query
    print("\nTesting information query: 'what are the ingredients in bread'")
    result = orchestrator.process_text_query("what are the ingredients in bread")
    print(f"Query type: {result.get('query_type')}")
    print(f"Normalized product: {result.get('normalized_product')}")
    print(f"Answer: {result.get('answer', 'No answer')[:100]}...")
    print(f"Confidence: {result.get('confidence', 0)}")
    
    # Test health status
    print("\nTesting health status...")
    health = orchestrator.get_health_status()
    print(f"Health status: {health}")

if __name__ == "__main__":
    test_orchestrator()
