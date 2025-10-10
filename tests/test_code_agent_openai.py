#!/usr/bin/env python3
"""
Test Code Agent with OpenAI GPT-4 provider.

Tests:
1. Initialize agent with OpenAI
2. Generate calculator module using GPT-4
3. Verify code quality
4. Compare with Ollama fallback

Usage:
    python3 tests/test_code_agent_openai.py

Author: Agent Forge
Date: 2025-10-10
"""

import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.runners.code_agent import CodeAgent


def test_openai_initialization():
    """Test 1: Initialize CodeAgent with OpenAI"""
    print("\n" + "="*70)
    print("🤖 TEST 1: Initialize CodeAgent with OpenAI")
    print("="*70)
    
    try:
        # Create temp project directory
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = CodeAgent(
                project_root=tmpdir,
                llm_provider="openai",  # Force OpenAI
                enable_monitoring=False
            )
            
            print(f"✅ Agent initialized")
            print(f"   Provider: {agent.llm_provider_name}")
            print(f"   Model: {agent.model}")
            
            if agent.llm_provider_name == "openai":
                print(f"   ✅ OpenAI provider active")
                return agent
            else:
                print(f"   ⚠️  Fell back to: {agent.llm_provider_name}")
                return None
                
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_simple_query(agent: CodeAgent):
    """Test 2: Simple LLM query"""
    print("\n" + "="*70)
    print("💬 TEST 2: Simple LLM Query")
    print("="*70)
    
    try:
        response = agent.query_llm(
            prompt="Write a Python function that calculates factorial. Just the code, one line if possible.",
            system_prompt="You are a Python expert. Be concise."
        )
        
        print(f"✅ Query successful")
        print(f"📏 Response length: {len(response)} chars")
        print(f"\n💡 Response:")
        print("─"*70)
        print(response[:300] + ("..." if len(response) > 300 else ""))
        print("─"*70)
        
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_code_generation(agent: CodeAgent):
    """Test 3: Full calculator module generation"""
    print("\n" + "="*70)
    print("🔧 TEST 3: Calculator Module Generation with GPT-4")
    print("="*70)
    
    try:
        from engine.operations.code_generator import CodeGenerator, ModuleSpec
        
        generator = CodeGenerator(agent)
        
        # Create spec for calculator
        spec = ModuleSpec(
            module_path="engine/utils/calculator.py",
            module_name="calculator",
            test_path="tests/test_calculator.py",
            description="Calculator module with add, subtract, multiply, divide functions",
            functions=["add", "subtract", "multiply", "divide"],
            dependencies=[]
        )
        
        print(f"📋 Generating: {spec.module_path}")
        print(f"   Functions: {', '.join(spec.functions)}")
        
        # Generate module
        result = generator.generate_module(spec)
        
        if result.success:
            print(f"✅ Generation successful!")
            print(f"   Retries: {result.retry_count}")
            
            if result.module_content:
                print(f"   Implementation: {len(result.module_content)} chars")
            if result.test_content:
                print(f"   Tests: {len(result.test_content)} chars")
            
            # Show snippet
            if result.module_content:
                print(f"\n💡 Implementation snippet (first 400 chars):")
                print("─"*70)
                print(result.module_content[:400] + "...")
                print("─"*70)
            
            return True
        else:
            print(f"❌ Generation failed")
            print(f"   Retries: {result.retry_count}")
            print(f"   Errors: {result.errors}")
            return False
            
    except Exception as e:
        print(f"❌ Code generation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_to_ollama():
    """Test 4: Fallback to Ollama when OpenAI not available"""
    print("\n" + "="*70)
    print("🔄 TEST 4: Fallback to Ollama")
    print("="*70)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Try with invalid provider
            agent = CodeAgent(
                project_root=tmpdir,
                llm_provider="invalid_provider",
                enable_monitoring=False
            )
            
            if agent.llm_provider_name == "local":
                print(f"✅ Correctly fell back to Ollama")
                return True
            else:
                print(f"❌ Unexpected provider: {agent.llm_provider_name}")
                return False
                
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False


def main():
    """Run all CodeAgent+OpenAI tests"""
    print("\n🤖 CodeAgent + OpenAI Integration Tests")
    print("="*70)
    
    results = {}
    
    # Test 1: Initialization
    agent = test_openai_initialization()
    results['init'] = agent is not None
    
    if not agent:
        print("\n❌ Cannot proceed without OpenAI agent")
        print("   Check: keys.json has OPENAI_API_KEY")
        return False
    
    # Test 2: Simple query
    results['query'] = test_simple_query(agent)
    
    # Test 3: Code generation
    results['codegen'] = test_code_generation(agent)
    
    # Test 4: Fallback
    results['fallback'] = test_fallback_to_ollama()
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
        print("\n🎉 CodeAgent can now use OpenAI GPT-4 for:")
        print("   - Code generation")
        print("   - Test generation")
        print("   - Issue resolution")
        print("   - Autonomous development")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   Review errors above")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
