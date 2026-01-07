"""Unit tests for CommandExecutor module."""
from unittest.mock import Mock
from pathlib import Path

import click
import pytest

from cli_repl_kit.core.command_executor import CommandExecutor
from cli_repl_kit.core.config import Config
from cli_repl_kit.plugins.base import ValidationResult


class TestCommandExecutor:
    """Test CommandExecutor class."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create a test config."""
        config_file = tmp_path / "config.yaml"
        return Config.load(str(config_file))

    @pytest.fixture
    def cli_group(self):
        """Create a test CLI group."""
        cli = click.Group()

        @cli.command()
        @click.argument("name")
        def greet(name):
            """Greet someone."""
            print(f"Hello {name}")

        @cli.command()
        def simple():
            """Simple command."""
            print("Simple output")

        # Add group command
        config_group = click.Group(name="config")

        @config_group.command()
        @click.argument("key")
        def get(key):
            """Get config value."""
            print(f"Config: {key}")

        cli.add_command(config_group)

        return cli

    @pytest.fixture
    def executor(self, config, cli_group):
        """Create a CommandExecutor for testing."""
        validate_callback = Mock(return_value=(ValidationResult(status="valid"), None))
        append_output = Mock()

        return CommandExecutor(
            config=config,
            cli=cli_group,
            validate_callback=validate_callback,
            append_output_callback=append_output,
        )

    def test_initialization(self, config, cli_group):
        """Test CommandExecutor initializes correctly."""
        validate_cb = Mock()
        append_cb = Mock()

        executor = CommandExecutor(
            config=config,
            cli=cli_group,
            validate_callback=validate_cb,
            append_output_callback=append_cb,
        )

        assert executor.config == config
        assert executor.cli == cli_group
        assert executor.validate_callback == validate_cb
        assert executor.append_output == append_cb

    def test_format_command_display_simple(self, executor):
        """Test formatting simple command."""
        lines = executor.format_command_display("/greet")

        assert len(lines) == 1
        assert any("/greet" in str(item) for item in lines[0])

    def test_format_command_display_with_args(self, executor):
        """Test formatting command with arguments."""
        lines = executor.format_command_display("/greet Alice")

        assert len(lines) >= 1
        # Should have command line and args line
        assert any("/greet" in str(item) for item in lines[0])

    def test_format_command_display_with_error(self, executor):
        """Test formatting command with error."""
        lines = executor.format_command_display("/unknown", has_error=True)

        assert len(lines) >= 1
        # Error styling should be applied

    def test_format_command_display_with_warning(self, executor):
        """Test formatting command with warning."""
        lines = executor.format_command_display("/deploy prod", has_warning=True)

        assert len(lines) >= 1
        # Warning styling should be applied

    def test_format_command_display_subcommand(self, executor):
        """Test formatting subcommand."""
        lines = executor.format_command_display("/config get mykey")

        assert len(lines) >= 1
        # Should show command chain

    def test_execute_command_quit(self, executor):
        """Test executing quit command."""
        input_buffer = Mock()
        event = Mock()

        executor.execute_command("/quit", input_buffer, False, event)

        # Should call app.exit()
        event.app.exit.assert_called_once()
        executor.append_output.assert_called()

    def test_execute_command_valid(self, executor, cli_group):
        """Test executing valid command."""
        input_buffer = Mock()
        event = Mock()

        executor.execute_command("/simple", input_buffer, False, event)

        # Should append history and output
        input_buffer.append_to_history.assert_called_once()
        executor.append_output.assert_called()

    def test_execute_command_with_validation_error(self, config, cli_group):
        """Test executing command with validation error."""
        # Create executor with failing validation
        validate_cb = Mock(
            return_value=(
                ValidationResult(status="invalid", message="Test error"),
                "required",
            )
        )
        append_output = Mock()

        executor = CommandExecutor(
            config=config,
            cli=cli_group,
            validate_callback=validate_cb,
            append_output_callback=append_output,
        )

        input_buffer = Mock()
        event = Mock()

        executor.execute_command("/greet", input_buffer, False, event)

        # Should not append to history (blocked)
        input_buffer.append_to_history.assert_not_called()
        # Should show error message
        assert any(
            "Test error" in str(call) for call in append_output.call_args_list
        )

    def test_execute_command_with_warning(self, config, cli_group):
        """Test executing command with validation warning."""
        validate_cb = Mock(
            return_value=(
                ValidationResult(status="warning", message="Test warning"),
                "optional",
            )
        )
        append_output = Mock()

        executor = CommandExecutor(
            config=config,
            cli=cli_group,
            validate_callback=validate_cb,
            append_output_callback=append_output,
        )

        input_buffer = Mock()
        event = Mock()

        executor.execute_command("/simple", input_buffer, False, event)

        # Should still execute (not blocked)
        input_buffer.append_to_history.assert_called_once()

    def test_execute_click_command(self, executor, cli_group):
        """Test executing Click command."""
        cmd = cli_group.commands["simple"]

        executor._execute_click_command(cmd, [])

        # Should append output from command
        executor.append_output.assert_called()
        # Check that "Simple output" was appended
        assert any(
            "Simple output" in str(call) for call in executor.append_output.call_args_list
        )

    def test_execute_click_command_with_args(self, executor, cli_group):
        """Test executing Click command with arguments."""
        cmd = cli_group.commands["greet"]

        executor._execute_click_command(cmd, ["Alice"])

        # Should append output
        executor.append_output.assert_called()
        # Check that output was generated (the command ran)
        assert len(executor.append_output.call_args_list) > 0

    def test_execute_click_command_error_handling(self, executor, cli_group):
        """Test Click command execution with error."""
        cmd = cli_group.commands["greet"]

        # Execute with missing argument (should catch exception)
        executor._execute_click_command(cmd, [])

        # Should append error message
        executor.append_output.assert_called()
