def reverse_string(s):
    """
    Reverses the given string.

    Args:
        s (str): The string to be reversed.

    Returns:
        str: The reversed string.
    """
    return s[::-1]

def capitalize_words(s):
    """
    Capitalizes the first letter of each word in the string, preserving spacing.

    Args:
        s (str): The string to capitalize.

    Returns:
        str: The string with each word capitalized, preserving original spacing.
    """
    if not s:
        return s
    
    result = []
    i = 0
    while i < len(s):
        # Preserve leading/trailing spaces and multiple spaces
        if s[i].isspace():
            result.append(s[i])
            i += 1
        else:
            # Find the word
            word_start = i
            while i < len(s) and not s[i].isspace():
                i += 1
            word = s[word_start:i]
            # Capitalize first letter, lowercase the rest
            if word:
                result.append(word[0].upper() + word[1:].lower())
    
    return ''.join(result)

def is_palindrome(s):
    """
    Checks if the given string is a palindrome.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string is a palindrome, False otherwise.
    """
    return s == s[::-1]

def count_vowels(s):
    """
    Counts the number of vowels in the given string.

    Args:
        s (str): The string to analyze.

    Returns:
        int: The number of vowels in the string.
    """
    vowels = "aeiouAEIOU"
    return sum(1 for char in s if char in vowels)

def contains_digit(s):
    """
    Checks if the given string contains any digit.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string contains a digit, False otherwise.
    """
    return any(char.isdigit() for char in s)