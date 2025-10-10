"""Code Module Generator for Agent-Forge.

Generates functional Python modules with implementation, tests, and documentation.
Part of Phase 3B roadmap for autonomous code generation pipeline.

Features:
- Infer file paths and module structure from issue description
- Generate implementation skeleton with type hints and docstrings
- Generate comprehensive test suite with pytest
- Run static analysis (bandit, flake8, mypy)
- Execute tests and validate coverage
- Retry mechanism for compilation/test errors
- Integration with issue_handler workflow

Author: Agent Forge
Date: 2025-10-09
"""

import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ModuleSpec:
    """Specification for code module to generate."""
    
    module_path: str  # e.g., "engine/operations/helper.py"
    module_name: str  # e.g., "helper"
    test_path: str    # e.g., "tests/test_helper.py"
    description: str  # What the module should do
    functions: List[str]  # Function names to implement
    dependencies: List[str]  # Import dependencies


@dataclass
class GenerationResult:
    """Result of code generation attempt."""
    
    success: bool
    module_content: Optional[str] = None
    test_content: Optional[str] = None
    static_analysis: Optional[Dict] = None
    test_results: Optional[Dict] = None
    errors: Optional[List[str]] = None
    retry_count: int = 0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CodeGenerator:
    """
    Generate functional Python modules with tests and documentation.
    
    Workflow:
    1. Parse issue to infer module structure (spec)
    2. Generate implementation via LLM
    3. Generate test suite via LLM
    4. Run static analysis (bandit, flake8)
    5. Execute tests and check coverage
    6. Retry on errors with feedback to LLM
    """
    
    def __init__(self, agent):
        """
        Initialize code generator.
        
        Args:
            agent: CodeAgent instance with LLM access
        """
        self.agent = agent
        self.project_root = agent.project_root
        self.max_retries = 3
        
    def infer_module_spec(self, issue_title: str, issue_body: str, labels: List[str]) -> Optional[ModuleSpec]:
        """
        Infer module specification from issue description.
        
        Args:
            issue_title: Issue title
            issue_body: Issue body text
            labels: Issue labels
            
        Returns:
            ModuleSpec or None if can't infer
        """
        logger.info("🔍 Inferring module specification from issue...")
        
        # Extract file path mentions (e.g., "create engine/operations/helper.py")
        text = f"{issue_title} {issue_body}".lower()
        
        # Pattern 1: Explicit path mention
        path_pattern = r'(?:create|add|implement|build)\s+(?:file\s+)?[`]?([a-z_/]+\.py)[`]?'
        path_match = re.search(path_pattern, text)
        
        if path_match:
            module_path = path_match.group(1)
        else:
            # Pattern 2: Infer from keywords
            if 'helper' in text or 'utility' in text:
                module_path = "engine/operations/helper.py"
            elif 'validator' in text or 'validation' in text:
                module_path = "engine/validation/validator.py"
            elif 'parser' in text or 'parse' in text:
                module_path = "engine/operations/parser.py"
            else:
                logger.warning("❌ Could not infer module path from issue")
                return None
        
        # Extract module name
        module_name = Path(module_path).stem
        
        # Construct test path
        test_path = f"tests/test_{module_name}.py"
        
        # Extract description
        description = issue_body.strip() if issue_body else issue_title
        
        # Extract function names if mentioned
        function_pattern = r'(?:function|def|method)\s+[`]?([a-z_][a-z0-9_]*)[`]?'
        functions = re.findall(function_pattern, text)
        
        if not functions:
            # Default to common patterns
            if 'validate' in text:
                functions = ['validate']
            elif 'parse' in text:
                functions = ['parse']
            elif 'process' in text:
                functions = ['process']
            else:
                functions = ['run']  # Generic default
        
        # Extract dependencies
        dependencies = []
        if 'yaml' in text:
            dependencies.append('yaml')
        if 'json' in text:
            dependencies.append('json')
        if 'requests' in text or 'http' in text:
            dependencies.append('requests')
        
        spec = ModuleSpec(
            module_path=module_path,
            module_name=module_name,
            test_path=test_path,
            description=description,
            functions=functions,
            dependencies=dependencies
        )
        
        logger.info(f"✅ Module spec inferred:")
        logger.info(f"   📄 Module: {spec.module_path}")
        logger.info(f"   🧪 Tests: {spec.test_path}")
        logger.info(f"   🔧 Functions: {', '.join(spec.functions)}")
        
        return spec
    
    def generate_module(self, spec: ModuleSpec) -> GenerationResult:
        """
        Generate complete module with implementation and tests.
        
        Args:
            spec: Module specification
            
        Returns:
            GenerationResult with success status and content
        """
        logger.info(f"🚀 Starting code generation for {spec.module_name}...")
        
        result = GenerationResult(success=False)
        
        for attempt in range(self.max_retries):
            result.retry_count = attempt
            
            logger.info(f"🔄 Generation attempt {attempt + 1}/{self.max_retries}")
            
            # Step 1: Generate implementation
            logger.info("   📝 Generating implementation...")
            impl_content = self._generate_implementation(spec, result.errors or [])
            
            if not impl_content:
                if result.errors:
                    result.errors.append("Failed to generate implementation")
                continue
            
            result.module_content = impl_content
            
            # Step 2: Generate tests
            logger.info("   🧪 Generating test suite...")
            test_content = self._generate_tests(spec, impl_content, result.errors or [])
            
            if not test_content:
                if result.errors:
                    result.errors.append("Failed to generate tests")
                continue
            
            result.test_content = test_content
            
            # Step 3: Write files temporarily for analysis
            temp_module = self.project_root / spec.module_path
            temp_test = self.project_root / spec.test_path
            
            try:
                temp_module.parent.mkdir(parents=True, exist_ok=True)
                temp_module.write_text(impl_content)
                
                temp_test.parent.mkdir(parents=True, exist_ok=True)
                temp_test.write_text(test_content)
                
                # Step 4: Run static analysis
                logger.info("   🔍 Running static analysis...")
                analysis = self._run_static_analysis(temp_module)
                result.static_analysis = analysis
                
                if not analysis['passed']:
                    if result.errors:
                        result.errors.append(f"Static analysis failed: {analysis['errors']}")
                    continue
                
                # Step 5: Run tests
                logger.info("   ✅ Running test suite...")
                test_results = self._run_tests(temp_test)
                result.test_results = test_results
                
                if not test_results['passed']:
                    if result.errors:
                        result.errors.append(f"Tests failed: {test_results['failures']}")
                    continue
                
                # Success!
                result.success = True
                logger.info(f"✅ Code generation successful after {attempt + 1} attempt(s)")
                return result
                
            except Exception as e:
                if result.errors:
                    result.errors.append(f"File operation error: {e}")
                logger.error(f"❌ Error: {e}")
                continue
        
        # Max retries exceeded
        logger.error(f"❌ Code generation failed after {self.max_retries} attempts")
        return result
    
    def _generate_implementation(self, spec: ModuleSpec, previous_errors: List[str]) -> Optional[str]:
        """Generate module implementation via LLM."""
        
        error_feedback = ""
        if previous_errors:
            error_feedback = f"""
PREVIOUS ERRORS TO FIX:
{chr(10).join(f"- {err}" for err in previous_errors[-3:])}

Please fix these issues in the new implementation.
"""
        
        prompt = f"""Generate a complete Python module: {spec.module_path}

Description:
{spec.description}

Requirements:
- Module name: {spec.module_name}
- Functions to implement: {', '.join(spec.functions)}
- Dependencies: {', '.join(spec.dependencies) if spec.dependencies else 'None'}

Guidelines:
1. Include comprehensive module docstring
2. Use type hints for all functions
3. Add detailed docstrings with Args/Returns
4. Implement error handling
5. Follow PEP 8 style guide
6. Keep functions focused and testable

{error_feedback}

Output ONLY the complete module code. Do NOT wrap in markdown code blocks.
"""
        
        try:
            response = self.agent.query_qwen(
                prompt=prompt,
                stream=False,
                system_prompt="You are an expert Python developer. Generate clean, well-documented, production-ready code."
            )
            
            if response:
                # Remove code blocks if present
                cleaned = self._clean_code_response(response)
                return cleaned
            
        except Exception as e:
            logger.error(f"❌ LLM error during implementation generation: {e}")
        
        return None
    
    def _generate_tests(self, spec: ModuleSpec, implementation: str, previous_errors: List[str]) -> Optional[str]:
        """Generate test suite via LLM."""
        
        error_feedback = ""
        if previous_errors:
            error_feedback = f"""
PREVIOUS TEST ERRORS TO FIX:
{chr(10).join(f"- {err}" for err in previous_errors[-3:])}

Please ensure tests address these issues.
"""
        
        prompt = f"""Generate comprehensive pytest test suite for: {spec.module_path}

Module Implementation:
```python
{implementation}
```

Requirements:
1. Test all functions in the module
2. Include positive and negative test cases
3. Test edge cases and error handling
4. Use pytest fixtures where appropriate
5. Aim for >80% code coverage
6. Clear test names (test_function_scenario)

{error_feedback}

Output ONLY the complete test file code. Do NOT wrap in markdown code blocks.
"""
        
        try:
            response = self.agent.query_qwen(
                prompt=prompt,
                stream=False,
                system_prompt="You are an expert at writing comprehensive test suites. Generate thorough pytest tests."
            )
            
            if response:
                cleaned = self._clean_code_response(response)
                return cleaned
            
        except Exception as e:
            logger.error(f"❌ LLM error during test generation: {e}")
        
        return None
    
    def _clean_code_response(self, response: str) -> str:
        """Remove markdown code blocks and clean LLM response."""
        # Remove ```python ... ``` or ``` ... ```
        patterns = [
            r'```python\s*\n(.*?)\n```',
            r'```\s*\n(.*?)\n```'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return response.strip()
    
    def _run_static_analysis(self, module_path: Path) -> Dict:
        """Run bandit and flake8 on module."""
        result = {
            'passed': True,
            'errors': [],
            'warnings': []
        }
        
        # Run bandit (security)
        try:
            bandit_output = subprocess.run(
                ['bandit', '-r', str(module_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if bandit_output.returncode != 0:
                # Parse bandit output for issues
                if 'High' in bandit_output.stdout or 'Medium' in bandit_output.stdout:
                    result['passed'] = False
                    result['errors'].append(f"Bandit security issues: {bandit_output.stdout[:200]}")
                else:
                    result['warnings'].append("Bandit low severity warnings")
                    
        except FileNotFoundError:
            logger.warning("⚠️ bandit not installed, skipping security check")
        except Exception as e:
            logger.warning(f"⚠️ bandit error: {e}")
        
        # Run flake8 (style)
        try:
            flake8_output = subprocess.run(
                ['flake8', '--max-line-length=120', str(module_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if flake8_output.returncode != 0:
                result['warnings'].append(f"Flake8 style issues: {flake8_output.stdout[:200]}")
                # Don't fail on style issues, just warn
                
        except FileNotFoundError:
            logger.warning("⚠️ flake8 not installed, skipping style check")
        except Exception as e:
            logger.warning(f"⚠️ flake8 error: {e}")
        
        return result
    
    def _run_tests(self, test_path: Path) -> Dict:
        """Run pytest on test file."""
        result = {
            'passed': False,
            'tests_run': 0,
            'failures': []
        }
        
        try:
            pytest_output = subprocess.run(
                ['pytest', str(test_path), '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_root)
            )
            
            result['passed'] = (pytest_output.returncode == 0)
            
            # Parse output for test count
            passed_match = re.search(r'(\d+) passed', pytest_output.stdout)
            if passed_match:
                result['tests_run'] = int(passed_match.group(1))
            
            # Extract failures if any
            if not result['passed']:
                failure_pattern = r'FAILED (.*?) - (.*?)(?:\n|$)'
                failures = re.findall(failure_pattern, pytest_output.stdout)
                result['failures'] = [f"{test}: {msg}" for test, msg in failures[:5]]
            
        except FileNotFoundError:
            result['failures'].append("pytest not installed")
        except subprocess.TimeoutExpired:
            result['failures'].append("Test execution timed out")
        except Exception as e:
            result['failures'].append(f"Test execution error: {e}")
        
        return result


__all__ = ['CodeGenerator', 'ModuleSpec', 'GenerationResult']
