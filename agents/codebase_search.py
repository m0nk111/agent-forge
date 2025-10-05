"""
Codebase search operations for Qwen agent.

Enables finding relevant code across large codebases.
Critical for understanding existing implementations before making changes.

Author: Agent Forge
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import re


class CodebaseSearch:
    """
    Search codebase for patterns and semantic matches.
    
    Features:
    - grep-based pattern matching (fast, exact)
    - File type filtering
    - Context lines (before/after matches)
    - Result ranking and limiting
    """
    
    def __init__(self, project_root: str):
        """
        Initialize codebase search.
        
        Args:
            project_root: Root directory for search operations
        """
        self.project_root = Path(project_root).resolve()
    
    def grep_search(
        self,
        pattern: str,
        file_pattern: Optional[str] = None,
        regex: bool = False,
        ignore_case: bool = True,
        context_lines: int = 2,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Search codebase using grep (fast pattern matching).
        
        Similar to GitHub Copilot's grep_search tool.
        
        Args:
            pattern: Pattern to search for
            file_pattern: Glob pattern for files (e.g., "*.py", "src/**/*.js")
            regex: If True, treat pattern as regex
            ignore_case: If True, case-insensitive search
            context_lines: Number of lines before/after match to include
            max_results: Maximum number of results to return
            
        Returns:
            List of dicts with: file, line_num, line_content, context_before, context_after
        """
        results = []
        
        try:
            # Build grep command
            cmd = ['grep', '-rn']  # Recursive, line numbers
            
            if regex:
                cmd.append('-E')  # Extended regex
            else:
                cmd.append('-F')  # Fixed string (faster)
            
            if ignore_case:
                cmd.append('-i')
            
            if context_lines > 0:
                cmd.extend(['-C', str(context_lines)])  # Context lines
            
            # Add pattern
            cmd.append(pattern)
            
            # Add path
            if file_pattern:
                # Use find to filter by pattern first
                find_cmd = ['find', str(self.project_root), '-type', 'f', '-name', file_pattern]
                find_result = subprocess.run(
                    find_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if find_result.returncode == 0:
                    files = find_result.stdout.strip().split('\n')
                    # Search each file
                    for file_path in files[:max_results]:
                        if file_path and Path(file_path).exists():
                            file_results = self._grep_file(
                                file_path,
                                pattern,
                                regex,
                                ignore_case,
                                context_lines
                            )
                            results.extend(file_results)
                            if len(results) >= max_results:
                                break
            else:
                # Search all files
                cmd.append(str(self.project_root))
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 or result.returncode == 1:  # 1 = no matches
                    results = self._parse_grep_output(result.stdout, context_lines)
            
            # Limit results
            results = results[:max_results]
            
            print(f"🔍 Found {len(results)} match(es) for '{pattern}'")
            return results
            
        except subprocess.TimeoutExpired:
            print(f"⏱️  Search timed out for pattern: {pattern}")
            return []
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def _grep_file(
        self,
        file_path: str,
        pattern: str,
        regex: bool,
        ignore_case: bool,
        context_lines: int
    ) -> List[Dict]:
        """Grep a single file and return results."""
        results = []
        
        try:
            cmd = ['grep', '-n']
            
            if regex:
                cmd.append('-E')
            else:
                cmd.append('-F')
            
            if ignore_case:
                cmd.append('-i')
            
            if context_lines > 0:
                cmd.extend(['-C', str(context_lines)])
            
            cmd.extend([pattern, file_path])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                results = self._parse_grep_output(result.stdout, context_lines)
            
        except:
            pass
        
        return results
    
    def _parse_grep_output(self, output: str, context_lines: int) -> List[Dict]:
        """Parse grep output into structured results."""
        results = []
        lines = output.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Parse grep line: filename:line_num:content or filename:line_num-content (context)
            match = re.match(r'^([^:]+):(\d+)[:-](.*)$', line)
            if match:
                file_path = match.group(1)
                line_num = int(match.group(2))
                content = match.group(3)
                
                # Make path relative to project root
                try:
                    rel_path = Path(file_path).relative_to(self.project_root)
                except:
                    rel_path = Path(file_path)
                
                # Collect context lines
                context_before = []
                context_after = []
                
                # Look back for context
                j = i - 1
                while j >= 0 and len(context_before) < context_lines:
                    prev_line = lines[j].strip()
                    if prev_line and prev_line.startswith(file_path):
                        context_match = re.match(r'^[^:]+:\d+[:-](.*)$', prev_line)
                        if context_match:
                            context_before.insert(0, context_match.group(1))
                    j -= 1
                
                # Look forward for context
                j = i + 1
                while j < len(lines) and len(context_after) < context_lines:
                    next_line = lines[j].strip()
                    if next_line and next_line.startswith(file_path):
                        context_match = re.match(r'^[^:]+:\d+[:-](.*)$', next_line)
                        if context_match:
                            context_after.append(context_match.group(1))
                    j += 1
                
                results.append({
                    'file': str(rel_path),
                    'line_num': line_num,
                    'line_content': content,
                    'context_before': context_before,
                    'context_after': context_after
                })
            
            i += 1
        
        return results
    
    def find_function(self, function_name: str, language: str = 'python') -> List[Dict]:
        """
        Find function definitions across codebase.
        
        Args:
            function_name: Name of function to find
            language: Programming language ('python', 'javascript', etc.)
            
        Returns:
            List of matches with file, line_num, definition
        """
        patterns = {
            'python': [
                f'def {function_name}\\(',
                f'async def {function_name}\\('
            ],
            'javascript': [
                f'function {function_name}\\(',
                f'const {function_name} =',
                f'{function_name}: function',
                f'{function_name}\\(.*\\) {{',  # Arrow functions
            ]
        }
        
        if language not in patterns:
            print(f"⚠️  Language '{language}' not supported for function search")
            return []
        
        all_results = []
        for pattern in patterns[language]:
            results = self.grep_search(
                pattern,
                regex=True,
                ignore_case=False,
                context_lines=5,
                max_results=20
            )
            all_results.extend(results)
        
        print(f"🔍 Found {len(all_results)} definition(s) for '{function_name}'")
        return all_results
    
    def find_class(self, class_name: str, language: str = 'python') -> List[Dict]:
        """
        Find class definitions across codebase.
        
        Args:
            class_name: Name of class to find
            language: Programming language
            
        Returns:
            List of matches
        """
        patterns = {
            'python': [f'class {class_name}[:(\\[]'],
            'javascript': [
                f'class {class_name}',
                f'export class {class_name}'
            ]
        }
        
        if language not in patterns:
            return []
        
        all_results = []
        for pattern in patterns[language]:
            results = self.grep_search(
                pattern,
                regex=True,
                ignore_case=False,
                context_lines=10,
                max_results=20
            )
            all_results.extend(results)
        
        print(f"🔍 Found {len(all_results)} class definition(s) for '{class_name}'")
        return all_results
    
    def find_imports(self, module_name: str, language: str = 'python') -> List[Dict]:
        """
        Find imports of a module across codebase.
        
        Useful for understanding dependencies and usage.
        
        Args:
            module_name: Module name to search for
            language: Programming language
            
        Returns:
            List of files importing the module
        """
        patterns = {
            'python': [
                f'import {module_name}',
                f'from {module_name}',
            ],
            'javascript': [
                f"import.*from ['\"].*{module_name}",
                f"require\\(['\"].*{module_name}"
            ]
        }
        
        if language not in patterns:
            return []
        
        all_results = []
        for pattern in patterns[language]:
            results = self.grep_search(
                pattern,
                regex=True,
                ignore_case=False,
                context_lines=1,
                max_results=50
            )
            all_results.extend(results)
        
        print(f"🔍 Found {len(all_results)} import(s) of '{module_name}'")
        return all_results
    
    def find_usages(self, symbol_name: str, file_pattern: Optional[str] = None) -> List[Dict]:
        """
        Find all usages of a symbol (function, class, variable).
        
        Args:
            symbol_name: Symbol to search for
            file_pattern: Optional file pattern to limit search
            
        Returns:
            List of usages
        """
        results = self.grep_search(
            symbol_name,
            file_pattern=file_pattern,
            regex=False,
            ignore_case=False,
            context_lines=2,
            max_results=100
        )
        
        print(f"🔍 Found {len(results)} usage(s) of '{symbol_name}'")
        return results


# Test harness
if __name__ == '__main__':
    import tempfile
    import shutil
    
    print("🧪 Testing CodebaseSearch...\n")
    
    # Create temp project structure
    temp_dir = tempfile.mkdtemp()
    
    # Create test files
    (Path(temp_dir) / 'src').mkdir()
    
    (Path(temp_dir) / 'src' / 'main.py').write_text("""
import os
import sys
from utils import Helper

class MyClass:
    def __init__(self):
        self.helper = Helper()
    
    def process(self, data):
        return self.helper.transform(data)

def my_function(arg):
    return arg * 2
""")
    
    (Path(temp_dir) / 'src' / 'utils.py').write_text("""
class Helper:
    def transform(self, data):
        return data.upper()
    
    def validate(self, data):
        return len(data) > 0
""")
    
    (Path(temp_dir) / 'tests').mkdir()
    (Path(temp_dir) / 'tests' / 'test_main.py').write_text("""
from src.main import MyClass, my_function

def test_my_function():
    assert my_function(2) == 4

def test_my_class():
    obj = MyClass()
    assert obj.process("hello") == "HELLO"
""")
    
    # Create search instance
    search = CodebaseSearch(temp_dir)
    
    print("Test 1: Find function definition")
    results = search.find_function('my_function', 'python')
    if results:
        print(f"  Found in: {results[0]['file']}:{results[0]['line_num']}")
    
    print("\nTest 2: Find class definition")
    results = search.find_class('MyClass', 'python')
    if results:
        print(f"  Found in: {results[0]['file']}:{results[0]['line_num']}")
    
    print("\nTest 3: Find imports")
    results = search.find_imports('utils', 'python')
    if results:
        for r in results:
            print(f"  {r['file']}:{r['line_num']} - {r['line_content']}")
    
    print("\nTest 4: Find usages")
    results = search.find_usages('Helper')
    print(f"  Found {len(results)} usage(s)")
    
    print("\nTest 5: Grep search with context")
    results = search.grep_search('transform', context_lines=1)
    if results:
        print(f"  Match: {results[0]['file']}:{results[0]['line_num']}")
        print(f"  Line: {results[0]['line_content']}")
        if results[0]['context_after']:
            print(f"  Context: {results[0]['context_after'][0]}")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    print("\n✅ CodebaseSearch tests completed!")
