"""
Test execution and validation for Qwen agent.

Enables running tests and validating generated code.
Critical for quality assurance and self-correction loops.

Author: Agent Forge
"""

from pathlib import Path
from typing import Optional, List, Dict
import re


class TestRunner:
    """
    Execute tests and parse results.
    
    Features:
    - Auto-detect test framework (pytest, jest, etc.)
    - Run all tests or specific test files
    - Parse test results into structured format
    - Extract failure details for self-correction
    """
    
    def __init__(self, terminal_ops):
        """
        Initialize test runner.
        
        Args:
            terminal_ops: TerminalOperations instance for command execution
        """
        self.terminal = terminal_ops
        self.project_root = terminal_ops.project_root
    
    def _detect_framework(self) -> Optional[str]:
        """
        Auto-detect test framework.
        
        Returns:
            Framework name ('pytest', 'jest', etc.) or None
        """
        # Python: pytest
        if (self.project_root / 'pytest.ini').exists() or \
           (self.project_root / 'tests').exists() or \
           (self.project_root / 'setup.py').exists():
            return 'pytest'
        
        # Node.js: jest, mocha, etc.
        if (self.project_root / 'package.json').exists():
            try:
                import json
                with open(self.project_root / 'package.json', 'r') as f:
                    pkg = json.load(f)
                    scripts = pkg.get('scripts', {})
                    if 'test' in scripts:
                        test_cmd = scripts['test']
                        if 'jest' in test_cmd:
                            return 'jest'
                        elif 'mocha' in test_cmd:
                            return 'mocha'
                        else:
                            return 'npm'
            except:
                pass
        
        return None
    
    def _parse_pytest_output(self, output: str) -> Dict:
        """
        Parse pytest output into structured results.
        
        Args:
            output: pytest stdout
            
        Returns:
            Dict with: tests_run, passed, failed, failures (list of dicts)
        """
        results = {
            'tests_run': 0,
            'passed': 0,
            'failed': 0,
            'failures': []
        }
        
        # Extract summary line: "5 passed, 2 failed in 1.23s"
        summary_pattern = r'(\d+)\s+passed'
        passed_match = re.search(summary_pattern, output)
        if passed_match:
            results['passed'] = int(passed_match.group(1))
        
        failed_pattern = r'(\d+)\s+failed'
        failed_match = re.search(failed_pattern, output)
        if failed_match:
            results['failed'] = int(failed_match.group(1))
        
        results['tests_run'] = results['passed'] + results['failed']
        
        # Extract failure details
        # Pytest format: FAILED test_file.py::test_name - AssertionError: ...
        failure_pattern = r'FAILED\s+([\w./]+)::([\w]+)\s+-\s+(.*?)(?:\n|$)'
        for match in re.finditer(failure_pattern, output):
            results['failures'].append({
                'file': match.group(1),
                'test': match.group(2),
                'error': match.group(3).strip()
            })
        
        return results
    
    def _parse_jest_output(self, output: str) -> Dict:
        """
        Parse jest output into structured results.
        
        Args:
            output: jest stdout
            
        Returns:
            Dict with: tests_run, passed, failed, failures
        """
        results = {
            'tests_run': 0,
            'passed': 0,
            'failed': 0,
            'failures': []
        }
        
        # Jest summary: "Tests: 2 failed, 5 passed, 7 total"
        passed_pattern = r'(\d+)\s+passed'
        passed_match = re.search(passed_pattern, output)
        if passed_match:
            results['passed'] = int(passed_match.group(1))
        
        failed_pattern = r'(\d+)\s+failed'
        failed_match = re.search(failed_pattern, output)
        if failed_match:
            results['failed'] = int(failed_match.group(1))
        
        total_pattern = r'(\d+)\s+total'
        total_match = re.search(total_pattern, output)
        if total_match:
            results['tests_run'] = int(total_match.group(1))
        
        # Extract failure details (basic parsing)
        failure_lines = []
        in_failure = False
        for line in output.split('\n'):
            if line.strip().startswith('●'):
                in_failure = True
                failure_lines.append(line)
            elif in_failure and line.strip():
                failure_lines.append(line)
            elif in_failure and not line.strip():
                in_failure = False
        
        if failure_lines:
            results['failures'].append({
                'details': '\n'.join(failure_lines)
            })
        
        return results
    
    def run_tests(
        self,
        test_paths: Optional[List[str]] = None,
        timeout: int = 120
    ) -> Dict:
        """
        Run tests using detected framework.
        
        Args:
            test_paths: Specific test files/directories to run
            timeout: Maximum execution time in seconds
            
        Returns:
            Dict with:
            - success: bool
            - framework: str
            - tests_run: int
            - passed: int
            - failed: int
            - failures: list of dicts with failure details
            - output: raw output
        """
        framework = self._detect_framework()
        
        if not framework:
            print("⚠️  Could not detect test framework")
            return {
                'success': False,
                'framework': 'unknown',
                'tests_run': 0,
                'passed': 0,
                'failed': 0,
                'failures': [],
                'error': 'Test framework not detected'
            }
        
        # Build command
        if framework == 'pytest':
            if test_paths:
                command = f"pytest {' '.join(test_paths)} -v"
            else:
                command = "pytest -v"
        
        elif framework == 'jest':
            if test_paths:
                command = f"npm test -- {' '.join(test_paths)}"
            else:
                command = "npm test"
        
        elif framework == 'npm':
            command = "npm test"
        
        else:
            print(f"⚠️  Unsupported framework: {framework}")
            return {
                'success': False,
                'framework': framework,
                'tests_run': 0,
                'passed': 0,
                'failed': 0,
                'failures': [],
                'error': f'Framework {framework} not supported'
            }
        
        print(f"🧪 Running tests with {framework}...")
        
        # Execute tests
        result = self.terminal.run_command(command, timeout=timeout)
        
        # Parse results based on framework
        if framework == 'pytest':
            parsed = self._parse_pytest_output(result['stdout'])
        elif framework == 'jest':
            parsed = self._parse_jest_output(result['stdout'])
        else:
            # Generic parsing
            parsed = {
                'tests_run': 0,
                'passed': 0,
                'failed': 0,
                'failures': []
            }
        
        # Build final result
        final_result = {
            'success': result['success'],
            'framework': framework,
            'tests_run': parsed['tests_run'],
            'passed': parsed['passed'],
            'failed': parsed['failed'],
            'failures': parsed['failures'],
            'output': result['stdout'],
            'stderr': result['stderr'],
            'timeout_occurred': result['timeout_occurred']
        }
        
        # Print summary
        if final_result['success']:
            print(f"✅ All tests passed ({parsed['passed']}/{parsed['tests_run']})")
        else:
            print(f"❌ {parsed['failed']} test(s) failed ({parsed['passed']}/{parsed['tests_run']} passed)")
            if parsed['failures']:
                print(f"📋 Failures:")
                for i, failure in enumerate(parsed['failures'][:5], 1):  # Show max 5
                    if 'file' in failure:
                        print(f"  {i}. {failure['file']}::{failure['test']}")
                        print(f"     {failure['error']}")
                    else:
                        print(f"  {i}. {failure.get('details', 'Unknown failure')}")
        
        return final_result
    
    def run_specific_test(
        self,
        test_identifier: str,
        timeout: int = 60
    ) -> Dict:
        """
        Run a specific test by name or path.
        
        Args:
            test_identifier: Test file path or test name pattern
            timeout: Maximum execution time in seconds
            
        Returns:
            Dict with test results
        """
        framework = self._detect_framework()
        
        if not framework:
            return {
                'success': False,
                'error': 'Test framework not detected'
            }
        
        # Build command based on framework
        if framework == 'pytest':
            # Support both file paths and test names
            # pytest tests/test_file.py::test_name
            command = f"pytest {test_identifier} -v"
        
        elif framework == 'jest':
            # jest -t "test name pattern"
            command = f"npm test -- -t '{test_identifier}'"
        
        else:
            return {
                'success': False,
                'error': f'Specific test execution not supported for {framework}'
            }
        
        print(f"🎯 Running specific test: {test_identifier}")
        
        # Execute
        result = self.terminal.run_command(command, timeout=timeout)
        
        # Parse results
        if framework == 'pytest':
            parsed = self._parse_pytest_output(result['stdout'])
        elif framework == 'jest':
            parsed = self._parse_jest_output(result['stdout'])
        else:
            parsed = {'tests_run': 0, 'passed': 0, 'failed': 0, 'failures': []}
        
        return {
            'success': result['success'],
            'framework': framework,
            'tests_run': parsed['tests_run'],
            'passed': parsed['passed'],
            'failed': parsed['failed'],
            'failures': parsed['failures'],
            'output': result['stdout']
        }
    
    def get_failure_context(self, failure: Dict) -> str:
        """
        Generate context string from failure for self-correction.
        
        Args:
            failure: Failure dict from test results
            
        Returns:
            Context string describing the failure
        """
        if 'file' in failure and 'test' in failure:
            context = f"Test {failure['test']} in {failure['file']} failed:\n"
            context += f"Error: {failure['error']}\n"
        elif 'details' in failure:
            context = f"Test failed:\n{failure['details']}\n"
        else:
            context = "Test failed (no details available)\n"
        
        return context


# Test harness
if __name__ == '__main__':
    from terminal_operations import TerminalOperations
    import tempfile
    import shutil
    
    print("🧪 Testing TestRunner...\n")
    
    # Create temp directory with simple pytest setup
    temp_dir = tempfile.mkdtemp()
    terminal = TerminalOperations(temp_dir)
    runner = TestRunner(terminal)
    
    # Create simple test file
    test_dir = Path(temp_dir) / "tests"
    test_dir.mkdir()
    
    test_file = test_dir / "test_sample.py"
    test_content = """
def test_pass():
    assert 2 + 2 == 4

def test_fail():
    assert 2 + 2 == 5

def test_another_pass():
    assert "hello".upper() == "HELLO"
"""
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print("Test 1: Detect framework")
    framework = runner._detect_framework()
    print(f"Detected: {framework}\n")
    
    print("Test 2: Run all tests (with failures)")
    results = runner.run_tests()
    print(f"Framework: {results['framework']}")
    print(f"Tests run: {results['tests_run']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Failures: {len(results['failures'])}\n")
    
    if results['failures']:
        print("Test 3: Get failure context")
        for failure in results['failures']:
            context = runner.get_failure_context(failure)
            print(context)
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    print("✅ TestRunner tests completed!")
