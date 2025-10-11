"""Module containing common string manipulation utilities."""

import re

def capitalize_words(text: str) -> str:
    """
    Capitalize the first letter of each word in the input text.

    Args:
        text (str): The input text to be processed.

    Returns:
        str: The text with the first letter of each word capitalized.
    """
    return ' '.join(word.capitalize() for word in text.split())

def reverse_string(text: str) -> str:
    """
    Reverse the input string.

    Args:
        text (str): The input text to be processed.

    Returns:
        str: The reversed version of the input text.
    """
    return text[::-1]

def count_vowels(text: str) -> int:
    """
    Count the number of vowels (a, e, i, o, u) in the input text.

    Args:
        text (str): The input text to be processed.

    Returns:
        int: The number of vowels found in the input text.
    """
    return len(re.findall(r'[aeiouAEIOU]', text))