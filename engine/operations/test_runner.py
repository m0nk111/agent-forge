"""
Test execution and validation for multi-LLM debug system.

Enables running tests, parsing results, and providing structured feedback
to the debug loop. Supports pytest and unittest frameworks with detailed
failure analysis and categorization.

Enhanced features:
- Structured test failure parsing with file/line numbers
- Failure type detection (syntax, assertion, runtime, etc.)
- Timeout handling and error recovery
- Integration with debug loop for automatic retesting

Author: Agent Forge
"""

from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum
import re
import os
import logging

# Debug flag
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of test failures"""
    SYNTAX_ERROR = "syntax_error"
    ASSERTION_ERROR = "assertion_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    IMPORT_ERROR = "import_error"
    OTHER = "other"


@dataclass
class TestFailure:
    """Details of a single test failure"""
    test_name: str
    test_file: str
    failure_type: FailureType
    error_message: str
    traceback: str
    line_number: Optional[int] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None


@dataclass
class TestResult:
    """Complete test execution result"""
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0
    duration: float = 0.0
    failures: List[TestFailure] = field(default_factory=list)
    success: bool = False
    command: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


class TestRunner:
    """
    Execute tests and parse results with enhanced failure analysis.
    
    Features:
    - Auto-detect test framework (pytest, jest, etc.)
    - Run all tests or specific test files
    - Parse test results into structured format with detailed failure info
    - Extract failure details with file/line numbers for debug loop
    - Categorize failure types (syntax, assertion, runtime, etc.)
    - Timeout handling and error recovery
    """
    
    def __init__(self, terminal_ops):
        """
        Initialize test runner.
        
        Args:
            terminal_ops: TerminalOperations instance for command execution
        """
        self.terminal = terminal_ops
        self.project_root = terminal_ops.project_root
        
        if DEBUG:
            logger.debug(f"🔍 TestRunner initialized")
            logger.debug(f"  - Project root: {self.project_root}")
    
    def _detect_failure_type(self, error_message: str, traceback: str) -> FailureType:
        """
        Detect type of test failure from error message and traceback
        
        Args:
            error_message: Error message from test
            traceback: Full traceback
        
        Returns:
            FailureType enum value
        """
        combined = (error_message + "\n" + traceback).lower()
        
        if "syntaxerror" in combined or "indentationerror" in combined:
            return FailureType.SYNTAX_ERROR
        elif "assertionerror" in combined or "assert " in combined:
            return FailureType.ASSERTION_ERROR
        elif "importerror" in combined or "modulenotfounderror" in combined:
            return FailureType.IMPORT_ERROR
        elif "timeout" in combined or "timedout" in combined:
            return FailureType.TIMEOUT
        elif any(err in combined for err in ["error", "exception", "traceback"]):
            return FailureType.RUNTIME_ERROR
        else:
            return FailureType.OTHER
    
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
    
    def _parse_pytest_output(self, output: str) -> TestResult:
        """
        Parse pytest output into structured results with enhanced failure details.
        
        Args:
            output: pytest stdout
            
        Returns:
            TestResult with detailed failure information
        """
        result = TestResult()
        result.stdout = output
        
        if DEBUG:
            logger.debug(f"🔍 Parsing pytest output ({len(output)} chars)")
        
        # Extract summary line: "5 passed, 2 failed, 1 skipped in 1.23s"
        summary_pattern = r'(\d+)\s+passed(?:,\s*(\d+)\s+failed)?(?:,\s*(\d+)\s+skipped)?(?:\s+in\s+([\d.]+)s)?'
        summary_match = re.search(summary_pattern, output)
        
        if summary_match:
            result.passed = int(summary_match.group(1))
            result.failed = int(summary_match.group(2) or 0)
            result.skipped = int(summary_match.group(3) or 0)
            result.duration = float(summary_match.group(4) or 0)
            result.total = result.passed + result.failed + result.skipped
            result.success = result.failed == 0
            
            if DEBUG:
                logger.debug(f"📊 Summary: {result.passed} passed, {result.failed} failed, {result.skipped} skipped")
        
        # Extract failure details
        # Pattern: FAILED test_file.py::test_name - Error message
        failure_pattern = r'FAILED\s+([\w./]+)::([\w]+)\s+-\s+(.*?)(?=FAILED|=+|$)'
        
        for match in re.finditer(failure_pattern, output, re.DOTALL):
            test_file = match.group(1)
            test_name = match.group(2)
            error_section = match.group(3).strip()
            
            # Extract first line as error message
            error_lines = error_section.split('\n')
            error_message = error_lines[0] if error_lines else "Unknown error"
            
            # Full section is traceback
            traceback = error_section
            
            # Try to find source file and line from traceback
            # Pattern: file.py:123: or File "file.py", line 123
            source_pattern = r'(?:File\s+")?([^\s:"]+\.py)"?[:,]\s*(?:line\s+)?(\d+)'
            source_match = re.search(source_pattern, traceback)
            
            source_file = None
            source_line = None
            if source_match:
                source_file = source_match.group(1)
                source_line = int(source_match.group(2))
            
            # Detect failure type
            failure_type = self._detect_failure_type(error_message, traceback)
            
            failure = TestFailure(
                test_name=test_name,
                test_file=test_file,
                failure_type=failure_type,
                error_message=error_message,
                traceback=traceback,
                source_file=source_file,
                source_line=source_line
            )
            
            result.failures.append(failure)
            
            if DEBUG:
                logger.debug(f"🐛 Parsed failure: {test_name} ({failure_type.value})")
        
        return result
    
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
    ) -> TestResult:
        """
        Run tests using detected framework with enhanced result parsing.
        
        Args:
            test_paths: Specific test files/directories to run
            timeout: Maximum execution time in seconds
            
        Returns:
            TestResult with detailed test execution information
        """
        framework = self._detect_framework()
        
        if not framework:
            print("⚠️  Could not detect test framework")
            result = TestResult()
            result.success = False
            result.command = "unknown"
            return result
        
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
            result = TestResult()
            result.success = False
            result.command = f"{framework} (unsupported)"
            return result
        
        print(f"🧪 Running tests with {framework}...")
        
        if DEBUG:
            logger.debug(f"🔍 Command: {command}")
        
        # Execute tests
        exec_result = self.terminal.run_command(command, timeout=timeout)
        
        # Parse results based on framework
        if framework == 'pytest':
            parsed = self._parse_pytest_output(exec_result['stdout'])
            parsed.command = command
            parsed.stderr = exec_result.get('stderr', '')
        elif framework == 'jest':
            parsed_dict = self._parse_jest_output(exec_result['stdout'])
            # Convert dict to TestResult for jest
            parsed = TestResult(
                passed=parsed_dict['passed'],
                failed=parsed_dict['failed'],
                total=parsed_dict['tests_run'],
                success=parsed_dict['failed'] == 0,
                command=command,
                stdout=exec_result['stdout'],
                stderr=exec_result.get('stderr', '')
            )
        else:
            # Generic result
            parsed = TestResult()
            parsed.command = command
            parsed.stdout = exec_result['stdout']
            parsed.stderr = exec_result.get('stderr', '')
        
        # Update success status
        parsed.success = exec_result['success'] and parsed.failed == 0
        
        # Print summary
        if parsed.success:
            print(f"✅ All tests passed ({parsed.passed}/{parsed.total})")
        else:
            print(f"❌ {parsed.failed} test(s) failed ({parsed.passed}/{parsed.total} passed)")
            if parsed.failures:
                print(f"📋 Failures:")
                for i, failure in enumerate(parsed.failures[:5], 1):  # Show max 5
                    print(f"  {i}. {failure.test_file}::{failure.test_name}")
                    print(f"     [{failure.failure_type.value}] {failure.error_message}")
                    if failure.source_file and failure.source_line:
                        print(f"     at {failure.source_file}:{failure.source_line}")
        
        return parsed
    
    def run_specific_test(
        self,
        test_identifier: str,
        timeout: int = 60
    ) -> TestResult:
        """
        Run a specific test by name or path.
        
        Args:
            test_identifier: Test file path or test name pattern
            timeout: Maximum execution time in seconds
            
        Returns:
            TestResult with test execution results
        """
        framework = self._detect_framework()
        
        if not framework:
            result = TestResult()
            result.success = False
            result.command = "unknown"
            return result
        
        # Build command based on framework
        if framework == 'pytest':
            # Support both file paths and test names
            # pytest tests/test_file.py::test_name
            command = f"pytest {test_identifier} -v"
        
        elif framework == 'jest':
            # jest -t "test name pattern"
            command = f"npm test -- -t '{test_identifier}'"
        
        else:
            result = TestResult()
            result.success = False
            result.command = f"{framework} (unsupported for specific tests)"
            return result
        
        print(f"🎯 Running specific test: {test_identifier}")
        
        # Execute
        exec_result = self.terminal.run_command(command, timeout=timeout)
        
        # Parse results
        if framework == 'pytest':
            parsed = self._parse_pytest_output(exec_result['stdout'])
            parsed.command = command
        elif framework == 'jest':
            parsed_dict = self._parse_jest_output(exec_result['stdout'])
            parsed = TestResult(
                passed=parsed_dict['passed'],
                failed=parsed_dict['failed'],
                total=parsed_dict['tests_run'],
                success=parsed_dict['failed'] == 0,
                command=command,
                stdout=exec_result['stdout']
            )
        else:
            parsed = TestResult()
            parsed.command = command
            parsed.stdout = exec_result['stdout']
        
        parsed.success = exec_result['success'] and parsed.failed == 0
        
        return parsed
    
    def get_failure_context(self, failure: TestFailure) -> str:
        """
        Generate context string from failure for debug loop consumption.
        
        Args:
            failure: TestFailure object from test results
            
        Returns:
            Context string describing the failure for LLMs
        """
        context = f"Test '{failure.test_name}' in {failure.test_file} failed:\n"
        context += f"Failure Type: {failure.failure_type.value}\n"
        context += f"Error: {failure.error_message}\n"
        
        if failure.source_file and failure.source_line:
            context += f"Source Location: {failure.source_file}:{failure.source_line}\n"
        
        if failure.traceback:
            context += f"Traceback:\n{failure.traceback}\n"
        
        return context
    
    def format_failures_for_llm(self, result: TestResult) -> str:
        """
        Format test failures specifically for LLM consumption.
        
        Args:
            result: TestResult with failures
        
        Returns:
            Formatted string optimized for LLM analysis
        """
        if not result.failures:
            return "✅ All tests passed successfully."
        
        lines = []
        lines.append(f"❌ {len(result.failures)} test(s) failed:")
        lines.append("")
        
        for i, failure in enumerate(result.failures, 1):
            lines.append(f"{i}. Test: {failure.test_name}")
            lines.append(f"   File: {failure.test_file}")
            lines.append(f"   Type: {failure.failure_type.value}")
            
            if failure.source_file and failure.source_line:
                lines.append(f"   Source: {failure.source_file} (line {failure.source_line})")
            
            lines.append(f"   Error: {failure.error_message}")
            
            # Include relevant traceback snippet (not entire thing)
            if failure.traceback:
                traceback_lines = failure.traceback.split('\n')[:5]
                lines.append(f"   Traceback (first 5 lines):")
                for line in traceback_lines:
                    lines.append(f"     {line}")
            
            lines.append("")
        
        return "\n".join(lines)


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
    print(f"Success: {results.success}")
    print(f"Tests run: {results.total}")
    print(f"Passed: {results.passed}")
    print(f"Failed: {results.failed}")
    print(f"Duration: {results.duration:.2f}s")
    print(f"Failures: {len(results.failures)}\n")
    
    if results.failures:
        print("Test 3: Get failure context")
        for failure in results.failures:
            context = runner.get_failure_context(failure)
            print(context)
        
        print("Test 4: Format for LLM")
        llm_format = runner.format_failures_for_llm(results)
        print(llm_format)
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    print("✅ TestRunner tests completed!")
