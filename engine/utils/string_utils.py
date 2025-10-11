"""
engine.utils.string_utils
~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides utility functions for common string manipulations:
- reverse: Reverse a given string.
- capitalize_words: Capitalize the first letter of each word in a string.
- count_vowels: Count the number of vowels in a string (case-insensitive).

All functions handle None or empty string inputs gracefully.
"""

from typing import Optional


def reverse(text: Optional[str]) -> str:
    """
    Reverse the given string.

    Args:
        text (Optional[str]): The string to reverse. Can be None.

    Returns:
        str: The reversed string. Returns an empty string if input is None or empty.

    Example:
        >>> reverse("hello")
        'olleh'
        >>> reverse(None)
        ''
    """
    if not text:
        return ""
    try:
        return text[::-1]
    except Exception:
        # In case of unexpected errors (e.g., non-string input)
        return ""


def capitalize_words(text: Optional[str]) -> str:
    """
    Capitalize the first letter of each word in the given string.

    Words are split by spaces, capitalized, and rejoined with a single space.

    Args:
        text (Optional[str]): The string whose words need capitalization. Can be None.

    Returns:
        str: A string with each word capitalized. Returns an empty string if input is None or empty.

    Example:
        >>> capitalize_words("hello world")
        'Hello World'
        >>> capitalize_words("")
        ''
    """
    if not text:
        return ""
    try:
        words = text.split()
        capitalized_words = [word.capitalize() for word in words]
        return " ".join(capitalized_words)
    except Exception:
        return ""


def count_vowels(text: Optional[str]) -> int:
    """
    Count the number of vowels (a, e, i, o, u) in the given string, case-insensitive.

    Args:
        text (Optional[str]): The string to analyze. Can be None.

    Returns:
        int: The number of vowels found in the string. Returns 0 if input is None or empty.

    Example:
        >>> count_vowels("Hello World")
        3
        >>> count_vowels(None)
        0
    """
    if not text:
        return 0
    try:
        vowels = set("aeiouAEIOU")
        return sum(1 for char in text if char in vowels)
    except Exception:
        return 0
