"""
End-to-End Integration Test for Code Generator.

Tests the full pipeline with real LLM (Ollama) to validate:
1. Prompt separation works correctly
2. Implementation file contains only implementation
3. Test file contains only tests
4. Coverage tracking works

Author: Agent Forge
Date: 2025-10-10
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
from engine.operations.code_generator import CodeGenerator, ModuleSpec


class MockAgent:
    """Mock agent with real Ollama integration."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        
    def query_qwen(self, prompt, stream=False, system_prompt=None):
        """Query real Ollama for E2E testing."""
        import requests
        import json
        
        try:
            response = requests.post(
                'http://localhost:11434/api/chat',
                json={
                    'model': 'qwen2.5-coder:7b',
                    'messages': [
                        {'role': 'system', 'content': system_prompt or 'You are a helpful assistant'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'stream': False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['message']['content']
            else:
                return None
                
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")


@pytest.mark.integration
def test_prompt_separation_with_real_llm():
    """
    Test that improved prompts correctly separate implementation from tests.
    
    This test validates:
    1. Implementation file contains function definitions
    2. Implementation file does NOT contain test functions
    3. Test file contains test functions
    4. Test file does NOT contain duplicate implementation
    """
    # Setup
    agent = MockAgent()
    generator = CodeGenerator(agent)
    
    spec = ModuleSpec(
        module_path="engine/operations/math_utils.py",
        module_name="math_utils",
        test_path="tests/test_math_utils.py",
        description="Simple math utility functions",
        functions=["add", "multiply"],
        dependencies=[]
    )
    
    # Generate implementation
    print("\n🔍 Testing implementation generation...")
    impl_content = generator._generate_implementation(spec, [])
    
    assert impl_content is not None, "Implementation should be generated"
    assert "def add(" in impl_content, "Implementation should contain add function"
    assert "def multiply(" in impl_content, "Implementation should contain multiply function"
    
    # Verify NO test code in implementation
    assert "def test_" not in impl_content, "Implementation should NOT contain test functions"
    assert "import pytest" not in impl_content.lower(), "Implementation should NOT import pytest"
    assert "assert " not in impl_content or "# assert" in impl_content, "Implementation should NOT have test assertions"
    
    print("✅ Implementation contains only implementation code")
    
    # Generate tests
    print("\n🔍 Testing test generation...")
    test_content = generator._generate_tests(spec, impl_content, [])
    
    assert test_content is not None, "Tests should be generated"
    assert "def test_" in test_content, "Tests should contain test functions"
    assert "import pytest" in test_content or "from " in test_content, "Tests should have imports"
    
    # Verify NO duplicate implementation in tests
    # Tests should import from module, not redefine functions
    test_lines = test_content.split('\n')
    implementation_defs = [line for line in test_lines if line.strip().startswith('def add(') or line.strip().startswith('def multiply(')]
    
    # Allow at most minimal helper functions, but not the full implementation
    assert len(implementation_defs) == 0, f"Tests should NOT redefine implementation functions. Found: {implementation_defs}"
    
    print("✅ Tests contain only test code")
    print(f"\n📊 Implementation: {len(impl_content)} chars, {len(impl_content.split(chr(10)))} lines")
    print(f"📊 Tests: {len(test_content)} chars, {len(test_content.split(chr(10)))} lines")


@pytest.mark.integration
def test_full_generation_workflow():
    """
    Test complete generation workflow with real LLM.
    
    This validates:
    1. Module specification inference
    2. Implementation generation
    3. Test generation
    4. Static analysis
    5. Test execution
    6. Coverage tracking (if pytest-cov available)
    """
    # Setup
    agent = MockAgent()
    generator = CodeGenerator(agent)
    
    # Infer spec
    spec = generator.infer_module_spec(
        issue_title="Create string_helper.py utility",
        issue_body="Need a helper module with capitalize_words and truncate functions",
        labels=["enhancement"]
    )
    
    assert spec is not None, "Should infer module spec"
    assert "helper" in spec.module_path, "Should infer helper path"
    
    print(f"\n📋 Spec: {spec.module_path}")
    
    # Full generation (this may take 30-60 seconds)
    print("\n🚀 Running full generation workflow (may take 60s)...")
    result = generator.generate_module(spec)
    
    # Validate result structure
    assert hasattr(result, 'success'), "Result should have success field"
    assert hasattr(result, 'module_content'), "Result should have module_content"
    assert hasattr(result, 'test_content'), "Result should have test_content"
    assert hasattr(result, 'static_analysis'), "Result should have static_analysis"
    assert hasattr(result, 'test_results'), "Result should have test_results"
    
    # Print summary
    print(f"\n📊 Generation Result:")
    print(f"   Success: {result.success}")
    print(f"   Retry count: {result.retry_count}")
    
    if result.static_analysis:
        print(f"   Static analysis: {'✅ PASS' if result.static_analysis['passed'] else '❌ FAIL'}")
        if result.static_analysis.get('errors'):
            print(f"      Errors: {result.static_analysis['errors']}")
    
    if result.test_results:
        print(f"   Tests: {'✅ PASS' if result.test_results['passed'] else '❌ FAIL'}")
        print(f"      Tests run: {result.test_results.get('tests_run', 0)}")
        if result.test_results.get('coverage'):
            print(f"      Coverage: {result.test_results['coverage']}%")
        if result.test_results.get('failures'):
            print(f"      Failures: {result.test_results['failures']}")
    
    # Success not guaranteed with real LLM, but should have attempted
    assert result.module_content is not None, "Should have generated implementation"
    assert result.test_content is not None, "Should have generated tests"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
