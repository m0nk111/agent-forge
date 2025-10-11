"""Utility module for string manipulation functions."""

from typing import Optional

def capitalize_words(text: str) -> str:
    """Capitalize each word in the given string.
    
    Args:
        text (str): The input string to be capitalized.
        
    Returns:
        str: A new string with each word capitalized.
        
    Raises:
        ValueError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    
    return ' '.join(word.capitalize() for word in text.split())

def reverse_string(text: str) -> str:
    """Reverse the given string.
    
    Args:
        text (str): The input string to be reversed.
        
    Returns:
        str: A new string that is the reverse of the input.
        
    Raises:
        ValueError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    
    return text[::-1]