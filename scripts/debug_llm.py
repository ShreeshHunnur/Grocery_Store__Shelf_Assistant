#!/usr/bin/env python3
"""
Debug script to test LLM service step by step.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.llm_service import LLMService

def debug_llm_service():
    """Debug LLM service step by step."""
    print("Debugging LLM Service...")
    
    try:
        # Create service
        print("1. Creating LLM service...")
        service = LLMService()
        print(f"   Model: {service.model_name}")
        print(f"   Base URL: {service.base_url}")
        
        # Test prompt library
        print("\n2. Testing prompt library...")
        library = service.prompt_library
        print(f"   Templates available: {list(library.templates.keys())}")
        
        # Test template selection
        print("\n3. Testing template selection...")
        template = library.get_prompt_template("what are the ingredients in milk")
        print(f"   Template length: {len(template)}")
        print(f"   Template preview: {template[:100]}...")
        
        # Test prompt building
        print("\n4. Testing prompt building...")
        context = service._build_context("milk", {"brand": "Organic Valley"})
        print(f"   Context: {context}")
        
        prompt = service._build_prompt("milk", "what are the ingredients in milk", template, context)
        print(f"   Prompt length: {len(prompt)}")
        print(f"   Prompt preview: {prompt[:200]}...")
        
        # Test LLM call
        print("\n5. Testing LLM call...")
        response = service._call_llm(prompt)
        print(f"   Response length: {len(response)}")
        print(f"   Response preview: {response[:200]}...")
        
        # Test response parsing
        print("\n6. Testing response parsing...")
        parsed = service._parse_response(response)
        print(f"   Parsed response: {parsed}")
        
        # Test full generation
        print("\n7. Testing full generation...")
        result = service.generate_info_answer("milk", "what are the ingredients in milk")
        print(f"   Final result: {result}")
        
        print("\n+ All steps completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n- Error at step: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_llm_service()
    sys.exit(0 if success else 1)
