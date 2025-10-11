"""Tests for calculator module.

Test suite for basic arithmetic operations in the calculator module.
Tests all four basic operations: add, subtract, multiply, divide.
"""

import pytest
from engine.utils.calculator import add, subtract, multiply, divide


class TestAdd:
    """Tests for the add function."""
    
    def test_add_positive_numbers(self):
        """Test adding two positive numbers."""
        assert add(2, 3) == 5.0
        assert add(10, 20) == 30.0
    
    def test_add_negative_numbers(self):
        """Test adding negative numbers."""
        assert add(-1, -1) == -2.0
        assert add(-5, -10) == -15.0
    
    def test_add_mixed_signs(self):
        """Test adding numbers with different signs."""
        assert add(-1, 1) == 0.0
        assert add(5, -3) == 2.0
    
    def test_add_decimals(self):
        """Test adding decimal numbers."""
        assert add(2.5, 3.5) == 6.0
        assert add(1.1, 2.2) == pytest.approx(3.3)
    
    def test_add_zero(self):
        """Test adding zero."""
        assert add(5, 0) == 5.0
        assert add(0, 5) == 5.0
        assert add(0, 0) == 0.0


class TestSubtract:
    """Tests for the subtract function."""
    
    def test_subtract_positive_numbers(self):
        """Test subtracting positive numbers."""
        assert subtract(5, 3) == 2.0
        assert subtract(10, 5) == 5.0
    
    def test_subtract_result_negative(self):
        """Test subtraction resulting in negative."""
        assert subtract(3, 5) == -2.0
        assert subtract(10, 15) == -5.0
    
    def test_subtract_negative_numbers(self):
        """Test subtracting negative numbers."""
        assert subtract(-5, -3) == -2.0
        assert subtract(-3, -5) == 2.0
    
    def test_subtract_decimals(self):
        """Test subtracting decimal numbers."""
        assert subtract(10.5, 2.5) == 8.0
        assert subtract(5.5, 2.3) == pytest.approx(3.2)
    
    def test_subtract_zero(self):
        """Test subtracting zero."""
        assert subtract(5, 0) == 5.0
        assert subtract(0, 5) == -5.0


class TestMultiply:
    """Tests for the multiply function."""
    
    def test_multiply_positive_numbers(self):
        """Test multiplying positive numbers."""
        assert multiply(4, 3) == 12.0
        assert multiply(5, 5) == 25.0
    
    def test_multiply_negative_numbers(self):
        """Test multiplying negative numbers."""
        assert multiply(-2, -3) == 6.0
        assert multiply(-4, -5) == 20.0
    
    def test_multiply_mixed_signs(self):
        """Test multiplying numbers with different signs."""
        assert multiply(-2, 3) == -6.0
        assert multiply(4, -5) == -20.0
    
    def test_multiply_decimals(self):
        """Test multiplying decimal numbers."""
        assert multiply(2.5, 4) == 10.0
        assert multiply(1.5, 2.5) == 3.75
    
    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        assert multiply(5, 0) == 0.0
        assert multiply(0, 5) == 0.0
        assert multiply(0, 0) == 0.0
    
    def test_multiply_by_one(self):
        """Test multiplying by one."""
        assert multiply(5, 1) == 5.0
        assert multiply(1, 5) == 5.0


class TestDivide:
    """Tests for the divide function."""
    
    def test_divide_positive_numbers(self):
        """Test dividing positive numbers."""
        assert divide(10, 2) == 5.0
        assert divide(15, 3) == 5.0
    
    def test_divide_result_decimal(self):
        """Test division resulting in decimal."""
        assert divide(7, 2) == 3.5
        assert divide(5, 4) == 1.25
    
    def test_divide_negative_numbers(self):
        """Test dividing negative numbers."""
        assert divide(-10, -2) == 5.0
        assert divide(-15, -3) == 5.0
    
    def test_divide_mixed_signs(self):
        """Test dividing numbers with different signs."""
        assert divide(-10, 2) == -5.0
        assert divide(10, -2) == -5.0
    
    def test_divide_decimals(self):
        """Test dividing decimal numbers."""
        assert divide(10.5, 2) == 5.25
        assert divide(7.5, 2.5) == 3.0
    
    def test_divide_by_one(self):
        """Test dividing by one."""
        assert divide(5, 1) == 5.0
        assert divide(10, 1) == 10.0
    
    def test_divide_by_zero_raises_error(self):
        """Test that division by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(10, 0)
        
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(0, 0)
        
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(-5, 0)


class TestIntegration:
    """Integration tests combining multiple operations."""
    
    def test_combined_operations(self):
        """Test combining multiple operations."""
        # (10 + 5) * 2 / 3 - 1 = 15 * 2 / 3 - 1 = 30 / 3 - 1 = 10 - 1 = 9
        result = add(10, 5)
        result = multiply(result, 2)
        result = divide(result, 3)
        result = subtract(result, 1)
        assert result == 9.0
    
    def test_order_doesnt_matter_for_add_multiply(self):
        """Test commutative property of addition and multiplication."""
        assert add(3, 5) == add(5, 3)
        assert multiply(4, 6) == multiply(6, 4)
    
    def test_distributive_property(self):
        """Test distributive property: a * (b + c) = a*b + a*c."""
        a, b, c = 2.0, 3.0, 4.0
        left_side = multiply(a, add(b, c))
        right_side = add(multiply(a, b), multiply(a, c))
        assert left_side == right_side
