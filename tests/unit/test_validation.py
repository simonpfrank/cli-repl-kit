"""Unit tests for validation system."""

import pytest
from cli_repl_kit.plugins.base import ValidationResult, CommandPlugin


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


class TestCommandPluginDefaults:
    """Test CommandPlugin default validation behavior."""

    def test_default_validation_config_empty(self):
        """Test that default validation config is empty dict."""

        class SimplePlugin(CommandPlugin):
            @property
            def name(self):
                return "simple"

            def register(self, cli, context_factory):
                pass

        plugin = SimplePlugin()
        assert plugin.get_validation_config() == {}

    def test_default_validate_returns_valid(self):
        """Test that default validate_command returns valid."""

        class SimplePlugin(CommandPlugin):
            @property
            def name(self):
                return "simple"

            def register(self, cli, context_factory):
                pass

        plugin = SimplePlugin()
        result = plugin.validate_command("test", ["arg1"], None)
        assert result.status == "valid"
        assert result.is_valid() is True

    def test_plugin_without_validation_works(self):
        """Test that plugins without validation overrides work correctly."""

        class LegacyPlugin(CommandPlugin):
            @property
            def name(self):
                return "legacy"

            def register(self, cli, context_factory):
                pass
            # No validation methods overridden

        plugin = LegacyPlugin()
        # Should have default behavior
        assert plugin.get_validation_config() == {}
        result = plugin.validate_command("any", [], None)
        assert result.is_valid() is True


class TestCommandPluginValidation:
    """Test CommandPlugin validation overrides."""

    def test_override_validation_config(self):
        """Test that plugins can override validation config."""

        class ValidatingPlugin(CommandPlugin):
            @property
            def name(self):
                return "validating"

            def register(self, cli, context_factory):
                pass

            def get_validation_config(self):
                return {
                    "deploy": "required",
                    "echo": "optional",
                }

        plugin = ValidatingPlugin()
        config = plugin.get_validation_config()
        assert config == {"deploy": "required", "echo": "optional"}

    def test_override_validate_method(self):
        """Test that plugins can override validate_command."""

        class ValidatingPlugin(CommandPlugin):
            @property
            def name(self):
                return "validating"

            def register(self, cli, context_factory):
                pass

            def validate_command(self, cmd_name, cmd_args, parsed_args):
                if cmd_name == "test" and cmd_args == ["invalid"]:
                    return ValidationResult(
                        status="invalid", message="Invalid argument"
                    )
                return ValidationResult(status="valid")

        plugin = ValidatingPlugin()
        # Valid command
        result = plugin.validate_command("test", ["valid"], None)
        assert result.is_valid() is True

        # Invalid command
        result = plugin.validate_command("test", ["invalid"], None)
        assert result.should_block() is True
        assert result.message == "Invalid argument"

    def test_validate_receives_correct_args(self):
        """Test that validate_command receives correct arguments."""
        received_args = {}

        class ValidatingPlugin(CommandPlugin):
            @property
            def name(self):
                return "validating"

            def register(self, cli, context_factory):
                pass

            def validate_command(self, cmd_name, cmd_args, parsed_args):
                received_args["cmd_name"] = cmd_name
                received_args["cmd_args"] = cmd_args
                received_args["parsed_args"] = parsed_args
                return ValidationResult(status="valid")

        plugin = ValidatingPlugin()
        plugin.validate_command("deploy", ["prod"], {"env": "prod"})

        assert received_args["cmd_name"] == "deploy"
        assert received_args["cmd_args"] == ["prod"]
        assert received_args["parsed_args"] == {"env": "prod"}
