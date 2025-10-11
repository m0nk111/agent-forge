import pytest
from string_helper import capitalize_words, reverse_string

def test_capitalize_words_positive():
    assert capitalize_words("hello world") == "Hello World"
    assert capitalize_words("capitalize these words") == "Capitalize These Words"

def test_capitalize_words_empty_string():
    assert capitalize_words("") == ""

def test_capitalize_words_single_word():
    assert capitalize_words("word") == "Word"

def test_capitalize_words_mixed_case():
    assert capitalize_words("hElLo wOrLd") == "Hello World"

def test_capitalize_words_with_punctuation():
    assert capitalize_words("hello, world!") == "Hello, World!"

def test_capitalize_words_with_numbers():
    assert capitalize_words("123 hello 456") == "123 Hello 456"

def test_capitalize_words_with_special_characters():
    assert capitalize_words("hello@world") == "Hello@World"

def test_reverse_string_positive():
    assert reverse_string("hello world") == "dlrow olleh"
    assert reverse_string("reverse this string") == "gnirts siht esrever"

def test_reverse_string_empty_string():
    assert reverse_string("") == ""

def test_reverse_string_single_character():
    assert reverse_string("a") == "a"

def test_reverse_string_with_punctuation():
    assert reverse_string("hello, world!") == "!dlrow ,olleh"

def test_reverse_string_with_numbers():
    assert reverse_string("12345") == "54321"

def test_reverse_string_with_special_characters():
    assert reverse_string("hello@world") == "dlrow@olleh"

def test_capitalize_words_raises_error_on_non_string_input():
    with pytest.raises(ValueError) as excinfo:
        capitalize_words(123)
    assert str(excinfo.value) == "Input must be a string"

def test_reverse_string_raises_error_on_non_string_input():
    with pytest.raises(ValueError) as excinfo:
        reverse_string(123)
    assert str(excinfo.value) == "Input must be a string"