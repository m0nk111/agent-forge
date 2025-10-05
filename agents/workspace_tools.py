#!/usr/bin/env python3
"""
Workspace Tools - Safe file system operations for autonomous agents

Addresses Issue #3: No workspace awareness
Provides sandboxed workspace exploration within project boundaries.

Author: Agent Forge
"""

import os
from pathlib import Path
from typing import List, Optional, Dict
import fnmatch
import ast


class WorkspaceTools:
    """Safe workspace exploration tools for autonomous agents
    
    All operations are sandboxed within project_root to prevent unauthorized access.
    """
    
    def __init__(self, project_root: str):
        """Initialize workspace tools
        
        Args:
            project_root: Absolute path to project root directory
        """
        self.project_root = Path(project_root).resolve()
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {project_root}")
        if not self.project_root.is_dir():
            raise ValueError(f"Project root is not a directory: {project_root}")
    
    def _validate_path(self, path: str) -> Path:
        """Validate path is within project root
        
        Args:
            path: Relative or absolute path
            
        Returns:
            Resolved absolute path
            
        Raises:
            ValueError: If path escapes project root
        """
        # Convert to Path and resolve
        if os.path.isabs(path):
            full_path = Path(path).resolve()
        else:
            full_path = (self.project_root / path).resolve()
        
        # Check if path is within project root
        try:
            full_path.relative_to(self.project_root)
        except ValueError:
            raise ValueError(f"Path escapes project root: {path}")
        
        return full_path
    
    def list_dir(self, path: str = ".") -> List[str]:
        """List directory contents
        
        Args:
            path: Relative path from project root (default: root)
            
        Returns:
            List of filenames/dirnames (not full paths)
            
        Raises:
            ValueError: If path invalid or escapes project root
            FileNotFoundError: If directory doesn't exist
        """
        full_path = self._validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not full_path.is_dir():
            raise ValueError(f"Not a directory: {path}")
        
        return sorted(os.listdir(full_path))
    
    def read_file(self, path: str, max_size: int = 100000) -> str:
        """Read file contents safely
        
        Args:
            path: Relative path from project root
            max_size: Maximum file size in bytes (default: 100KB)
            
        Returns:
            File contents as string
            
        Raises:
            ValueError: If path invalid, file too large, or not a file
            FileNotFoundError: If file doesn't exist
        """
        full_path = self._validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not full_path.is_file():
            raise ValueError(f"Not a file: {path}")
        
        # Check file size
        size = full_path.stat().st_size
        if size > max_size:
            raise ValueError(f"File too large: {size} bytes (max: {max_size})")
        
        try:
            return full_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            raise ValueError(f"File is not text (UTF-8): {path}")
    
    def read_file_lines(self, path: str, start_line: int, end_line: int) -> str:
        """Read specific line range from file
        
        Addresses Issue #8: Precise line-range file reading
        More efficient than reading entire file when you only need specific sections.
        
        Args:
            path: Relative path from project root
            start_line: First line to read (1-indexed, inclusive)
            end_line: Last line to read (1-indexed, inclusive)
            
        Returns:
            String containing lines [start_line, end_line]
            
        Raises:
            ValueError: If path invalid, line numbers invalid, or not a file
            FileNotFoundError: If file doesn't exist
            
        Example:
            >>> tools.read_file_lines("main.py", 10, 20)
            # Returns lines 10-20 (inclusive)
        """
        full_path = self._validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not full_path.is_file():
            raise ValueError(f"Not a file: {path}")
        
        # Validate line numbers
        if start_line < 1:
            raise ValueError(f"start_line must be >= 1, got {start_line}")
        if end_line < start_line:
            raise ValueError(f"end_line ({end_line}) must be >= start_line ({start_line})")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                # Read only the lines we need
                lines = []
                for line_num, line in enumerate(f, start=1):
                    if line_num < start_line:
                        continue
                    if line_num > end_line:
                        break
                    lines.append(line.rstrip('\n'))
                
                if not lines:
                    # File has fewer lines than start_line
                    raise ValueError(f"File has fewer than {start_line} lines")
                
                return '\n'.join(lines)
        except UnicodeDecodeError:
            raise ValueError(f"File is not text (UTF-8): {path}")
    
    def read_function(self, path: str, function_name: str) -> str:
        """Read specific function definition from Python file
        
        Addresses Issue #8: Precise line-range file reading
        Uses AST parsing to find function boundaries automatically.
        
        Args:
            path: Relative path to Python file
            function_name: Name of function/method to extract
            
        Returns:
            String containing complete function definition
            
        Raises:
            ValueError: If not a Python file, function not found, or parse error
            FileNotFoundError: If file doesn't exist
            
        Example:
            >>> tools.read_function("agents/qwen_agent.py", "execute_phase")
            # Returns complete execute_phase function with decorators
        """
        full_path = self._validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not full_path.is_file():
            raise ValueError(f"Not a file: {path}")
        if not path.endswith('.py'):
            raise ValueError(f"Not a Python file: {path}")
        
        try:
            source = full_path.read_text(encoding='utf-8')
            tree = ast.parse(source, filename=str(full_path))
        except UnicodeDecodeError:
            raise ValueError(f"File is not text (UTF-8): {path}")
        except SyntaxError as e:
            raise ValueError(f"Python syntax error in {path}: {e}")
        
        # Find function in AST
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function_name:
                    # Get line range (AST is 1-indexed)
                    start_line = node.lineno
                    
                    # Include decorators if present
                    if node.decorator_list:
                        start_line = node.decorator_list[0].lineno
                    
                    # end_lineno available in Python 3.8+
                    if hasattr(node, 'end_lineno'):
                        end_line = node.end_lineno
                    else:
                        # Fallback: estimate end from body
                        end_line = node.body[-1].lineno if node.body else start_line
                    
                    # Use read_file_lines to get the content
                    return self.read_file_lines(path, start_line, end_line)
        
        raise ValueError(f"Function '{function_name}' not found in {path}")
    
    def file_exists(self, path: str) -> bool:
        """Check if file or directory exists
        
        Args:
            path: Relative path from project root
            
        Returns:
            True if exists, False otherwise
        """
        try:
            full_path = self._validate_path(path)
            return full_path.exists()
        except ValueError:
            return False
    
    def is_file(self, path: str) -> bool:
        """Check if path is a file
        
        Args:
            path: Relative path from project root
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            full_path = self._validate_path(path)
            return full_path.is_file()
        except ValueError:
            return False
    
    def is_dir(self, path: str) -> bool:
        """Check if path is a directory
        
        Args:
            path: Relative path from project root
            
        Returns:
            True if directory exists, False otherwise
        """
        try:
            full_path = self._validate_path(path)
            return full_path.is_dir()
        except ValueError:
            return False
    
    def find_files(self, pattern: str, path: str = ".", max_depth: int = 5) -> List[str]:
        """Find files matching pattern
        
        Args:
            pattern: Glob pattern (e.g., "*.py", "**/__init__.py")
            path: Starting directory (default: root)
            max_depth: Maximum directory depth (default: 5)
            
        Returns:
            List of relative paths matching pattern
            
        Raises:
            ValueError: If path invalid
        """
        start_path = self._validate_path(path)
        if not start_path.is_dir():
            raise ValueError(f"Not a directory: {path}")
        
        matches = []
        for root, dirs, files in os.walk(start_path):
            # Calculate depth
            depth = len(Path(root).relative_to(start_path).parts)
            if depth > max_depth:
                dirs.clear()  # Don't recurse deeper
                continue
            
            # Match files
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    full_path = Path(root) / filename
                    rel_path = full_path.relative_to(self.project_root)
                    matches.append(str(rel_path))
        
        return sorted(matches)
    
    def get_project_structure(self, path: str = ".", max_depth: int = 3) -> Dict:
        """Get directory tree structure
        
        Args:
            path: Starting directory (default: root)
            max_depth: Maximum depth to traverse (default: 3)
            
        Returns:
            Nested dict representing directory structure
        """
        start_path = self._validate_path(path)
        if not start_path.is_dir():
            raise ValueError(f"Not a directory: {path}")
        
        def build_tree(current_path: Path, depth: int) -> Dict:
            if depth > max_depth:
                return {}
            
            tree = {'_type': 'dir', '_children': {}}
            try:
                for item in sorted(current_path.iterdir()):
                    rel_name = item.name
                    if item.is_dir():
                        tree['_children'][rel_name] = build_tree(item, depth + 1)
                    else:
                        tree['_children'][rel_name] = {'_type': 'file'}
            except PermissionError:
                pass
            
            return tree
        
        return build_tree(start_path, 0)


# Test harness
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 workspace_tools.py <project_root>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    tools = WorkspaceTools(project_root)
    
    print(f"🔧 Workspace Tools Test - Project: {project_root}\n")
    
    # Test list_dir
    print("📁 Root directory contents:")
    for item in tools.list_dir():
        print(f"  - {item}")
    print()
    
    # Test find_files
    print("🔍 Python files (*.py):")
    py_files = tools.find_files("*.py", max_depth=2)
    for f in py_files[:10]:
        print(f"  - {f}")
    if len(py_files) > 10:
        print(f"  ... and {len(py_files) - 10} more")
    print()
    
    # Test file_exists
    test_files = ['README.md', 'setup.py', 'requirements.txt']
    print("📄 File existence checks:")
    for f in test_files:
        exists = tools.file_exists(f)
        print(f"  - {f}: {'✓ exists' if exists else '✗ not found'}")
    print()
    
    print("✅ Workspace tools working!")
