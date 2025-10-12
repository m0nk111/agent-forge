import pytest
from string_helper import capitalize_words, reverse_string

# Positive test cases for capitalize_words function
def test_capitalize_words_with_single_word():
    assert capitalize_words("hello") == "Hello"

def test_capitalize_words_with_multiple_words():
    assert capitalize_words("hello world") == "Hello World"

def test_capitalize_words_with_mixed_case():
    assert capitalize_words("hElLo wOrLD") == "Hello World"

# Negative test cases for capitalize_words function
def test_capitalize_words_with_non_string_input():
    with pytest.raises(TypeError):
        capitalize_words(123)

def test_capitalize_words_with_empty_string():
    assert capitalize_words("") == ""

# Positive test cases for reverse_string function
def test_reverse_string_with_single_word():
    assert reverse_string("hello") == "olleh"

def test_reverse_string_with_multiple_words():
    assert reverse_string("hello world") == "dlrow olleh"

def test_reverse_string_with_mixed_case():
    assert reverse_string("hElLo wOrLD") == "DLRoW OLLEh"

# Negative test cases for reverse_string function
def test_reverse_string_with_non_string_input():
    with pytest.raises(TypeError):
        reverse_string(123)

def test_reverse_string_with_empty_string():
    assert reverse_string("") == ""