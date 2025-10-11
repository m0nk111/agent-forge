import pytest
from string_helper import capitalize_words, reverse_string

def test_capitalize_words_positive():
    """Test capitalization of words in a sentence."""
    assert capitalize_words("hello world") == "Hello World"
    assert capitalize_words("this is a test") == "This Is A Test"

def test_capitalize_words_empty_string():
    """Test capitalization of an empty string."""
    assert capitalize_words("") == ""

def test_capitalize_words_single_word():
    """Test capitalization of a single word."""
    assert capitalize_words("word") == "Word"

def test_capitalize_words_with_special_characters():
    """Test capitalization with special characters."""
    assert capitalize_words("hello, world!") == "Hello, World!"

def test_capitalize_words_with_numbers():
    """Test capitalization with numbers."""
    assert capitalize_words("123 hello 456") == "123 Hello 456"

def test_capitalize_words_with_uppercase():
    """Test capitalization of already capitalized words."""
    assert capitalize_words("Hello World") == "Hello World"

def test_reverse_string_positive():
    """Test reversing a string."""
    assert reverse_string("hello world") == "dlrow olleh"
    assert reverse_string("this is a test") == "tset a si siht"

def test_reverse_string_empty_string():
    """Test reversing an empty string."""
    assert reverse_string("") == ""

def test_reverse_string_single_character():
    """Test reversing a single character."""
    assert reverse_string("a") == "a"

def test_reverse_string_with_special_characters():
    """Test reversing a string with special characters."""
    assert reverse_string("hello, world!") == "!dlrow ,olleh"

def test_reverse_string_with_numbers():
    """Test reversing a string with numbers."""
    assert reverse_string("123 hello 456") == "654 olleh 321"

def test_reverse_string_with_uppercase():
    """Test reversing a string with uppercase letters."""
    assert reverse_string("Hello World") == "dlroW olleH"