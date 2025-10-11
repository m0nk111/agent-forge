import pytest
from string_utils import capitalize_words, reverse_string, count_vowels

def test_capitalize_words_positive():
    assert capitalize_words("hello world") == "Hello World"

def test_capitalize_words_leading_spaces():
    assert capitalize_words(" hello world") == " Hello World"

def test_capitalize_words_trailing_spaces():
    assert capitalize_words("hello world ") == "Hello World "

def test_capitalize_words_multiple_spaces():
    assert capitalize_words("hello   world") == "Hello   World"

def test_capitalize_words_all_uppercase():
    assert capitalize_words("HELLO WORLD") == "Hello World"

def test_capitalize_words_empty_string():
    assert capitalize_words("") == ""

def test_reverse_string_positive():
    assert reverse_string("hello world") == "dlrow olleh"

def test_reverse_string_mixed_case():
    assert reverse_string("HeLlO wOrLD") == "DLRoW OLLEh"

def test_reverse_string_empty_string():
    assert reverse_string("") == ""

def test_count_vowels_positive():
    assert count_vowels("good morning") == 4

def test_count_vowels_mixed_case():
    assert count_vowels("HeLlO wOrLD") == 3

def test_count_vowels_with_punctuation():
    assert count_vowels("a, e, i, o, u!") == 5

def test_count_vowels_empty_string():
    assert count_vowels("") == 0