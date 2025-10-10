#!/usr/bin/env python3
"""
Test suite for workspace_tools.py line-range reading features

Tests Issue #8 implementation:
- read_file_lines() - precise line-range reading
- read_function() - AST-based function extraction
"""

import sys
import tempfile
from pathlib import Path

# Zorg dat project root op sys.path staat
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.operations.workspace_tools import WorkspaceTools


def test_read_file_lines():
    """Test read_file_lines with various scenarios"""
    print("🧪 Testing read_file_lines()...")
    
    # Create temp test file
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        
        tools = WorkspaceTools(tmpdir)
        
        # Test 1: Read middle lines
        result = tools.read_file_lines("test.txt", 2, 4)
        expected = "Line 2\nLine 3\nLine 4"
        assert result == expected, f"Expected:\n{expected}\n\nGot:\n{result}"
        print("  ✓ Read middle lines (2-4)")
        
        # Test 2: Read first line only
        result = tools.read_file_lines("test.txt", 1, 1)
        expected = "Line 1"
        assert result == expected, f"Expected:\n{expected}\n\nGot:\n{result}"
        print("  ✓ Read single line (1)")
        
        # Test 3: Read all lines
        result = tools.read_file_lines("test.txt", 1, 5)
        expected = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        assert result == expected, f"Expected:\n{expected}\n\nGot:\n{result}"
        print("  ✓ Read all lines (1-5)")
        
        # Test 4: Read last lines
        result = tools.read_file_lines("test.txt", 4, 5)
        expected = "Line 4\nLine 5"
        assert result == expected, f"Expected:\n{expected}\n\nGot:\n{result}"
        print("  ✓ Read last lines (4-5)")
        
        # Test 5: Invalid start_line (< 1)
        try:
            tools.read_file_lines("test.txt", 0, 3)
            assert False, "Should raise ValueError for start_line < 1"
        except ValueError as e:
            assert "must be >= 1" in str(e)
            print("  ✓ Reject invalid start_line < 1")
        
        # Test 6: Invalid end_line < start_line
        try:
            tools.read_file_lines("test.txt", 3, 2)
            assert False, "Should raise ValueError for end_line < start_line"
        except ValueError as e:
            assert "must be >=" in str(e)
            print("  ✓ Reject end_line < start_line")
        
        # Test 7: start_line beyond file length
        try:
            tools.read_file_lines("test.txt", 100, 200)
            assert False, "Should raise ValueError for start_line beyond file"
        except ValueError as e:
            assert "fewer than" in str(e)
            print("  ✓ Reject start_line beyond file length")
    
    print("✅ read_file_lines() tests passed!\n")


def test_read_function():
    """Test read_function with Python files"""
    print("🧪 Testing read_function()...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("""# Test module
import os

def hello():
    '''Say hello'''
    return "Hello"

@decorator
def decorated_func():
    '''Function with decorator'''
    return "Decorated"

class MyClass:
    def method(self):
        '''Class method'''
        return "Method"

async def async_func():
    '''Async function'''
    return "Async"
""")
        
        tools = WorkspaceTools(tmpdir)
        
        # Test 1: Read simple function
        result = tools.read_function("test.py", "hello")
        assert "def hello():" in result
        assert "return \"Hello\"" in result
        print("  ✓ Read simple function")
        
        # Test 2: Read decorated function
        result = tools.read_function("test.py", "decorated_func")
        assert "@decorator" in result
        assert "def decorated_func():" in result
        print("  ✓ Read decorated function (includes decorator)")
        
        # Test 3: Read class method
        result = tools.read_function("test.py", "method")
        assert "def method(self):" in result
        assert "return \"Method\"" in result
        print("  ✓ Read class method")
        
        # Test 4: Read async function
        result = tools.read_function("test.py", "async_func")
        assert "async def async_func():" in result
        print("  ✓ Read async function")
        
        # Test 5: Function not found
        try:
            tools.read_function("test.py", "nonexistent")
            assert False, "Should raise ValueError for missing function"
        except ValueError as e:
            assert "not found" in str(e)
            print("  ✓ Reject nonexistent function")
        
        # Test 6: Not a Python file
        non_py = Path(tmpdir) / "test.txt"
        non_py.write_text("Not Python")
        try:
            tools.read_function("test.txt", "hello")
            assert False, "Should raise ValueError for non-Python file"
        except ValueError as e:
            assert "Not a Python file" in str(e)
            print("  ✓ Reject non-Python file")
    
    print("✅ read_function() tests passed!\n")


def test_integration():
    """Integration test with real agent-forge files"""
    print("🧪 Integration test with agent-forge...")
    
    # Test on agent-forge itself
    agent_forge_root = Path(__file__).parent.parent
    if not agent_forge_root.exists():
        print("  ⚠ Skipping (agent-forge root not found)")
        return
    
    tools = WorkspaceTools(str(agent_forge_root))
    
    # Test 1: Read specific function from workspace_tools.py (engine path)
    result = tools.read_function("engine/operations/workspace_tools.py", "read_file_lines")
    assert "def read_file_lines" in result
    assert "start_line" in result
    assert "end_line" in result
    print("  ✓ Read read_file_lines from workspace_tools.py")
    
    # Test 2: Read lines from README
    result = tools.read_file_lines("README.md", 1, 5)
    assert len(result) > 0
    print("  ✓ Read first 5 lines of README.md")
    
    print("✅ Integration tests passed!\n")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Issue #8: Precise line-range file reading")
    print("=" * 60 + "\n")
    
    try:
        test_read_file_lines()
        test_read_function()
        test_integration()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
