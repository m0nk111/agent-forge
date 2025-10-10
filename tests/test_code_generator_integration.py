"""
Integration tests for CodeGenerator with real LLM.

Tests actual code generation with Ollama (qwen2.5-coder).
Requires Ollama running with qwen2.5-coder model.

Run with: pytest tests/test_code_generator_integration.py -v -s

Author: Agent Forge
Date: 2025-10-10
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

from engine.operations.code_generator import CodeGenerator, ModuleSpec


@pytest.fixture(scope="module")
def temp_project_dir():
    """Create temporary project directory for generated code."""
    temp_dir = Path(tempfile.mkdtemp(prefix="agent_forge_test_"))
    
    # Create subdirectories
    (temp_dir / "engine" / "operations").mkdir(parents=True, exist_ok=True)
    (temp_dir / "tests").mkdir(parents=True, exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def real_agent(temp_project_dir):
    """Create agent with real Ollama LLM access."""
    agent = Mock()
    agent.project_root = temp_project_dir
    
    # Real LLM query function
    def query_qwen(prompt, system_prompt=None, model="qwen2.5-coder:7b", stream=False, **kwargs):
        """Query Ollama API directly."""
        import requests
        import json
        
        url = "http://localhost:11434/api/generate"
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False  # Always non-streaming for simplicity
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            print(f"LLM query error: {e}")
            return ""
    
    agent.query_qwen = query_qwen
    return agent


@pytest.fixture
def code_generator(real_agent):
    """Create CodeGenerator with real LLM."""
    return CodeGenerator(real_agent)


class TestRealCodeGeneration:
    """Test code generation with real LLM."""
    
    @pytest.mark.integration
    def test_generate_simple_calculator(self, code_generator, temp_project_dir):
        """
        Test generating a simple calculator module.
        
        This is the canonical integration test for Phase 3B.
        Verifies end-to-end workflow:
        1. Generate implementation
        2. Generate tests
        3. Run static analysis
        4. Execute tests
        """
        print("\n🧪 Integration Test: Simple Calculator Module")
        print("=" * 70)
        
        # Define spec for simple calculator
        spec = ModuleSpec(
            module_path="engine/operations/calculator.py",
            module_name="calculator",
            test_path="tests/test_calculator.py",
            description="Simple calculator with add, subtract, multiply, divide functions",
            functions=["add", "subtract", "multiply", "divide"],
            dependencies=[]
        )
        
        # Generate module
        print("\n📝 Generating calculator module...")
        result = code_generator.generate_module(spec)
        
        # Verify success
        print(f"\n{'✅' if result.success else '❌'} Generation {'succeeded' if result.success else 'failed'}")
        print(f"   Retry count: {result.retry_count}")
        
        if result.success:
            print("\n📄 Generated Implementation:")
            print("-" * 70)
            print(result.module_content[:500] + "..." if len(result.module_content) > 500 else result.module_content)
            
            print("\n🧪 Generated Tests:")
            print("-" * 70)
            print(result.test_content[:500] + "..." if len(result.test_content) > 500 else result.test_content)
            
            if result.static_analysis:
                print("\n🔍 Static Analysis:")
                print(f"   Passed: {result.static_analysis['passed']}")
                if result.static_analysis['errors']:
                    print(f"   Errors: {result.static_analysis['errors']}")
                if result.static_analysis['warnings']:
                    print(f"   Warnings: {result.static_analysis['warnings']}")
            
            if result.test_results:
                print("\n✅ Test Results:")
                print(f"   Passed: {result.test_results['passed']}")
                print(f"   Tests run: {result.test_results['tests_run']}")
                if result.test_results['failures']:
                    print(f"   Failures: {result.test_results['failures']}")
        else:
            print("\n❌ Generation failed:")
            if result.errors:
                for error in result.errors:
                    print(f"   - {error}")
        
        # Assertions
        assert result.success, f"Code generation failed: {result.errors}"
        assert result.module_content, "No implementation generated"
        assert result.test_content, "No tests generated"
        
        # Verify key functions are present
        assert "def add(" in result.module_content, "add function not found"
        assert "def subtract(" in result.module_content, "subtract function not found"
        assert "def multiply(" in result.module_content, "multiply function not found"
        assert "def divide(" in result.module_content, "divide function not found"
        
        # Verify tests exist
        assert "def test_" in result.test_content, "No test functions found"
        assert "assert" in result.test_content, "No assertions in tests"
        
        # Verify static analysis passed
        assert result.static_analysis is not None, "No static analysis run"
        assert result.static_analysis['passed'], f"Static analysis failed: {result.static_analysis['errors']}"
        
        # Verify tests passed
        assert result.test_results is not None, "No tests run"
        assert result.test_results['passed'], f"Tests failed: {result.test_results['failures']}"
        assert result.test_results['tests_run'] > 0, "No tests executed"
        
        print("\n✅ Integration test passed!")
        print("=" * 70)
    
    @pytest.mark.integration
    def test_generate_string_helper(self, code_generator, temp_project_dir):
        """Test generating a string helper utility module."""
        print("\n🧪 Integration Test: String Helper Module")
        print("=" * 70)
        
        spec = ModuleSpec(
            module_path="engine/operations/string_helper.py",
            module_name="string_helper",
            test_path="tests/test_string_helper.py",
            description="String utilities: capitalize_words, reverse_string, count_vowels",
            functions=["capitalize_words", "reverse_string", "count_vowels"],
            dependencies=[]
        )
        
        print("\n📝 Generating string helper module...")
        result = code_generator.generate_module(spec)
        
        print(f"\n{'✅' if result.success else '❌'} Generation {'succeeded' if result.success else 'failed'}")
        
        if not result.success and result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"   - {error}")
        
        # Basic assertions
        assert result.success, f"Code generation failed: {result.errors}"
        assert "def capitalize_words(" in result.module_content
        assert "def reverse_string(" in result.module_content
        assert "def count_vowels(" in result.module_content
        
        print("✅ String helper test passed!")
    
    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires bandit/flake8 installed - manual verification only")
    def test_verify_static_analysis_tools(self, code_generator, temp_project_dir):
        """Verify bandit and flake8 are available."""
        import subprocess
        
        # Check bandit
        try:
            result = subprocess.run(['bandit', '--version'], capture_output=True, timeout=5)
            print(f"✅ bandit available: {result.stdout.decode().strip()}")
        except FileNotFoundError:
            print("❌ bandit not installed: pip install bandit")
        
        # Check flake8
        try:
            result = subprocess.run(['flake8', '--version'], capture_output=True, timeout=5)
            print(f"✅ flake8 available: {result.stdout.decode().strip()}")
        except FileNotFoundError:
            print("❌ flake8 not installed: pip install flake8")


class TestModuleSpecInferenceIntegration:
    """Test spec inference with realistic issue examples."""
    
    def test_infer_from_realistic_issue(self, code_generator):
        """Test spec inference from a realistic GitHub issue."""
        issue_title = "Implement email validator module"
        issue_body = """
We need a utility to validate email addresses.

Requirements:
- Create `engine/validation/email_validator.py`
- Implement `validate_email(email: str) -> bool` function
- Check for @ symbol, domain, and valid characters
- Add comprehensive test coverage

Dependencies:
- Use regex for validation
"""
        labels = ["feature", "code", "enhancement"]
        
        spec = code_generator.infer_module_spec(issue_title, issue_body, labels)
        
        assert spec is not None
        assert "email_validator" in spec.module_path
        assert "validate" in spec.functions or "validate_email" in spec.functions
        print(f"✅ Inferred spec: {spec.module_path}")


if __name__ == "__main__":
    # Run integration tests with output
    pytest.main([__file__, "-v", "-s", "-m", "integration"])
