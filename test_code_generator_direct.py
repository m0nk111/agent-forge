#!/usr/bin/env python3
"""
Direct test of Code Generator with Issue #84 requirements
Bypasses issue_handler authentication issues
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Enable debug mode
os.environ['DEBUG'] = '1'

sys.path.insert(0, '/home/flip/agent-forge')

from engine.operations.code_generator import CodeGenerator, ModuleSpec

def create_mock_agent():
    """Create mock agent with actual Ollama LLM"""
    agent = Mock()
    agent.project_root = Path('/home/flip/agent-forge')
    
    # Mock query_qwen to use actual Ollama
    def mock_query_qwen(prompt, system_prompt="", model=None, stream=False, **kwargs):
        import requests
        url = 'http://localhost:11434/api/generate'
        payload = {
            'model': model or 'qwen2.5-coder:7b',
            'prompt': prompt,
            'system': system_prompt,
            'stream': False
        }
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            print(f"⚠️ LLM query failed: {e}")
            return f"Error: {e}"
    
    agent.query_qwen = mock_query_qwen
    return agent

def test_code_generator_issue84():
    """Test code generator with Issue #84 requirements"""
    
    print("=" * 80)
    print("Phase 3B Direct Code Generator Test: Issue #84")
    print("=" * 80)
    
    # Create mock agent and generator
    agent = create_mock_agent()
    generator = CodeGenerator(agent)
    
    # Define module spec from Issue #84
    spec = ModuleSpec(
        module_path="engine/operations/string_utils.py",
        module_name="string_utils",
        test_path="tests/test_string_utils.py",
        description="""Create string manipulation utilities with these functions:
- capitalize_words(text: str) -> str: Capitalize first letter of each word
- reverse_string(text: str) -> str: Reverse the input string  
- count_vowels(text: str) -> int: Count vowels (a, e, i, o, u) in text

Requirements:
- Type hints for all functions
- Docstrings for all functions
- Comprehensive pytest test suite
""",
        functions=[
            "capitalize_words",
            "reverse_string",
            "count_vowels"
        ],
        dependencies=[]
    )
    
    print(f"\n🔍 Module Spec:")
    print(f"   Path: {spec.module_path}")
    print(f"   Test: {spec.test_path}")
    print(f"   Functions: {', '.join(spec.functions)}")
    
    print(f"\n🔍 Step 1: Generate implementation...")
    result = generator.generate_module(spec)
    
    print(f"\n📊 Generation Result:")
    print(f"   Success: {result.success}")
    print(f"   Retries: {result.retry_count}")
    print(f"   Errors: {len(result.errors or [])}")
    
    if result.success:
        print(f"\n✅ Implementation Generated:")
        if result.module_content:
            print(f"   Lines: {len(result.module_content.splitlines())}")
            print(f"   Preview (first 20 lines):")
            for i, line in enumerate(result.module_content.splitlines()[:20], 1):
                print(f"      {i:3d} | {line}")
        
        print(f"\n✅ Tests Generated:")
        if result.test_content:
            print(f"   Lines: {len(result.test_content.splitlines())}")
            print(f"   Preview (first 20 lines):")
            for i, line in enumerate(result.test_content.splitlines()[:20], 1):
                print(f"      {i:3d} | {line}")
        
        print(f"\n📊 Static Analysis:")
        if result.static_analysis:
            print(f"   Passed: {result.static_analysis.get('passed')}")
            print(f"   Errors: {result.static_analysis.get('errors', [])}")
            print(f"   Warnings: {result.static_analysis.get('warnings', [])}")
        
        print(f"\n📊 Test Execution:")
        if result.test_results:
            print(f"   Passed: {result.test_results.get('passed')}")
            print(f"   Tests Run: {result.test_results.get('tests_run')}")
            print(f"   Failures: {result.test_results.get('failures', [])}")
    else:
        print(f"\n❌ Generation Failed:")
        for error in (result.errors or []):
            print(f"   - {error}")
    
    print("=" * 80)
    return result.success

if __name__ == '__main__':
    try:
        success = test_code_generator_issue84()
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Code generator test completed")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
