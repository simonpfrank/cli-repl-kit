"""Unit tests for validation system.

NOTE: Tests for automatic validation are in test_auto_validation.py.
This file only tests the ValidationResult dataclass which is still used internally.
"""

from cli_repl_kit.plugins.base import ValidationResult


class TestValidationResult:
    """Test ValidationResult class."""

    def test_valid_status_is_valid(self):
        """Test that valid status returns is_valid True."""
        result = ValidationResult(status="valid")
        assert result.is_valid() is True
        assert result.should_block() is False
        assert result.should_warn() is False

    def test_invalid_status_should_block(self):
        """Test that invalid status returns should_block True."""
        result = ValidationResult(status="invalid", message="Test error")
        assert result.is_valid() is False
        assert result.should_block() is True
        assert result.should_warn() is False

    def test_warning_status_should_warn(self):
        """Test that warning status returns should_warn True."""
        result = ValidationResult(status="warning", message="Test warning")
        assert result.should_warn() is True
        assert result.should_block() is False

    def test_warning_status_is_valid(self):
        """Test that warning status is still considered valid (doesn't block)."""
        result = ValidationResult(status="warning")
        assert result.is_valid() is True

    def test_message_optional(self):
        """Test that message is optional."""
        result = ValidationResult(status="valid")
        assert result.message is None

        result_with_msg = ValidationResult(status="invalid", message="Error")
        assert result_with_msg.message == "Error"
