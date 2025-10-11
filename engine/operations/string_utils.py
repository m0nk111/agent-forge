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

def extract_substrings(text: str, start_index: int, end_index: int) -> List[str]:
    """
    Extract substrings from the input string based on specified indices.

    Args:
        text (str): The input string to extract substrings from.
        start_index (int): The starting index for each substring.
        end_index (int): The ending index for each substring.

    Returns:
        List[str]: A list of substrings extracted from the input string.
    """
    if not isinstance(text, str) or not isinstance(start_index, int) or not isinstance(end_index, int):
        raise ValueError("Input must be a string and indices must be integers")
    
    return [text[start:end] for start, end in zip(start_index, end_index)]

def remove_punctuation(text: str) -> str:
    """
    Remove all punctuation from the input string.

    Args:
        text (str): The input string to remove punctuation from.

    Returns:
        str: A new string with all punctuation removed.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    import string
    return ''.join(char for char in text if char not in string.punctuation)

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

def test_extract_substrings():
    assert extract_substrings('hello world', [0, 6], [5, 11]) == ['hello', 'world']
    assert extract_substrings('python programming', [7, 8], [15, 21]) == ['programming']
    with pytest.raises(ValueError):
        extract_substrings('test', [0], [3])

def test_remove_punctuation():
    assert remove_punctuation('Hello, World!') == 'Hello World'
    assert remove_punctuation('Python 3.8') == 'Python 38'
    assert remove_punctuation('No punctuation here') == 'No punctuation here'