"""Unit tests for amount validation utilities."""
from decimal import Decimal

import pytest

from src.bot.utils.validators import AmountValidationError
from src.bot.utils.validators import parse_amount
from src.bot.utils.validators import validate_amount


class TestParseAmount:
    """Test amount parsing from various string formats."""

    def test_parse_plain_number(self):
        """Should parse plain numeric strings."""
        assert parse_amount("500000") == Decimal("500000")
        assert parse_amount("1500000") == Decimal("1500000")
        assert parse_amount("100") == Decimal("100")

    def test_parse_comma_separator(self):
        """Should parse amounts with comma thousands separators."""
        assert parse_amount("500,000") == Decimal("500000")
        assert parse_amount("1,500,000") == Decimal("1500000")
        assert parse_amount("10,000,000") == Decimal("10000000")

    def test_parse_dot_separator_indonesian(self):
        """Should parse amounts with dot thousands separators (Indonesian format)."""
        assert parse_amount("500.000") == Decimal("500000")
        assert parse_amount("1.500.000") == Decimal("1500000")
        assert parse_amount("10.000.000") == Decimal("10000000")

    def test_parse_mixed_separators(self):
        """Should handle mixed comma and dot separators."""
        assert parse_amount("1,500.000") == Decimal("1500000")

    def test_parse_with_decimals(self):
        """Should handle decimal values (round to whole rupiah)."""
        result = parse_amount("1500000.50")
        # Rounds to 2 decimal places
        assert result == Decimal("1500000.50")

    def test_parse_with_whitespace(self):
        """Should handle leading/trailing whitespace."""
        assert parse_amount("  500000  ") == Decimal("500000")
        assert parse_amount(" 1,500,000 ") == Decimal("1500000")

    def test_parse_invalid_non_numeric(self):
        """Should raise error for non-numeric strings."""
        with pytest.raises(AmountValidationError) as exc_info:
            parse_amount("abc")
        assert "abc" in str(exc_info.value)

    def test_parse_invalid_special_chars(self):
        """Should raise error for strings with invalid special characters."""
        with pytest.raises(AmountValidationError):
            parse_amount("500@000")
        with pytest.raises(AmountValidationError):
            parse_amount("500#000")

    def test_parse_empty_string(self):
        """Should raise error for empty string."""
        with pytest.raises(AmountValidationError):
            parse_amount("")

    def test_parse_negative_number(self):
        """Should parse negative numbers (validation happens separately)."""
        assert parse_amount("-500000") == Decimal("-500000")


class TestValidateAmount:
    """Test amount validation logic."""

    def test_validate_positive_amount(self):
        """Should accept positive amounts."""
        # Should not raise
        validate_amount(Decimal("500000"))
        validate_amount(Decimal("1"))
        validate_amount(Decimal("9999999999"))

    def test_validate_zero_rejected(self):
        """Should reject zero amount."""
        with pytest.raises(AmountValidationError) as exc_info:
            validate_amount(Decimal("0"))
        assert "greater than 0" in str(exc_info.value).lower()

    def test_validate_negative_rejected(self):
        """Should reject negative amounts."""
        with pytest.raises(AmountValidationError) as exc_info:
            validate_amount(Decimal("-500000"))
        assert "greater than 0" in str(exc_info.value).lower()

    def test_validate_max_limit_10_billion(self):
        """Should enforce maximum limit of Rp 10,000,000,000."""
        # Just under limit - should pass
        validate_amount(Decimal("10000000000"))

        # Exactly at limit - should pass
        validate_amount(Decimal("10000000000"))

        # Over limit - should fail
        with pytest.raises(AmountValidationError) as exc_info:
            validate_amount(Decimal("10000000001"))
        assert "maximum allowed" in str(exc_info.value).lower()

    def test_validate_max_limit_edge_cases(self):
        """Should handle edge cases around maximum limit."""
        # 10.1 billion - should fail
        with pytest.raises(AmountValidationError):
            validate_amount(Decimal("10100000000"))

        # 100 billion - should fail
        with pytest.raises(AmountValidationError):
            validate_amount(Decimal("100000000000"))


class TestParseAndValidate:
    """Test combined parsing and validation workflows."""

    def test_valid_input_formats(self):
        """Should successfully parse and validate valid inputs."""
        test_cases = [
            ("500000", Decimal("500000")),
            ("1,500,000", Decimal("1500000")),
            ("1.500.000", Decimal("1500000")),
            ("10000000000", Decimal("10000000000")),  # Max limit
        ]

        for input_str, expected in test_cases:
            parsed = parse_amount(input_str)
            assert parsed == expected
            # Should not raise on validation
            validate_amount(parsed)

    def test_invalid_input_formats(self):
        """Should reject invalid inputs at parsing stage."""
        test_cases = ["abc", "500abc", "", "   "]

        for input_str in test_cases:
            with pytest.raises(AmountValidationError):
                parse_amount(input_str)

    def test_invalid_amounts_after_parsing(self):
        """Should reject invalid amounts at validation stage."""
        test_cases = ["0", "-500000", "10000000001"]

        for input_str in test_cases:
            parsed = parse_amount(input_str)
            with pytest.raises(AmountValidationError):
                validate_amount(parsed)
