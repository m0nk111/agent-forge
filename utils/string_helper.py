"""Utility functions for string manipulation."""

from typing import Optional

def capitalize_words(text: str) -> str:
    """
    Capitalizes each word in the given text.
    
    Args:
        text (str): The input text to be capitalized.
    
    Returns:
        str: The capitalized text.
    
    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    return ' '.join(word.capitalize() for word in text.split())

def reverse_string(text: str) -> str:
    """
    Reverses the given string.
    
    Args:
        text (str): The input string to be reversed.
    
    Returns:
        str: The reversed string.
    
    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    return text[::-1]