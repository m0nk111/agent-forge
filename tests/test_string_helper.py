import pytest
from string_helper import capitalize_words, reverse_string

def test_capitalize_words_normal():
    """Test capitalizing words in a normal sentence."""
    assert capitalize_words("hello world") == "Hello World"

def test_capitalize_words_multiple_spaces():
    """Test capitalizing words with multiple spaces between them."""
    assert capitalize_words("   hello   world   ") == "   Hello   World   "

def test_capitalize_words_single_word():
    """Test capitalizing a single word."""
    assert capitalize_words("python") == "Python"

def test_capitalize_words_empty_string():
    """Test capitalizing an empty string."""
    assert capitalize_words("") == ""

def test_capitalize_words_with_special_characters():
    """Test capitalizing words with special characters."""
    assert capitalize_words("hello, world!") == "Hello, World!"

def test_capitalize_words_with_numbers():
    """Test capitalizing words with numbers."""
    assert capitalize_words("123 hello 456") == "123 Hello 456"

def test_reverse_string_normal():
    """Test reversing a normal string."""
    assert reverse_string("hello world") == "dlrow olleh"

def test_reverse_string_empty_string():
    """Test reversing an empty string."""
    assert reverse_string("") == ""

def test_reverse_string_with_special_characters():
    """Test reversing a string with special characters."""
    assert reverse_string("hello, world!") == "!dlrow ,olleh"

def test_reverse_string_with_numbers():
    """Test reversing a string with numbers."""
    assert reverse_string("123 hello 456") == "654 olleh 321"

def test_capitalize_words_error_handling():
    """Test error handling for non-string input."""
    with pytest.raises(ValueError):
        capitalize_words(123)

def test_reverse_string_error_handling():
    """Test error handling for non-string input."""
    with pytest.raises(ValueError):
        reverse_string(123)