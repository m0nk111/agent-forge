import pytest
from engine.utils.string_utils import capitalize_words, reverse_string, count_vowels

def test_capitalize_words_basic():
    """Test basic capitalization of words."""
    assert capitalize_words("hello world") == "Hello World"
    assert capitalize_words("python programming") == "Python Programming"

def test_capitalize_words_edge_cases():
    """Test edge cases for capitalization."""
    assert capitalize_words("") == ""
    assert capitalize_words("a") == "A"

def test_reverse_string_basic():
    """Test basic string reversal."""
    assert reverse_string("hello") == "olleh"
    assert reverse_string("hello world") == "dlrow olleh"

def test_reverse_string_edge_cases():
    """Test edge cases for string reversal."""
    assert reverse_string("") == ""
    assert reverse_string("a") == "a"

def test_count_vowels_basic():
    """Test basic vowel counting."""
    assert count_vowels("hello") == 2  # e, o
    assert count_vowels("aeiou") == 5
    
def test_count_vowels_edge_cases():
    """Test edge cases for vowel counting."""
    assert count_vowels("") == 0
    assert count_vowels("bcdfg") == 0
    assert count_vowels("HELLO") == 2  # E, O (case insensitive)
