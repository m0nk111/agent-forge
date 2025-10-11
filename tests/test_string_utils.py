import pytest
from string_utils import capitalize_words, reverse_string, count_vowels

def test_capitalize_words_positive():
    assert capitalize_words("hello world") == "Hello World"

def test_capitalize_words_leading_space():
    assert capitalize_words(" hello world") == " Hello World"

def test_capitalize_words_trailing_space():
    assert capitalize_words("hello world ") == "Hello World "

def test_capitalize_words_empty_string():
    assert capitalize_words("") == ""

def test_capitalize_words_single_word():
    assert capitalize_words("python") == "Python"

def test_capitalize_words_multiple_spaces():
    assert capitalize_words("   hello     world  ") == "   Hello     World  "

def test_capitalize_words_special_characters():
    assert capitalize_words("hello, world!") == "Hello, World!"

def test_capitalize_words_negative_not_string():
    with pytest.raises(ValueError):
        capitalize_words(123)

def test_reverse_string_positive():
    assert reverse_string("hello") == "olleh"

def test_reverse_string_leading_space():
    assert reverse_string(" hello") == " olleh"

def test_reverse_string_trailing_space():
    assert reverse_string("hello ") == " olleh"

def test_reverse_string_empty_string():
    assert reverse_string("") == ""

def test_reverse_string_single_char():
    assert reverse_string("a") == "a"

def test_reverse_string_multiple_spaces():
    assert reverse_string("   hello  ") == "  olleh   "

def test_reverse_string_special_characters():
    assert reverse_string("hello, world!") == "!dlrow ,olleh"

def test_reverse_string_negative_not_string():
    with pytest.raises(ValueError):
        reverse_string(123)

def test_count_vowels_positive():
    assert count_vowels("good morning") == 4

def test_count_vowels_empty_string():
    assert count_vowels("") == 0

def test_count_vowels_no_vowels():
    assert count_vowels("bcdfghjkl") == 0

def test_count_vowels_case_insensitive():
    assert count_vowels("AEIOUaeiou") == 10

def test_count_vowels_special_characters():
    assert count_vowels("hello, world!") == 3

def test_count_vowels_negative_not_string():
    with pytest.raises(ValueError):
        count_vowels(123)