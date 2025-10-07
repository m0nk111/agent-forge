#!/usr/bin/env python3
"""
Safe Shell Command Runner for Agents

Provides controlled shell access with safety guardrails:
- Command timeouts
- Working directory restrictions
- Allowed/blocked command lists
- Resource limits
- Output capture and logging

Critical for Issue #64: Enable agents to test their code locally.
"""

import subprocess
import os
import shlex
import time
import re
import logging
import psutil
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """Shell command execution status"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"
    ERROR = "error"


@dataclass
class CommandResult:
    """Result of shell command execution"""
    command: str
    status: CommandStatus
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    working_dir: str
    timestamp: datetime
    blocked_reason: Optional[str] = None
    
    def is_success(self) -> bool:
        return self.status == CommandStatus.SUCCESS and self.exit_code == 0
    
    def to_dict(self) -> Dict:
        return {
            'command': self.command,
            'status': self.status.value,
            'exit_code': self.exit_code,
            'stdout': self.stdout[:1000],  # Limit output size
            'stderr': self.stderr[:1000],
            'execution_time': self.execution_time,
            'working_dir': self.working_dir,
            'timestamp': self.timestamp.isoformat(),
            'blocked_reason': self.blocked_reason,
        }


class ShellSafetyConfig:
    """Safety configuration for shell execution"""
    
    def __init__(self):
        # Timeouts
        self.default_timeout = 300  # 5 minutes
        self.max_timeout = 3600     # 1 hour
        
        # Working directory restrictions
        self.allowed_base_dirs = [
            '/home/flip/agent-forge',
            '/tmp/agent-',  # Temporary agent workspaces
        ]
        
        # Blocked commands (security risks)
        self.blocked_commands = [
            'rm -rf /',
            'rm -rf *',
            'dd',
            'mkfs',
            'fdisk',
            'shutdown',
            'reboot',
            'init',
            'systemctl stop',
            ':(){ :|:& };:',  # Fork bomb
            'chmod 777',
            'chown root',
        ]
        
        # Blocked patterns (regex)
        self.blocked_patterns = [
            r'rm\s+-rf\s+/',           # Dangerous rm commands
            r'>\s*/dev/sd',            # Writing to disk devices
            r'curl.*\|\s*bash',        # Piping to bash
            r'wget.*\|\s*sh',          # Piping to shell
            r'eval\s*\(',              # Eval injection
            r'exec\s*\(',              # Exec injection
        ]
        
        # Allowed commands (whitelist for strict mode)
        self.allowed_commands = [
            # Testing
            'pytest', 'python', 'python3', 'node', 'npm', 'jest', 'cargo', 'go', 'make',
            # Build
            'gcc', 'clang', 'javac', 'rustc', 'tsc',
            # Package managers
            'pip', 'pip3', 'npm', 'yarn', 'cargo', 'apt-get', 'apt',
            # Version control
            'git',
            # File operations
            'ls', 'cat', 'grep', 'find', 'wc', 'head', 'tail', 'less', 'more',
            # Process management
            'ps', 'top', 'kill', 'pkill',
            # Utilities
            'echo', 'cd', 'pwd', 'mkdir', 'touch', 'mv', 'cp',
        ]
        
        # Resource limits
        self.max_output_size = 10 * 1024 * 1024  # 10MB
        self.max_concurrent_commands = 5
        
    def is_command_allowed(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Check if command is allowed to execute.
        Returns (allowed, blocked_reason)
        """
        command_lower = command.lower().strip()
        
        # Check blocked commands
        for blocked in self.blocked_commands:
            if blocked in command_lower:
                return False, f"Blocked command pattern: {blocked}"
        
        # Check blocked regex patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, command_lower):
                return False, f"Blocked regex pattern: {pattern}"
        
        # Check for piping to bash/sh (dangerous)
        if '| bash' in command_lower or '| sh' in command_lower:
            return False, "Piping to bash/sh is blocked for security"
        
        # Check for sudo (requires manual approval)
        if command_lower.startswith('sudo '):
            return False, "sudo commands require explicit admin approval"
        
        return True, None
    
    def is_working_dir_allowed(self, working_dir: str) -> bool:
        """Check if working directory is within allowed paths"""
        abs_path = os.path.abspath(working_dir)
        return any(abs_path.startswith(allowed) for allowed in self.allowed_base_dirs)


