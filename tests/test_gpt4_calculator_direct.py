#!/usr/bin/env python3
"""
Direct end-to-end test: GPT-4 generates calculator, we execute it.
"""

import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.runners.code_agent import CodeAgent
from engine.operations.code_generator import CodeGenerator, ModuleSpec

# Create temp directory
tmpdir = Path("/tmp/calculator_test_gpt4")
tmpdir.mkdir(parents=True, exist_ok=True)

# Create agent with OpenAI
agent = CodeAgent(
    project_root=str(tmpdir),
    llm_provider="openai",
    model="gpt-4",
    enable_monitoring=False
)

# Create spec
spec = ModuleSpec(
    module_path="calculator.py",
    module_name="calculator", 
    test_path="test_calculator.py",
    description="Calculator with add, subtract, multiply, divide functions. Handle division by zero.",
    functions=["add", "subtract", "multiply", "divide"],
    dependencies=[]
)

print("🚀 Generating calculator module with GPT-4...")
generator = CodeGenerator(agent)
result = generator.generate_module(spec)

if result.success:
    print(f"✅ SUCCESS!")
    if result.module_content:
        print(f"   Module: {len(result.module_content)} chars")
    if result.test_content:
        print(f"   Tests: {len(result.test_content)} chars")
    if result.module_content:
        print(f"\n📝 Implementation snippet:")
        print(result.module_content[:400])
else:
    print(f"❌ FAILED after {result.retry_count} attempts")
    print(f"   Errors: {result.errors}")
    if result.test_results:
        print(f"   Test failures: {result.test_results.get('failures')}")
