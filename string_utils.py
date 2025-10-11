"""Utility functions for string manipulation."""

import re

def capitalize_words(text: str) -> str:
    """Capitalize the first letter of each word in the input text.

    Args:
        text (str): The input text to be processed.

    Returns:
        str: The text with the first letter of each word capitalized.
    
    Raises:
        ValueError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    return ' '.join(word.capitalize() for word in text.split())

def reverse_string(text: str) -> str:
    """Reverse the input string.

    Args:
        text (str): The input text to be processed.

    Returns:
        str: The reversed version of the input string.
    
    Raises:
        ValueError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    return text[::-1]

def count_vowels(text: str) -> int:
    """Count the number of vowels in the input text.

    Args:
        text (str): The input text to be processed.

    Returns:
        int: The number of vowels in the input text.
    
    Raises:
        ValueError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    return len(re.findall(r'[aeiouAEIOU]', text))