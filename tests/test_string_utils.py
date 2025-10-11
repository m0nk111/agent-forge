import pytest
from engine.operations.string_utils import capitalize_words, reverse_string, count_vowels

def test_capitalize_words_positive():
    assert capitalize_words("hello world") == "Hello World"
    assert capitalize_words("good morning") == "Good Morning"

def test_capitalize_words_negative():
    assert capitalize_words("") == ""
    assert capitalize_words("12345") == "12345"

def test_capitalize_words_edge_case():
    assert capitalize_words("a") == "A"
    assert capitalize_words(" ") == ""  # split() removes whitespace-only strings

def test_reverse_string_positive():
    assert reverse_string("hello world") == "dlrow olleh"
    assert reverse_string("good morning") == "gninrom doog"  # Reverses exactly, maintains case

def test_reverse_string_negative():
    assert reverse_string("") == ""
    assert reverse_string("12345") == "54321"

def test_reverse_string_edge_case():
    assert reverse_string("a") == "a"
    assert reverse_string(" ") == " "

def test_count_vowels_positive():
    assert count_vowels("hello world") == 3  # e, o, o
    assert count_vowels("good morning") == 4  # o, o, o, i

def test_count_vowels_negative():
    assert count_vowels("") == 0
    assert count_vowels("12345") == 0

def test_count_vowels_edge_case():
    assert count_vowels("aeiou") == 5
    assert count_vowels("bcdfg") == 0