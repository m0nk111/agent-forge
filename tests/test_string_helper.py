import pytest
from utils.string_helper import capitalize_words, reverse_string

def test_capitalize_words_positive():
    assert capitalize_words("hello world") == "Hello World"
    assert capitalize_words("this is a test") == "This Is A Test"

def test_capitalize_words_handles_empty_strings():
    assert capitalize_words("") == ""

def test_capitalize_words_handles_single_word():
    assert capitalize_words("single") == "Single"

def test_capitalize_words_raises_value_error_on_non_string_input():
    with pytest.raises(ValueError):
        capitalize_words(123)
    with pytest.raises(ValueError):
        capitalize_words(None)

def test_reverse_string_positive():
    assert reverse_string("hello world") == "dlrow olleh"
    assert reverse_string("this is a test") == "tset a si siht"

def test_reverse_string_handles_empty_strings():
    assert reverse_string("") == ""

def test_reverse_string_handles_single_character():
    assert reverse_string("a") == "a"

def test_reverse_string_raises_value_error_on_non_string_input():
    with pytest.raises(ValueError):
        reverse_string(123)
    with pytest.raises(ValueError):
        reverse_string(None)