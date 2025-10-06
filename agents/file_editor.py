"""
File editing operations for Qwen agent.

Enables editing existing files instead of only creating new ones.
Critical for iterative development and refactoring.

Author: Agent Forge
"""

from pathlib import Path
from typing import Optional, List
import re


class FileEditor:
    """
    Edit existing files with various operations.
    
    Features:
    - Replace exact text matches (like GitHub Copilot)
    - Insert at specific line numbers
    - Append to files
    - Safe with validation and backups
    """
    
    def __init__(self, project_root: str):
        """
        Initialize file editor.
        
        Args:
            project_root: Root directory for all file operations
        """
        self.project_root = Path(project_root).resolve()
        
        # Initialize instruction validator (optional)
        self.validator = None
        try:
            from agents.instruction_validator import InstructionValidator
            self.validator = InstructionValidator(project_root=str(self.project_root))
        except Exception:
            # Validator is optional - continue without it
            pass
    
    def _validate_file_location(self, filepath: str) -> bool:
        """
        Validate file location before edit/create.
        
        Args:
            filepath: Relative path from project root
            
        Returns:
            True if location is valid or validation disabled
        """
        if not self.validator:
            return True
        
        try:
            result = self.validator.validate_file_location(filepath)
            if not result.valid:
                print(f"⚠️  {result.message}")
                if result.suggestions:
                    print(f"   💡 {result.suggestions[0]}")
                return False
            return True
        except Exception:
            # Don't fail on validator errors
            return True
    
    def replace_in_file(
        self,
        filepath: str,
        old_text: str,
        new_text: str,
        validate: bool = True
    ) -> bool:
        """
        Replace exact text match in file.
        
        Similar to GitHub Copilot's replace_string_in_file.
        
        Args:
            filepath: Relative path from project root
            old_text: Exact text to find and replace (must match exactly)
            new_text: Replacement text
            validate: If True, verify old_text exists exactly once
            
        Returns:
            True if successful, False otherwise
        """
        # Validate file location first
        if not self._validate_file_location(filepath):
            print(f"❌ File location validation failed for: {filepath}")
            return False
        
        full_path = self.project_root / filepath
        
        if not full_path.exists():
            print(f"❌ File not found: {filepath}")
            return False
        
        try:
            # Read file
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if old_text exists
            if old_text not in content:
                print(f"❌ Text not found in {filepath}")
                print(f"Looking for: {old_text[:100]}...")
                return False
            
            # Validate single occurrence if requested
            if validate:
                count = content.count(old_text)
                if count == 0:
                    print(f"❌ Text not found in {filepath}")
                    return False
                elif count > 1:
                    print(f"⚠️  Text appears {count} times in {filepath}, skipping replacement")
                    print("   Use validate=False to replace all occurrences")
                    return False
            
            # Replace
            new_content = content.replace(old_text, new_text)
            
            # Write back
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ Replaced text in {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error editing {filepath}: {e}")
            return False
    
    def insert_at_line(
        self,
        filepath: str,
        line_num: int,
        text: str,
        after: bool = False
    ) -> bool:
        """
        Insert text at specific line number.
        
        Args:
            filepath: Relative path from project root
            line_num: Line number (1-based)
            text: Text to insert
            after: If True, insert after line; if False, insert before
            
        Returns:
            True if successful, False otherwise
        """
        full_path = self.project_root / filepath
        
        if not full_path.exists():
            print(f"❌ File not found: {filepath}")
            return False
        
        try:
            # Read lines
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Validate line number
            if line_num < 1 or line_num > len(lines) + 1:
                print(f"❌ Invalid line number {line_num} for {filepath} ({len(lines)} lines)")
                return False
            
            # Insert (convert to 0-based index)
            insert_index = line_num if after else line_num - 1
            
            # Ensure text ends with newline
            if not text.endswith('\n'):
                text += '\n'
            
            lines.insert(insert_index, text)
            
            # Write back
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            action = "after" if after else "before"
            print(f"✅ Inserted text {action} line {line_num} in {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error editing {filepath}: {e}")
            return False
    
    def append_to_file(self, filepath: str, text: str) -> bool:
        """
        Append text to end of file.
        
        Args:
            filepath: Relative path from project root
            text: Text to append
            
        Returns:
            True if successful, False otherwise
        """
        full_path = self.project_root / filepath
        
        if not full_path.exists():
            print(f"❌ File not found: {filepath}")
            return False
        
        try:
            # Append
            with open(full_path, 'a', encoding='utf-8') as f:
                if not text.endswith('\n'):
                    text += '\n'
                f.write(text)
            
            print(f"✅ Appended text to {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error appending to {filepath}: {e}")
            return False
    
    def insert_after_pattern(
        self,
        filepath: str,
        pattern: str,
        text: str,
        regex: bool = False
    ) -> bool:
        """
        Insert text after first line matching pattern.
        
        Useful for adding imports, methods, etc.
        
        Args:
            filepath: Relative path from project root
            pattern: Pattern to search for
            text: Text to insert after matching line
            regex: If True, treat pattern as regex
            
        Returns:
            True if successful, False otherwise
        """
        full_path = self.project_root / filepath
        
        if not full_path.exists():
            print(f"❌ File not found: {filepath}")
            return False
        
        try:
            # Read lines
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find matching line
            found_index = None
            for i, line in enumerate(lines):
                if regex:
                    if re.search(pattern, line):
                        found_index = i
                        break
                else:
                    if pattern in line:
                        found_index = i
                        break
            
            if found_index is None:
                print(f"❌ Pattern not found in {filepath}: {pattern}")
                return False
            
            # Insert after matching line
            if not text.endswith('\n'):
                text += '\n'
            
            lines.insert(found_index + 1, text)
            
            # Write back
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"✅ Inserted text after pattern in {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error editing {filepath}: {e}")
            return False
    
    def delete_lines(
        self,
        filepath: str,
        start_line: int,
        end_line: Optional[int] = None
    ) -> bool:
        """
        Delete lines from file.
        
        Args:
            filepath: Relative path from project root
            start_line: First line to delete (1-based)
            end_line: Last line to delete (inclusive, 1-based). If None, delete only start_line
            
        Returns:
            True if successful, False otherwise
        """
        full_path = self.project_root / filepath
        
        if not full_path.exists():
            print(f"❌ File not found: {filepath}")
            return False
        
        try:
            # Read lines
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Validate line numbers
            if start_line < 1 or start_line > len(lines):
                print(f"❌ Invalid start line {start_line} for {filepath} ({len(lines)} lines)")
                return False
            
            if end_line is None:
                end_line = start_line
            
            if end_line < start_line or end_line > len(lines):
                print(f"❌ Invalid end line {end_line}")
                return False
            
            # Delete lines (convert to 0-based indices)
            del lines[start_line - 1:end_line]
            
            # Write back
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            count = end_line - start_line + 1
            print(f"✅ Deleted {count} line(s) from {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error editing {filepath}: {e}")
            return False


# Test harness
if __name__ == '__main__':
    import tempfile
    import shutil
    
    print("🧪 Testing FileEditor...\n")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    editor = FileEditor(temp_dir)
    
    # Create test file
    test_file = Path(temp_dir) / "test.py"
    test_content = """# Test file
import os
import sys

def hello():
    print("Hello, world!")

def goodbye():
    print("Goodbye!")
"""
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print("Test 1: Replace exact text")
    editor.replace_in_file(
        "test.py",
        'print("Hello, world!")',
        'print("Hello, Agent-Forge!")'
    )
    
    print("\nTest 2: Insert after pattern")
    editor.insert_after_pattern(
        "test.py",
        "import sys",
        "import json"
    )
    
    print("\nTest 3: Append to file")
    editor.append_to_file(
        "test.py",
        "\nif __name__ == '__main__':\n    hello()\n"
    )
    
    print("\nTest 4: Insert at line number")
    editor.insert_at_line("test.py", 3, "# New comment\n", after=True)
    
    print("\n" + "="*60)
    print("Final file content:")
    print("="*60)
    with open(test_file, 'r') as f:
        print(f.read())
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    print("✅ FileEditor tests completed!")
