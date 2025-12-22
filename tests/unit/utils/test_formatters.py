"""Unit tests for currency formatters and transaction ID generation."""
from datetime import date
from decimal import Decimal

import pytest

from bot.utils.formatters import format_currency
from bot.utils.formatters import format_currency_with_sign
from bot.utils.formatters import generate_transaction_id
from bot.utils.formatters import parse_transaction_id


class TestFormatCurrency:
    """Test currency formatting for Indonesian Rupiah."""

    def test_format_integer_amount(self):
        """Should format integer amounts with thousand separators."""
        assert format_currency(1500000) == "Rp 1,500,000"
        assert format_currency(500000) == "Rp 500,000"
        assert format_currency(1000) == "Rp 1,000"

    def test_format_decimal_amount(self):
        """Should round decimal amounts to whole rupiah."""
        assert format_currency(Decimal("1500000.50")) == "Rp 1,500,000"
        assert format_currency(Decimal("1500000.99")) == "Rp 1,500,001"
        assert format_currency(Decimal("250000.49")) == "Rp 250,000"

    def test_format_zero(self):
        """Should format zero correctly."""
        assert format_currency(0) == "Rp 0"
        assert format_currency(Decimal("0")) == "Rp 0"

    def test_format_large_amounts(self):
        """Should format large amounts correctly."""
        assert format_currency(10000000000) == "Rp 10,000,000,000"
        assert format_currency(1000000) == "Rp 1,000,000"

    def test_format_small_amounts(self):
        """Should format small amounts correctly."""
        assert format_currency(100) == "Rp 100"
        assert format_currency(1) == "Rp 1"


class TestFormatCurrencyWithSign:
    """Test currency formatting with explicit sign."""

    def test_format_positive_amount(self):
        """Should add plus sign for positive amounts."""
        assert format_currency_with_sign(1500000) == "+Rp 1,500,000"
        assert format_currency_with_sign(Decimal("500000")) == "+Rp 500,000"

    def test_format_negative_amount(self):
        """Should add minus sign for negative amounts."""
        assert format_currency_with_sign(-1500000) == "-Rp 1,500,000"
        assert format_currency_with_sign(Decimal("-500000")) == "-Rp 500,000"

    def test_format_zero(self):
        """Should format zero without sign."""
        assert format_currency_with_sign(0) == "Rp 0"
        assert format_currency_with_sign(Decimal("0")) == "Rp 0"


class TestGenerateTransactionId:
    """Test transaction ID generation with TX20251218001 format."""

    def test_generate_id_format(self):
        """Should generate ID with correct format: TX{YYYYMMDD}{NNN}."""
        tx_id = generate_transaction_id(date(2025, 12, 18), 1)
        assert tx_id == "TX20251218001"

        tx_id = generate_transaction_id(date(2025, 12, 18), 42)
        assert tx_id == "TX20251218042"

    def test_generate_id_sequence_padding(self):
        """Should pad sequence number with leading zeros (3 digits)."""
        assert generate_transaction_id(date(2025, 12, 18), 1) == "TX20251218001"
        assert generate_transaction_id(date(2025, 12, 18), 10) == "TX20251218010"
        assert generate_transaction_id(date(2025, 12, 18), 100) == "TX20251218100"

    def test_generate_id_different_dates(self):
        """Should handle different dates correctly."""
        assert generate_transaction_id(date(2025, 1, 1), 1) == "TX20250101001"
        assert generate_transaction_id(date(2025, 12, 31), 999) == "TX20251231999"
        assert generate_transaction_id(date(2026, 6, 15), 50) == "TX20260615050"

    def test_generate_id_sequence_numbers(self):
        """Should handle various sequence numbers."""
        # First transaction of the day
        assert generate_transaction_id(date(2025, 12, 18), 1) == "TX20251218001"

        # Mid-day transaction
        assert generate_transaction_id(date(2025, 12, 18), 150) == "TX20251218150"

        # High-volume day
        assert generate_transaction_id(date(2025, 12, 18), 999) == "TX20251218999"

    def test_generate_id_consistency(self):
        """Should generate same ID for same inputs."""
        test_date = date(2025, 12, 18)
        tx_id_1 = generate_transaction_id(test_date, 42)
        tx_id_2 = generate_transaction_id(test_date, 42)
        assert tx_id_1 == tx_id_2


class TestParseTransactionId:
    """Test transaction ID parsing."""

    def test_parse_valid_id(self):
        """Should parse valid transaction IDs correctly."""
        parsed_date, sequence = parse_transaction_id("TX20251218001")
        assert parsed_date == date(2025, 12, 18)
        assert sequence == 1

        parsed_date, sequence = parse_transaction_id("TX20251218042")
        assert parsed_date == date(2025, 12, 18)
        assert sequence == 42

    def test_parse_different_dates(self):
        """Should parse various dates correctly."""
        parsed_date, sequence = parse_transaction_id("TX20250101001")
        assert parsed_date == date(2025, 1, 1)
        assert sequence == 1

        parsed_date, sequence = parse_transaction_id("TX20251231999")
        assert parsed_date == date(2025, 12, 31)
        assert sequence == 999

    def test_parse_invalid_format(self):
        """Should raise error for invalid transaction ID format."""
        with pytest.raises(ValueError):
            parse_transaction_id("INVALID")

        with pytest.raises(ValueError):
            parse_transaction_id("TX2025121801")  # Wrong length

        with pytest.raises(ValueError):
            parse_transaction_id("20251218001")  # Missing TX prefix

    def test_parse_invalid_date(self):
        """Should raise error for invalid date in transaction ID."""
        with pytest.raises(ValueError):
            parse_transaction_id("TX20251399001")  # Invalid month

        with pytest.raises(ValueError):
            parse_transaction_id("TX20250230001")  # Invalid date (Feb 30)

    def test_roundtrip_consistency(self):
        """Should maintain consistency in generate -> parse -> generate cycle."""
        original_date = date(2025, 12, 18)
        original_seq = 42

        # Generate ID
        tx_id = generate_transaction_id(original_date, original_seq)

        # Parse it back
        parsed_date, parsed_seq = parse_transaction_id(tx_id)

        # Should match original
        assert parsed_date == original_date
        assert parsed_seq == original_seq

        # Generate again - should get same ID
        regenerated_id = generate_transaction_id(parsed_date, parsed_seq)
        assert regenerated_id == tx_id
