"""Simple calculator module for basic arithmetic operations.

This module provides basic calculator functionality with proper error handling
and type hints for use in the agent-forge project.
"""


def add(a: float, b: float) -> float:
    """Add two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
        
    Examples:
        >>> add(2, 3)
        5.0
        >>> add(-1, 1)
        0.0
        >>> add(2.5, 3.5)
        6.0
    """
    return float(a + b)


def subtract(a: float, b: float) -> float:
    """Subtract second number from first.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Difference between a and b (a - b)
        
    Examples:
        >>> subtract(5, 3)
        2.0
        >>> subtract(3, 5)
        -2.0
        >>> subtract(10.5, 2.5)
        8.0
    """
    return float(a - b)


def multiply(a: float, b: float) -> float:
    """Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Product of a and b
        
    Examples:
        >>> multiply(4, 3)
        12.0
        >>> multiply(2.5, 4)
        10.0
        >>> multiply(-2, 3)
        -6.0
    """
    return float(a * b)


def divide(a: float, b: float) -> float:
    """Divide first number by second.
    
    Args:
        a: Numerator
        b: Denominator
        
    Returns:
        Quotient of a divided by b
        
    Raises:
        ValueError: If b is zero (division by zero)
        
    Examples:
        >>> divide(10, 2)
        5.0
        >>> divide(15, 3)
        5.0
        >>> divide(7, 2)
        3.5
        >>> divide(10, 0)
        Traceback (most recent call last):
            ...
        ValueError: Cannot divide by zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return float(a / b)
