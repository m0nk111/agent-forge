# engine/operations/string_utils.py

from typing import List, Tuple

def capitalize_words(text: str) -> str:
    """
    Capitalize the first letter of each word in the input string.

    Args:
        text (str): The input string to be processed.

    Returns:
        str: A new string with the first letter of each word capitalized.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    return ' '.join(word.capitalize() for word in text.split())

def reverse_string(text: str) -> str:
    """
    Reverse the input string.

    Args:
        text (str): The input string to be reversed.

    Returns:
        str: A new string that is the reverse of the input.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    return text[::-1]

def count_vowels(text: str) -> int:
    """
    Count the number of vowels (a, e, i, o, u) in the input string.

    Args:
        text (str): The input string to count vowels from.

    Returns:
        int: The total count of vowels in the input string.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    vowels = 'aeiouAEIOU'
    return sum(1 for char in text if char in vowels)

# Test suite using pytest
import pytest

def test_capitalize_words():
    assert capitalize_words('hello world') == 'Hello World'
    assert capitalize_words('python programming') == 'Python Programming'
    with pytest.raises(ValueError):
        capitalize_words(12345)

def test_reverse_string():
    assert reverse_string('hello') == 'olleh'
    assert reverse_string('world') == 'dlrow'
    with pytest.raises(ValueError):
        reverse_string(12345)

def test_count_vowels():
    assert count_vowels('hello world') == 3
    assert count_vowels('python programming') == 3
    assert count_vowels('AEIOU') == 5
    with pytest.raises(ValueError):
        count_vowels(12345)