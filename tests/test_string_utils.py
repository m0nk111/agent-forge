import pytest
from string_utils import capitalize_words, reverse_string, count_vowels

def test_capitalize_words_positive():
    assert capitalize_words("hello world") == "Hello World"

def test_capitalize_words_mixed_case():
    assert capitalize_words("hElLo wOrLD") == "Hello World"

def test_capitalize_words_single_word():
    assert capitalize_words("apple") == "Apple"

def test_capitalize_words_empty_string():
    assert capitalize_words("") == ""

def test_reverse_string_positive():
    assert reverse_string("hello world") == "dlrow olleh"

def test_reverse_string_mixed_case():
    assert reverse_string("hElLo wOrLD") == "DLRoW OLleH"

def test_reverse_string_single_word():
    assert reverse_string("apple") == "elppa"

def test_reverse_string_empty_string():
    assert reverse_string("") == ""

def test_count_vowels_positive():
    assert count_vowels("hello world") == 3

def test_count_vowels_mixed_case():
    assert count_vowels("hElLo wOrLD") == 3

def test_count_vowels_with_numbers():
    assert count_vowels("a1e2i3o4u5") == 5

def test_count_vowels_empty_string():
    assert count_vowels("") == 0

def test_count_vowels_no_vowels():
    assert count_vowels("bcdfghjklmnpqrstvwxyz") == 0