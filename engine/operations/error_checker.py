"""
Error checking and linting for Qwen agent.

Enables detecting syntax errors, code quality issues, and type errors.
Critical for validating generated code before execution.

Author: Agent Forge
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict
import ast
import json


class ErrorChecker:
    """
    Check code for errors and quality issues.
    
    Features:
    - Syntax validation (Python, JavaScript)
    - Linting (pylint, flake8, eslint)
    - Type checking (mypy)
    - Structured error reports
    """
    
    def __init__(self, terminal_ops):
        """
        Initialize error checker.
        
        Args:
            terminal_ops: TerminalOperations instance for running linters
        """
        self.terminal = terminal_ops
        self.project_root = terminal_ops.project_root
    
    def check_syntax(self, file_path: str) -> Dict:
        """
        Check file for syntax errors.
        
        Fast validation without running linters.
        
        Args:
            file_path: Relative path from project root
            
        Returns:
            Dict with: valid, errors (list of dicts with line, message)
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return {
                'valid': False,
                'errors': [{'line': 0, 'message': 'File not found'}]
            }
        
        # Detect language
        suffix = full_path.suffix.lower()
        
        if suffix == '.py':
            return self._check_python_syntax(full_path)
        elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
            return self._check_javascript_syntax(full_path)
        else:
            return {
                'valid': True,
                'errors': [],
                'message': f'Syntax checking not supported for {suffix} files'
            }
    
    def _check_python_syntax(self, file_path: Path) -> Dict:
        """Check Python file syntax using ast module."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Try to parse with ast
            ast.parse(code)
            
            return {
                'valid': True,
                'errors': []
            }
        
        except SyntaxError as e:
            return {
                'valid': False,
                'errors': [{
                    'line': e.lineno or 0,
                    'column': e.offset or 0,
                    'message': e.msg,
                    'text': e.text or ''
                }]
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [{
                    'line': 0,
                    'message': f'Parse error: {str(e)}'
                }]
            }
    
    def _check_javascript_syntax(self, file_path: Path) -> Dict:
        """Check JavaScript/TypeScript syntax using node."""
        # Try to use node to check syntax
        result = self.terminal.run_command(
            f'node --check {file_path.name}',
            cwd=str(file_path.parent),
            timeout=5
        )
        
        if result['success']:
            return {
                'valid': True,
                'errors': []
            }
        else:
            # Parse error from stderr
            errors = []
            if result['stderr']:
                # Basic parsing of node syntax errors
                for line in result['stderr'].split('\n'):
                    if 'SyntaxError' in line or 'Error' in line:
                        errors.append({
                            'line': 0,
                            'message': line.strip()
                        })
            
            return {
                'valid': False,
                'errors': errors or [{'line': 0, 'message': 'Syntax error'}]
            }
    
    def run_linter(
        self,
        file_path: str,
        linter: Optional[str] = None
    ) -> Dict:
        """
        Run linter on file.
        
        Args:
            file_path: Relative path from project root
            linter: Specific linter to use (pylint, flake8, eslint, etc.)
                   If None, auto-detect based on file type
            
        Returns:
            Dict with: success, linter_used, errors, warnings, output
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return {
                'success': False,
                'error': 'File not found'
            }
        
        # Auto-detect linter
        if not linter:
            suffix = full_path.suffix.lower()
            if suffix == '.py':
                # Try flake8 first (faster), fall back to pylint
                if self._has_command('flake8'):
                    linter = 'flake8'
                elif self._has_command('pylint'):
                    linter = 'pylint'
            elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
                if self._has_command('eslint'):
                    linter = 'eslint'
        
        if not linter:
            return {
                'success': False,
                'error': 'No linter available for this file type'
            }
        
        print(f"🔍 Running {linter} on {file_path}...")
        
        # Run linter
        if linter == 'pylint':
            return self._run_pylint(file_path)
        elif linter == 'flake8':
            return self._run_flake8(file_path)
        elif linter == 'eslint':
            return self._run_eslint(file_path)
        else:
            return {
                'success': False,
                'error': f'Unsupported linter: {linter}'
            }
    
    def _has_command(self, command: str) -> bool:
        """Check if command is available."""
        result = self.terminal.run_command(f'which {command}', timeout=5)
        return result['success']
    
    def _run_pylint(self, file_path: str) -> Dict:
        """Run pylint on Python file."""
        result = self.terminal.run_command(
            f'pylint {file_path} --output-format=json',
            timeout=30
        )
        
        errors = []
        warnings = []
        
        if result['stdout']:
            try:
                # Parse pylint JSON output
                messages = json.loads(result['stdout'])
                for msg in messages:
                    item = {
                        'line': msg.get('line', 0),
                        'column': msg.get('column', 0),
                        'message': msg.get('message', ''),
                        'code': msg.get('message-id', ''),
                        'type': msg.get('type', '')
                    }
                    
                    if msg.get('type') in ['error', 'fatal']:
                        errors.append(item)
                    else:
                        warnings.append(item)
            except json.JSONDecodeError:
                # Fall back to plain text parsing
                pass
        
        return {
            'success': result['success'],
            'linter': 'pylint',
            'errors': errors,
            'warnings': warnings,
            'output': result['stdout']
        }
    
    def _run_flake8(self, file_path: str) -> Dict:
        """Run flake8 on Python file."""
        result = self.terminal.run_command(
            f'flake8 {file_path}',
            timeout=30
        )
        
        errors = []
        warnings = []
        
        # Parse flake8 output: filename:line:col: code message
        if result['stdout']:
            for line in result['stdout'].split('\n'):
                if ':' in line:
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        try:
                            item = {
                                'line': int(parts[1]),
                                'column': int(parts[2]),
                                'message': parts[3].strip(),
                                'code': parts[3].split()[0] if parts[3] else ''
                            }
                            
                            # E and F codes are errors, W is warnings
                            code = item['code']
                            if code.startswith('E') or code.startswith('F'):
                                errors.append(item)
                            else:
                                warnings.append(item)
                        except (ValueError, IndexError):
                            pass
        
        return {
            'success': result['success'],
            'linter': 'flake8',
            'errors': errors,
            'warnings': warnings,
            'output': result['stdout']
        }
    
    def _run_eslint(self, file_path: str) -> Dict:
        """Run eslint on JavaScript file."""
        result = self.terminal.run_command(
            f'eslint {file_path} --format json',
            timeout=30
        )
        
        errors = []
        warnings = []
        
        if result['stdout']:
            try:
                # Parse eslint JSON output
                data = json.loads(result['stdout'])
                if data and len(data) > 0:
                    messages = data[0].get('messages', [])
                    for msg in messages:
                        item = {
                            'line': msg.get('line', 0),
                            'column': msg.get('column', 0),
                            'message': msg.get('message', ''),
                            'code': msg.get('ruleId', ''),
                            'severity': msg.get('severity', 1)
                        }
                        
                        if msg.get('severity') == 2:
                            errors.append(item)
                        else:
                            warnings.append(item)
            except json.JSONDecodeError:
                pass
        
        return {
            'success': result['success'],
            'linter': 'eslint',
            'errors': errors,
            'warnings': warnings,
            'output': result['stdout']
        }
    
    def check_types(self, file_path: str) -> Dict:
        """
        Run type checker on file (mypy for Python).
        
        Args:
            file_path: Relative path from project root
            
        Returns:
            Dict with type errors
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return {
                'success': False,
                'error': 'File not found'
            }
        
        suffix = full_path.suffix.lower()
        
        if suffix == '.py':
            if not self._has_command('mypy'):
                return {
                    'success': False,
                    'error': 'mypy not installed'
                }
            
            print(f"🔍 Running mypy on {file_path}...")
            
            result = self.terminal.run_command(
                f'mypy {file_path}',
                timeout=30
            )
            
            errors = []
            
            # Parse mypy output: filename:line: error: message
            if result['stdout']:
                for line in result['stdout'].split('\n'):
                    if ': error:' in line:
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            try:
                                errors.append({
                                    'line': int(parts[1]),
                                    'type': 'type',
                                    'message': parts[3].strip()
                                })
                            except (ValueError, IndexError):
                                pass
            
            return {
                'success': result['success'],
                'checker': 'mypy',
                'errors': errors,
                'output': result['stdout']
            }
        
        else:
            return {
                'success': False,
                'error': f'Type checking not supported for {suffix} files'
            }
    
    def check_all(self, file_path: str) -> Dict:
        """
        Run all checks on a file: syntax, linting, type checking.
        
        Args:
            file_path: Relative path from project root
            
        Returns:
            Dict with all results
        """
        print(f"🔍 Running all checks on {file_path}...")
        
        results = {
            'file': file_path,
            'syntax': self.check_syntax(file_path),
            'linter': self.run_linter(file_path),
            'types': None
        }
        
        # Only run type checker if syntax is valid
        if results['syntax']['valid']:
            full_path = self.project_root / file_path
            if full_path.suffix.lower() == '.py':
                results['types'] = self.check_types(file_path)
        
        # Summary
        total_errors = len(results['syntax'].get('errors', []))
        if results['linter'].get('errors'):
            total_errors += len(results['linter']['errors'])
        if results['types'] and results['types'].get('errors'):
            total_errors += len(results['types']['errors'])
        
        results['summary'] = {
            'has_errors': total_errors > 0,
            'total_errors': total_errors
        }
        
        if total_errors == 0:
            print(f"✅ No errors found in {file_path}")
        else:
            print(f"❌ Found {total_errors} error(s) in {file_path}")
        
        return results


# Test harness
if __name__ == '__main__':
    from terminal_operations import TerminalOperations
    import tempfile
    import shutil
    
    print("🧪 Testing ErrorChecker...\n")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    terminal = TerminalOperations(temp_dir)
    checker = ErrorChecker(terminal)
    
    # Test 1: Valid Python syntax
    valid_file = Path(temp_dir) / 'valid.py'
    valid_file.write_text("""
def hello(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == '__main__':
    print(hello("World"))
""")
    
    print("Test 1: Check valid Python syntax")
    result = checker.check_syntax('valid.py')
    print(f"  Valid: {result['valid']}")
    print(f"  Errors: {len(result['errors'])}")
    
    # Test 2: Invalid Python syntax
    invalid_file = Path(temp_dir) / 'invalid.py'
    invalid_file.write_text("""
def broken(
    print("Missing closing paren"
""")
    
    print("\nTest 2: Check invalid Python syntax")
    result = checker.check_syntax('invalid.py')
    print(f"  Valid: {result['valid']}")
    print(f"  Errors: {len(result['errors'])}")
    if result['errors']:
        print(f"  Error: {result['errors'][0]['message']}")
    
    # Test 3: Run linter (if available)
    print("\nTest 3: Run linter")
    result = checker.run_linter('valid.py')
    if 'error' in result:
        print(f"  {result['error']}")
    else:
        print(f"  Linter: {result['linter']}")
        print(f"  Errors: {len(result.get('errors', []))}")
        print(f"  Warnings: {len(result.get('warnings', []))}")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    print("\n✅ ErrorChecker tests completed!")
