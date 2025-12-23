"""Amount validation utilities.

Provides parsing and validation of transaction amounts.
"""
import re
from decimal import Decimal
from decimal import InvalidOperation
from typing import Optional
from typing import Union


class AmountValidationError(ValueError):
    """Exception raised when amount validation fails."""

    def __init__(self, message: str, amount_str: str):
        """Initialize validation error.

        Args:
            message: Error message
            amount_str: The invalid amount string
        """
        super().__init__(message)
        self.amount_str = amount_str


def parse_amount(amount_str: str) -> Decimal:
    """Parse amount string to Decimal, handling various formats.

    Supports:
    - Plain numbers: "500000", "1500000"
    - Comma separators: "1,500,000"
    - Dot separators: "1.500.000" (Indonesian format)
    - Mixed: "1,500.000"
    - With decimals: "1500000.50" (cents are rounded)

    Args:
        amount_str: Amount string to parse

    Returns:
        Parsed Decimal amount

    Raises:
        AmountValidationError: If amount cannot be parsed

    Examples:
        >>> parse_amount("500000")
        Decimal('500000')
        >>> parse_amount("1,500,000")
        Decimal('1500000')
        >>> parse_amount("1.500.000")
        Decimal('1500000')
    """
    if not amount_str or not amount_str.strip():
        raise AmountValidationError("Amount cannot be empty", amount_str)

    # Remove whitespace
    amount_str = amount_str.strip()

    # Remove currency symbols and text
    amount_str = re.sub(r"[Rp\s]", "", amount_str, flags=re.IGNORECASE)

    # Handle different separator formats
    # Check if dots are used as thousand separators (Indonesian format)
    if "." in amount_str and "," in amount_str:
        # Mixed format - remove both separators
        amount_str = amount_str.replace(",", "").replace(".", "")
    elif amount_str.count(".") > 1:
        # Multiple dots = thousand separators (e.g., "1.500.000")
        amount_str = amount_str.replace(".", "")
    elif "," in amount_str:
        # Comma as thousand separator (e.g., "1,500,000")
        amount_str = amount_str.replace(",", "")
    else:
        # Single dot could be decimal separator or nothing
        # If there are 1-2 digits after the dot, it's decimal
        # If there are 3+ digits, it's a thousand separator
        if "." in amount_str:
            parts = amount_str.split(".")
            if len(parts[-1]) > 2:
                # Thousand separator
                amount_str = amount_str.replace(".", "")

    # Try to convert to Decimal
    try:
        amount = Decimal(amount_str)
    except (InvalidOperation, ValueError) as e:
        raise AmountValidationError(f"Invalid amount format: '{amount_str}'", amount_str) from e

    # Round to 2 decimal places (Rupiah has no smaller unit, but handle decimals)
    amount = amount.quantize(Decimal("0.01"))

    return amount


def validate_amount(
    amount: Union[Decimal, str],
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
) -> Decimal:
    """Validate transaction amount against business rules.

    Args:
        amount: Amount to validate (Decimal or string)
        min_amount: Minimum allowed amount (default: 0.01)
        max_amount: Maximum allowed amount (default: from settings)

    Returns:
        Validated Decimal amount

    Raises:
        AmountValidationError: If validation fails

    Examples:
        >>> validate_amount("500000")
        Decimal('500000.00')
        >>> validate_amount("0")
        AmountValidationError: Amount must be greater than 0
        >>> validate_amount("999999999999")
        AmountValidationError: Amount exceeds maximum...
    """
    # Parse if string
    if isinstance(amount, str):
        amount = parse_amount(amount)

    # Set defaults
    if min_amount is None:
        min_amount = Decimal("0.01")
    if max_amount is None:
        from src.config.settings import get_settings

        max_amount = Decimal(str(get_settings().max_amount))

    # Validate minimum
    if amount <= 0:
        raise AmountValidationError("Amount must be greater than 0", str(amount))

    if amount < min_amount:
        raise AmountValidationError(f"Amount must be at least {min_amount}", str(amount))

    # Validate maximum (FR-022: max 10 billion)
    if amount > max_amount:
        from src.bot.utils.formatters import format_currency

        raise AmountValidationError(
            f"Amount exceeds maximum allowed: {format_currency(max_amount)}", str(amount)
        )

    return amount


def is_valid_amount(amount_str: str) -> bool:
    """Check if amount string is valid without raising exception.

    Args:
        amount_str: Amount string to check

    Returns:
        True if valid, False otherwise

    Examples:
        >>> is_valid_amount("500000")
        True
        >>> is_valid_amount("abc")
        False
        >>> is_valid_amount("0")
        False
    """
    try:
        validate_amount(amount_str)
        return True
    except AmountValidationError:
        return False


def get_validation_example() -> str:
    """Get example message for amount validation errors.

    Returns:
        Example usage string
    """
    return (
        "Valid formats:\n"
        "• 500000\n"
        "• 1,500,000\n"
        "• 1.500.000\n"
        "\n"
        "Example: /income 500000 Client payment"
    )
