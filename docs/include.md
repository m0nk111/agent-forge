# include.md

## Introduction

This document outlines the guidelines for including docstrings and type hints in Python files within our project.

## Guidelines

1. **Docstrings**: Every function, class, and module should have a docstring at the beginning of its definition.
   - The first line of the docstring should be a concise summary.
   - The subsequent lines provide a detailed description, including parameters, return values, and exceptions raised.
   - Use triple double quotes (`"""`) for multi-line strings.

2. **Type Hints**: Type hints are used to specify variable types in function signatures.
   - Use Python's built-in types (e.g., `int`, `str`, `list`).
   - For complex types, use the `typing` module (e.g., `List[int]`, `Dict[str, Any]`).

3. **Consistency**: Follow PEP 484 and PEP 257 guidelines for docstring format.
   - Use a consistent style for parameters and return values in docstrings.
   - Type hints should be included in function signatures where possible.

## Example

```python
def add(a: int, b: int) -> int:
    """Return the sum of two integers.
    
    Args:
        a (int): The first integer.
        b (int): The second integer.
        
    Returns:
        int: The sum of the two integers.
    """
    return a + b

class Calculator:
    """A simple calculator class."""
    
    def multiply(self, x: float, y: float) -> float:
        """Return the product of two numbers.
        
        Args:
            x (float): The first number.
            y (float): The second number.
            
        Returns:
            float: The product of the two numbers.
        """
        return x * y
```