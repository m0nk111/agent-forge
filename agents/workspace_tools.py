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
