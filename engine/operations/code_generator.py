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
                    error_msg = f"Tests failed: {test_results['failures']}"
                    logger.warning(f"   ❌ {error_msg}")
                    if result.errors:
                        result.errors.append(error_msg)
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
        
        prompt = f"""You are generating the IMPLEMENTATION file (not tests): {spec.module_path}

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

CRITICAL: Output ONLY the implementation code for {spec.module_path}.
- DO include: imports, function definitions, classes, implementation logic
- DO NOT include: test code, pytest fixtures, test assertions
- DO NOT wrap in markdown code blocks or add explanations
- Start directly with imports or module docstring
"""
        
        try:
            response = self.agent.query_llm(
                prompt=prompt,
                system_prompt="You are an expert Python developer. Generate clean, well-documented, production-ready code.",
                stream=False
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
        
        prompt = f"""You are generating the TEST file (not implementation): {spec.test_path}

Module Implementation to Test:
```python
{implementation}
```

Requirements for {spec.test_path}:
1. Test all functions in the module
2. Include positive and negative test cases
3. Test edge cases and error handling
4. Use pytest fixtures where appropriate
5. Aim for >80% code coverage
6. Clear test names (test_function_scenario)

{error_feedback}

CRITICAL: Output ONLY the test file code for {spec.test_path}.
- DO include: pytest imports, test functions, fixtures, assertions, mock usage
- DO NOT include: the actual implementation code being tested
- DO NOT include: function definitions from {spec.module_path}
- DO NOT wrap in markdown code blocks or add explanations
- Start directly with: import pytest or from {spec.module_name} import ...

This file will be saved as {spec.test_path}, NOT as implementation.
"""
        
        try:
            response = self.agent.query_llm(
                prompt=prompt,
                system_prompt="You are an expert at writing comprehensive test suites. Generate thorough pytest tests.",
                stream=False
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
        
        # Find tools in venv or system PATH
        def find_tool(name: str) -> Optional[str]:
            """Find tool in venv/bin or system PATH"""
            # Try venv first
            venv_tool = self.project_root / 'venv' / 'bin' / name
            if venv_tool.exists():
                return str(venv_tool)
            # Try system
            import shutil
            return shutil.which(name)
        
        # Run bandit (security)
        bandit_cmd = find_tool('bandit')
        if bandit_cmd:
            try:
                bandit_output = subprocess.run(
                    [bandit_cmd, '-r', str(module_path)],
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
                        
            except Exception as e:
                logger.warning(f"⚠️ bandit error: {e}")
        else:
            logger.debug("⚠️ bandit not found, skipping security check")
        
        # Run flake8 (style)
        flake8_cmd = find_tool('flake8')
        if flake8_cmd:
            try:
                flake8_output = subprocess.run(
                    [flake8_cmd, '--max-line-length=120', str(module_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if flake8_output.returncode != 0:
                    result['warnings'].append(f"Flake8 style issues: {flake8_output.stdout[:200]}")
                    # Don't fail on style issues, just warn
                    
            except Exception as e:
                logger.warning(f"⚠️ flake8 error: {e}")
        else:
            logger.debug("⚠️ flake8 not found, skipping style check")
        
        return result
    
    def _run_tests(self, test_path: Path) -> Dict:
        """Run pytest on test file with coverage metrics."""
        result = {
            'passed': False,
            'tests_run': 0,
            'failures': [],
            'coverage': None
        }
        
        # Find pytest in venv or system PATH
        def find_pytest() -> Optional[str]:
            """Find pytest in venv/bin or system PATH"""
            venv_pytest = self.project_root / 'venv' / 'bin' / 'pytest'
            if venv_pytest.exists():
                return str(venv_pytest)
            import shutil
            return shutil.which('pytest')
        
        pytest_cmd_path = find_pytest()
        if not pytest_cmd_path:
            logger.warning("⚠️ pytest not found, skipping tests")
            result['failures'].append("pytest not installed")
            return result
        
        try:
            # Run pytest with coverage if available
            pytest_cmd = [pytest_cmd_path, str(test_path), '-v', '--tb=short']
            
            # Try to add coverage if pytest-cov is installed
            try:
                import pytest_cov
                # Get module path from test path (tests/test_X.py -> engine/operations/X.py)
                module_name = test_path.stem.replace('test_', '')
                pytest_cmd.extend(['--cov', '--cov-report=term-missing'])
                logger.info("   📊 Coverage tracking enabled")
            except ImportError:
                logger.debug("   ℹ️  pytest-cov not available, skipping coverage")
            
            pytest_output = subprocess.run(
                pytest_cmd,
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
            
            # Parse coverage if available
            coverage_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', pytest_output.stdout)
            if coverage_match:
                result['coverage'] = int(coverage_match.group(1))
                logger.info(f"   📊 Coverage: {result['coverage']}%")
            
            # Extract failures if any
            if not result['passed']:
                # Log failure summary
                logger.warning(f"   ⚠️ Tests failed (returncode: {pytest_output.returncode})")
                
                # Extract specific error details
                failure_pattern = r'FAILED (.*?) - (.+?)(?=\n\n|$)'  # Match until double newline or end
                failures = re.findall(failure_pattern, pytest_output.stdout, re.DOTALL)
                
                # Check for collection errors (import/syntax errors)
                if 'collected 0 items / 1 error' in pytest_output.stdout or 'ERRORS =' in pytest_output.stdout:
                    # Extract error section
                    error_section = pytest_output.stdout.split('ERRORS =')
                    if len(error_section) > 1:
                        error_details = error_section[1].split('=====')[0].strip()[:800]
                        result['failures'].append(f"Collection error: {error_details}")
                        logger.error(f"   ❌ Collection error:\n{error_details}")
                    else:
                        result['failures'].append("Collection error: Unable to parse error details")
                elif failures:
                    result['failures'] = [f"{test}: {msg}" for test, msg in failures[:5]]
                else:
                    # Generic failure
                    result['failures'].append(f"Test execution failed with code {pytest_output.returncode}")
                    # Log first 1000 chars of output for debugging
                    if pytest_output.stderr:
                        result['failures'].append(f"STDERR: {pytest_output.stderr[:500]}")
                    if pytest_output.stdout:
                        # Log last part which usually has the summary
                        stdout_lines = pytest_output.stdout.split('\n')
                        relevant_output = '\n'.join(stdout_lines[-20:])
                        logger.debug(f"   Test output (last 20 lines):\n{relevant_output}")
            
        except FileNotFoundError:
            result['failures'].append("pytest not installed")
        except subprocess.TimeoutExpired:
            result['failures'].append("Test execution timed out")
        except Exception as e:
            result['failures'].append(f"Test execution error: {e}")
        
        return result


__all__ = ['CodeGenerator', 'ModuleSpec', 'GenerationResult']
