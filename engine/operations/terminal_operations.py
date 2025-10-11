"""
Terminal command execution for Qwen agent.

Enables running commands and testing code instead of only generating.
Critical for validation and testing workflows.

Author: Agent Forge
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import shlex


class TerminalOperations:
    """
    Execute terminal commands with security controls.
    
    Features:
    - Run commands with timeout and working directory
    - Run background processes
    - Output capture with size limits
    - Security: whitelist allowed commands, block dangerous operations
    """
    
    # Commands that are always allowed
    ALLOWED_COMMANDS = {
        'pytest', 'python', 'python3', 'pip', 'pip3',
        'npm', 'node', 'yarn', 'pnpm',
        'git', 'docker', 'docker-compose',
        'make', 'cmake', 'gcc', 'g++',
        'ls', 'cat', 'grep', 'find', 'head', 'tail', 'pwd',
        'echo', 'curl', 'wget',
        'which', 'whereis', 'type'
    }
    
    # Patterns that are always blocked
    BLOCKED_PATTERNS = [
        'rm -rf',
        'rm -fr',
        'sudo rm',
        '> /dev/sda',
        'mkfs',
        'dd if=',
        'chmod 777',
        ':(){:|:&};:',  # fork bomb
        'sudo su',
        'sudo -i'
    ]
    
    def __init__(self, project_root: str, allow_all: bool = False):
        """
        Initialize terminal operations.
        
        Args:
            project_root: Root directory for command execution
            allow_all: If True, disable command restrictions (DANGEROUS)
        """
        self.project_root = Path(project_root).resolve()
        self.allow_all = allow_all
        
        if allow_all:
            print("⚠️  WARNING: Terminal security disabled (allow_all=True)")
    
    def _validate_command(self, command: str) -> Tuple[bool, str]:
        """
        Validate command against security rules.
        
        Args:
            command: Command string to validate
            
        Returns:
            (is_valid, error_message)
        """
        if self.allow_all:
            return True, ""
        
        # Check blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in command:
                return False, f"Blocked dangerous pattern: {pattern}"
        
        # Extract base command
        try:
            parts = shlex.split(command)
        except Exception as e:
            return False, f"Invalid command syntax: {e}"
        
        if not parts:
            return False, "Empty command"
        
        base_command = parts[0].split('/')[-1]  # Handle /usr/bin/python -> python
        
        # Check if allowed
        if base_command not in self.ALLOWED_COMMANDS:
            return False, f"Command not in whitelist: {base_command}"
        
        return True, ""
    
    def run_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 30,
        max_output_size: int = 1024 * 1024  # 1MB
    ) -> Dict:
        """
        Run command and capture output.
        
        Args:
            command: Command string to execute
            cwd: Working directory (relative to project root)
            timeout: Maximum execution time in seconds
            max_output_size: Maximum output size in bytes
            
        Returns:
            Dict with: success, returncode, stdout, stderr, timeout_occurred
        """
        # Validate command
        is_valid, error_msg = self._validate_command(command)
        if not is_valid:
            print(f"❌ Command blocked: {error_msg}")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': error_msg,
                'timeout_occurred': False
            }
        
        # Determine working directory
        if cwd:
            work_dir = self.project_root / cwd
        else:
            work_dir = self.project_root
        
        if not work_dir.exists():
            print(f"❌ Working directory not found: {work_dir}")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f"Working directory not found: {work_dir}",
                'timeout_occurred': False
            }
        
        print(f"▶️  Running: {command}")
        print(f"📁 Working directory: {work_dir}")
        
        try:
            # Run command
            result = subprocess.run(
                command,
                cwd=str(work_dir),
                shell=True,
                capture_output=True,
                timeout=timeout,
                text=True
            )
            
            # Truncate output if too large
            stdout = result.stdout
            stderr = result.stderr
            
            if len(stdout) > max_output_size:
                stdout = stdout[:max_output_size] + f"\n[... truncated, {len(result.stdout) - max_output_size} bytes omitted]"
            
            if len(stderr) > max_output_size:
                stderr = stderr[:max_output_size] + f"\n[... truncated, {len(result.stderr) - max_output_size} bytes omitted]"
            
            success = result.returncode == 0
            
            if success:
                print(f"✅ Command completed (exit code {result.returncode})")
            else:
                print(f"❌ Command failed (exit code {result.returncode})")
            
            return {
                'success': success,
                'returncode': result.returncode,
                'stdout': stdout,
                'stderr': stderr,
                'timeout_occurred': False
            }
            
        except subprocess.TimeoutExpired:
            print(f"⏱️  Command timed out after {timeout}s")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f"Command timed out after {timeout} seconds",
                'timeout_occurred': True
            }
        except Exception as e:
            print(f"❌ Error executing command: {e}")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'timeout_occurred': False
            }
    
    def run_background(
        self,
        command: str,
        cwd: Optional[str] = None,
        log_file: Optional[str] = None
    ) -> Optional[int]:
        """
        Run command in background and return process ID.
        
        Useful for servers, watchers, etc.
        
        Args:
            command: Command string to execute
            cwd: Working directory (relative to project root)
            log_file: File to redirect output (relative to project root)
            
        Returns:
            Process ID if successful, None otherwise
        """
        # Validate command
        is_valid, error_msg = self._validate_command(command)
        if not is_valid:
            print(f"❌ Command blocked: {error_msg}")
            return None
        
        # Determine working directory
        if cwd:
            work_dir = self.project_root / cwd
        else:
            work_dir = self.project_root
        
        if not work_dir.exists():
            print(f"❌ Working directory not found: {work_dir}")
            return None
        
        print(f"▶️  Starting background: {command}")
        print(f"📁 Working directory: {work_dir}")
        if log_file:
            print(f"📝 Logging to: {log_file}")
        
        log_file_handle = None
        try:
            # Setup log file with proper resource management
            if log_file:
                log_path = self.project_root / log_file
                log_path.parent.mkdir(parents=True, exist_ok=True)
                # Open file in context manager for proper cleanup
                log_file_handle = open(log_path, 'w')
                stdout_dest = log_file_handle
                stderr_dest = subprocess.STDOUT
            else:
                stdout_dest = subprocess.DEVNULL
                stderr_dest = subprocess.DEVNULL
            
            # Start background process
            process = subprocess.Popen(
                command,
                cwd=str(work_dir),
                shell=True,
                stdout=stdout_dest,
                stderr=stderr_dest,
                start_new_session=True  # Detach from parent
            )
            
            # Close log file handle after process starts
            # Note: Process keeps its own file descriptor
            if log_file_handle:
                log_file_handle.close()
            
            print(f"✅ Background process started (PID: {process.pid})")
            return process.pid
            
        except Exception as e:
            print(f"❌ Error starting background process: {e}")
            # Ensure file handle is closed on error
            if log_file_handle:
                log_file_handle.close()
            return None
    
    def run_tests(
        self,
        test_paths: Optional[List[str]] = None,
        timeout: int = 120
    ) -> Dict:
        """
        Run tests using appropriate test framework.
        
        Auto-detects pytest, jest, etc.
        
        Args:
            test_paths: Specific test files/directories to run
            timeout: Maximum execution time in seconds
            
        Returns:
            Dict with test results
        """
        # Try to detect test framework
        if (self.project_root / 'pytest.ini').exists() or \
           (self.project_root / 'setup.py').exists():
            # Python project with pytest
            if test_paths:
                command = f"pytest {' '.join(test_paths)} -v"
            else:
                command = "pytest -v"
        
        elif (self.project_root / 'package.json').exists():
            # Node.js project
            command = "npm test"
        
        else:
            print("⚠️  Could not detect test framework")
            return {
                'success': False,
                'framework': 'unknown',
                'tests_run': 0,
                'passed': 0,
                'failed': 0,
                'error': 'Test framework not detected'
            }
        
        # Run tests
        result = self.run_command(command, timeout=timeout)
        
        # Parse results (basic parsing, can be improved)
        framework = 'pytest' if 'pytest' in command else 'npm'
        
        return {
            'success': result['success'],
            'framework': framework,
            'returncode': result['returncode'],
            'stdout': result['stdout'],
            'stderr': result['stderr'],
            'timeout_occurred': result['timeout_occurred']
        }


# Test harness
if __name__ == '__main__':
    import tempfile
    import shutil
    
    print("🧪 Testing TerminalOperations...\n")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    terminal = TerminalOperations(temp_dir)
    
    print("Test 1: Run allowed command (echo)")
    result = terminal.run_command("echo 'Hello from Agent-Forge!'")
    print(f"Output: {result['stdout'].strip()}")
    print(f"Success: {result['success']}\n")
    
    print("Test 2: Run allowed command (ls)")
    result = terminal.run_command("ls -la")
    print(f"Success: {result['success']}")
    print(f"Output lines: {len(result['stdout'].splitlines())}\n")
    
    print("Test 3: Try blocked command (rm -rf)")
    result = terminal.run_command("rm -rf /")
    print(f"Blocked: {not result['success']}")
    print(f"Error: {result['stderr']}\n")
    
    print("Test 4: Try non-whitelisted command (reboot)")
    result = terminal.run_command("reboot")
    print(f"Blocked: {not result['success']}")
    print(f"Error: {result['stderr']}\n")
    
    print("Test 5: Run with working directory")
    # Create subdirectory
    subdir = Path(temp_dir) / "subdir"
    subdir.mkdir()
    result = terminal.run_command("pwd", cwd="subdir")
    print(f"Working dir: {result['stdout'].strip()}")
    print(f"Success: {result['success']}\n")
    
    print("Test 6: Python command")
    result = terminal.run_command("python3 -c 'print(2 + 2)'")
    print(f"Output: {result['stdout'].strip()}")
    print(f"Success: {result['success']}\n")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    print("✅ TerminalOperations tests completed!")
