'''Utility module for string manipulation functions.'''

from typing import Optional

def capitalize_words(text: str) -> str:
    '''Capitalizes each word in the provided text.
    
    Args:
        text (str): The input text to be processed.

    Returns:
        str: A new string with each word capitalized.

    Raises:
        ValueError: If the input is not a string.
    '''
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    return ' '.join(word.capitalize() for word in text.split())

def reverse_string(text: str) -> str:
    '''Reverses the provided text.
    
    Args:
        text (str): The input text to be processed.

    Returns:
        str: A new string that is the reverse of the input.

    Raises:
        ValueError: If the input is not a string.
    '''
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    return text[::-1]