class ShellRunner:
    """
    Safe shell command runner for agents.
    
    Usage:
        runner = ShellRunner(agent_id="test-agent")
        result = runner.run_command("pytest tests/", timeout=60)
        if result.is_success():
            print(result.stdout)
    """
    
    def __init__(
        self,
        agent_id: str,
        working_dir: Optional[str] = None,
        safety_config: Optional[ShellSafetyConfig] = None
    ):
        self.agent_id = agent_id
        self.working_dir = working_dir or os.getcwd()
        self.safety_config = safety_config or ShellSafetyConfig()
        self.command_history: List[CommandResult] = []
        self.active_processes: Dict[int, subprocess.Popen] = {}
        
        logger.info(f"🐚 ShellRunner initialized for agent {agent_id} in {self.working_dir}")
    
    def run_command(
        self,
        command: str,
        timeout: Optional[int] = None,
        capture_output: bool = True,
        env: Optional[Dict[str, str]] = None
    ) -> CommandResult:
        """
        Execute shell command with safety guardrails.
        
        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds (default: 300s)
            capture_output: Whether to capture stdout/stderr
            env: Additional environment variables
            
        Returns:
            CommandResult with execution details
        """
        start_time = time.time()
        timestamp = datetime.now()
        timeout = timeout or self.safety_config.default_timeout
        
        # Safety check: working directory
        if not self.safety_config.is_working_dir_allowed(self.working_dir):
            logger.error(f"🚫 Working directory not allowed: {self.working_dir}")
            return CommandResult(
                command=command,
                status=CommandStatus.BLOCKED,
                exit_code=-1,
                stdout="",
                stderr=f"Working directory {self.working_dir} is not allowed",
                execution_time=0,
                working_dir=self.working_dir,
                timestamp=timestamp,
                blocked_reason="Working directory not in allowed list"
            )
        
        # Safety check: command validation
        is_allowed, blocked_reason = self.safety_config.is_command_allowed(command)
        if not is_allowed:
            logger.error(f"🚫 Blocked command from agent {self.agent_id}: {command}")
            logger.error(f"   Reason: {blocked_reason}")
            return CommandResult(
                command=command,
                status=CommandStatus.BLOCKED,
                exit_code=-1,
                stdout="",
                stderr=f"Command blocked: {blocked_reason}",
                execution_time=0,
                working_dir=self.working_dir,
                timestamp=timestamp,
                blocked_reason=blocked_reason
            )
        
        logger.info(f"🔧 Agent {self.agent_id} executing: {command}")
        logger.info(f"   Working dir: {self.working_dir}")
        logger.info(f"   Timeout: {timeout}s")
        
        try:
            # Prepare environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # Execute command
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                cwd=self.working_dir,
                env=exec_env,
                text=True,
                preexec_fn=os.setsid  # Create new process group for better control
            )
            
            # Track active process
            self.active_processes[process.pid] = process
            
            try:
                # Wait for completion with timeout
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
                status = CommandStatus.SUCCESS if exit_code == 0 else CommandStatus.FAILURE
                
            except subprocess.TimeoutExpired:
                logger.warning(f"⏱️ Command timeout after {timeout}s: {command}")
                process.kill()
                stdout, stderr = process.communicate()
                exit_code = -1
                status = CommandStatus.TIMEOUT
                
            finally:
                # Remove from active processes
                self.active_processes.pop(process.pid, None)
            
            execution_time = time.time() - start_time
            
            # Truncate large outputs
            if len(stdout) > self.safety_config.max_output_size:
                stdout = stdout[:self.safety_config.max_output_size] + "\n... (output truncated)"
            if len(stderr) > self.safety_config.max_output_size:
                stderr = stderr[:self.safety_config.max_output_size] + "\n... (output truncated)"
            
            result = CommandResult(
                command=command,
                status=status,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                working_dir=self.working_dir,
                timestamp=timestamp
            )
            
            # Log result
            if result.is_success():
                logger.info(f"✅ Command completed successfully in {execution_time:.2f}s")
            else:
                logger.error(f"❌ Command failed with exit code {exit_code}")
                if stderr:
                    logger.error(f"   Error: {stderr[:200]}")
            
            # Store in history
            self.command_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"💥 Command execution error: {e}")
            return CommandResult(
                command=command,
                status=CommandStatus.ERROR,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=time.time() - start_time,
                working_dir=self.working_dir,
                timestamp=timestamp
            )
    
    def run_test_suite(self, test_command: Optional[str] = None) -> CommandResult:
        """
        Run repository test suite (pytest, npm test, cargo test, etc.)
        Auto-detects test framework if not specified.
        """
        if test_command:
            return self.run_command(test_command, timeout=600)  # 10 min timeout for tests
        
        # Auto-detect test framework
        repo_path = Path(self.working_dir)
        
        # Python (pytest)
        if (repo_path / "pytest.ini").exists() or (repo_path / "tests").exists():
            logger.info("🔍 Detected Python project, running pytest")
            return self.run_command("pytest -v", timeout=600)
        
        # Node.js (npm test)
        if (repo_path / "package.json").exists():
            logger.info("🔍 Detected Node.js project, running npm test")
            return self.run_command("npm test", timeout=600)
        
        # Rust (cargo test)
        if (repo_path / "Cargo.toml").exists():
            logger.info("🔍 Detected Rust project, running cargo test")
            return self.run_command("cargo test", timeout=600)
        
        # Go (go test)
        if (repo_path / "go.mod").exists():
            logger.info("🔍 Detected Go project, running go test")
            return self.run_command("go test ./...", timeout=600)
        
        # Makefile (make test)
        if (repo_path / "Makefile").exists():
            logger.info("🔍 Detected Makefile, running make test")
            return self.run_command("make test", timeout=600)
        
        logger.warning("⚠️ No test framework detected")
        return CommandResult(
            command="auto-detect test",
            status=CommandStatus.ERROR,
            exit_code=-1,
            stdout="",
            stderr="No test framework detected (pytest, npm, cargo, go, make)",
            execution_time=0,
            working_dir=self.working_dir,
            timestamp=datetime.now()
        )
    
    def kill_all_processes(self):
        """Kill all active processes started by this runner"""
        for pid, process in list(self.active_processes.items()):
            try:
                logger.warning(f"🔪 Killing process {pid}")
                process.kill()
                process.wait(timeout=5)
            except Exception as e:
                logger.error(f"❌ Failed to kill process {pid}: {e}")
        
        self.active_processes.clear()
    
    def get_command_history(self, limit: int = 10) -> List[CommandResult]:
        """Get recent command history"""
        return self.command_history[-limit:]
    
    def get_statistics(self) -> Dict:
        """Get execution statistics"""
        total = len(self.command_history)
        if total == 0:
            return {'total': 0, 'success': 0, 'failure': 0, 'timeout': 0, 'blocked': 0}
        
        success = sum(1 for r in self.command_history if r.status == CommandStatus.SUCCESS)
        failure = sum(1 for r in self.command_history if r.status == CommandStatus.FAILURE)
        timeout = sum(1 for r in self.command_history if r.status == CommandStatus.TIMEOUT)
        blocked = sum(1 for r in self.command_history if r.status == CommandStatus.BLOCKED)
        
        return {
            'total': total,
            'success': success,
            'failure': failure,
            'timeout': timeout,
            'blocked': blocked,
            'success_rate': (success / total * 100) if total > 0 else 0,
        }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    runner = ShellRunner(agent_id="test-agent", working_dir="/home/flip/agent-forge")
    
    print("\n🧪 Testing ShellRunner\n")
    
    # Test 1: Safe command
    print("Test 1: List files")
    result = runner.run_command("ls -la")
    print(f"  Status: {result.status.value}")
    print(f"  Exit code: {result.exit_code}")
    print(f"  Execution time: {result.execution_time:.2f}s\n")
    
    # Test 2: Blocked command
    print("Test 2: Blocked dangerous command")
    result = runner.run_command("rm -rf /")
    print(f"  Status: {result.status.value}")
    print(f"  Blocked reason: {result.blocked_reason}\n")
    
    # Test 3: Command with timeout
    print("Test 3: Command with short timeout")
    result = runner.run_command("sleep 10", timeout=2)
    print(f"  Status: {result.status.value}")
    print(f"  Exit code: {result.exit_code}\n")
    
    # Test 4: Auto-detect and run tests
    print("Test 4: Auto-detect tests")
    result = runner.run_test_suite()
    print(f"  Status: {result.status.value}")
    print(f"  Command: {result.command}\n")
    
    # Show statistics
    print("Statistics:")
    stats = runner.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
