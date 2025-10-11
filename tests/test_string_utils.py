import pytest
from string_utils import capitalize_words, reverse_string, count_vowels

def test_capitalize_words_positive():
    assert capitalize_words("hello world") == "Hello World"

def test_capitalize_words_multiple_words():
    assert capitalize_words("this is a test") == "This Is A Test"

def test_capitalize_words_single_word():
    assert capitalize_words("python") == "Python"

def test_capitalize_words_empty_string():
    assert capitalize_words("") == ""

def test_capitalize_words_with_numbers():
    assert capitalize_words("hello123") == "Hello123"

def test_capitalize_words_with_special_chars():
    assert capitalize_words("hello!@#") == "Hello!@#"

def test_capitalize_words_with_leading_and_trailing_spaces():
    assert capitalize_words("  hello world  ") == "  Hello World  "

def test_capitalize_words_mixed_case():
    assert capitalize_words("hElLo wOrLd") == "HElLO WoRlD"

def test_reverse_string_positive():
    assert reverse_string("hello") == "olleh"

def test_reverse_string_multiple_words():
    assert reverse_string("hello world") == "dlrow olleh"

def test_reverse_string_single_word():
    assert reverse_string("python") == "nohtyp"

def test_reverse_string_empty_string():
    assert reverse_string("") == ""

def test_reverse_string_with_numbers():
    assert reverse_string("12345") == "54321"

def test_reverse_string_with_special_chars():
    assert reverse_string("!@#$%") == "%$#@!"

def test_reverse_string_with_leading_and_trailing_spaces():
    assert reverse_string("  hello world  ") == "  dlrow olleh  "

def test_count_vowels_positive():
    assert count_vowels("hello world") == 3

def test_count_vowels_multiple_words():
    assert count_vowels("this is a test") == 4

def test_count_vowels_single_word():
    assert count_vowels("python") == 1

def test_count_vowels_empty_string():
    assert count_vowels("") == 0

def test_count_vowels_with_numbers():
    assert count_vowels("12345") == 0

def test_count_vowels_with_special_chars():
    assert count_vowels("!@#$%") == 0

def test_count_vowels_with_leading_and_trailing_spaces():
    assert count_vowels("  hello world  ") == 3

def test_count_vowels_mixed_case():
    assert count_vowels("hElLo wOrLd") == 4

def test_capitalize_words_error_handling():
    with pytest.raises(ValueError):
        capitalize_words(123)

def test_reverse_string_error_handling():
    with pytest.raises(ValueError):
        reverse_string(123)

def test_count_vowels_error_handling():
    with pytest.raises(ValueError):
        count_vowels(123)