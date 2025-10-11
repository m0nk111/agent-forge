import pytest
from engine.utils.string_utils import capitalize_words, reverse_string, count_vowels

# Test cases for the capitalize_words function
def test_capitalize_words_positive():
    assert capitalize_words("hello world") == "Hello World"

def test_capitalize_words_empty_string():
    assert capitalize_words("") == ""

def test_capitalize_words_all_uppercase():
    assert capitalize_words("HELLO WORLD") == "Hello World"

def test_capitalize_words_single_word():
    assert capitalize_words("apple") == "Apple"

# Test cases for the reverse_string function
def test_reverse_string_positive():
    assert reverse_string("hello world") == "dlrow olleh"

def test_reverse_string_empty_string():
    assert reverse_string("") == ""

def test_reverse_string_all_uppercase():
    assert reverse_string("HELLO WORLD") == "DLROW OLLEH"

def test_reverse_string_single_word():
    assert reverse_string("apple") == "elppa"

# Test cases for the count_vowels function
def test_count_vowels_positive():
    assert count_vowels("good morning") == 4

def test_count_vowels_empty_string():
    assert count_vowels("") == 0

def test_count_vowels_all_consonants():
    assert count_vowels("bcdfghjklmnpqrstvwxyz") == 0

def test_count_vowels_single_vowel():
    assert count_vowels("a") == 1

# Test cases for the count_vowels function with mixed case
def test_count_vowels_mixed_case():
    assert count_vowels("AeIoU") == 5