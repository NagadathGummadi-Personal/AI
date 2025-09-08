"""Test cases for main.py module."""

from utils.main import hello_world


class TestMainModule:
    """Test cases for the main module functions."""

    def test_hello_world_returns_correct_sum(self):
        """Test that hello_world returns the correct sum of 1 + 2."""
        result = hello_world()
        assert result == 3

    def test_hello_world_return_type(self):
        """Test that hello_world returns an integer."""
        result = hello_world()
        assert isinstance(result, int)

    def test_hello_world_positive_result(self):
        """Test that hello_world returns a positive number."""
        result = hello_world()
        assert result > 0

    def test_hello_world_specific_calculation(self):
        """Test the specific calculation logic."""
        # Since we know the function adds 1 + 2, test this explicitly
        expected = 1 + 2
        actual = hello_world()
        assert actual == expected
