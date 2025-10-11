"""Utility module for string manipulation."""

from typing import Optional


def capitalize_words(text: str) -> str:
    """Capitalizes each word in the given text.

    Args:
        text (str): The input text to be capitalized.

    Returns:
        str: The text with each word capitalized.

    Raises:
        ValueError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    return ' '.join(word.capitalize() for word in text.split())


def reverse_string(text: str) -> str:
    """Reverses the given string.

    Args:
        text (str): The input text to be reversed.

    Returns:
        str: The reversed text.

    Raises:
        ValueError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    return text[::-1]