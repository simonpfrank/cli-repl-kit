"""Command executor for REPL commands.

This module provides the CommandExecutor class that handles command
formatting, validation, and execution.
"""
import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Callable, List, Optional, Tuple

import click
from prompt_toolkit.buffer import Buffer

from cli_repl_kit.core.config import Config
from cli_repl_kit.core.state import REPLState
from cli_repl_kit.plugins.base import ValidationResult


class CommandExecutor:
    """Handles command execution and formatting.

    Manages command display formatting, validation integration,
    and Click command execution with output capture. Coordinates
    between user input, validation, and Click command execution.

    Attributes:
        config: REPL configuration
        cli: Click CLI group
        validate_callback: Callback for command validation
        append_output: Callback to add output lines

    Example:
        >>> from unittest.mock import Mock
        >>> config = Config.load("config.yaml")
        >>> cli = click.Group()
        >>> validate_cb = Mock(return_value=(ValidationResult(status="valid"), None))
        >>> append_cb = Mock()
        >>> executor = CommandExecutor(config, cli, validate_cb, append_cb)
        >>> lines = executor.format_command_display("/hello world")
        >>> len(lines) > 0
        True
    """

    def __init__(
        self,
        config: Config,
        cli: click.Group,
        validate_callback: Callable[[str, List[str]], Tuple[ValidationResult, Optional[str]]],
        append_output_callback: Callable[[Any], None],
    ):
        """Initialize command executor.

        Args:
            config: REPL configuration
            cli: Click CLI group
            validate_callback: Function to validate commands before execution
            append_output_callback: Function to append formatted output lines

        Example:
            >>> executor = CommandExecutor(config, cli, validate, append)
            >>> executor.config == config
            True
        """
        self.config = config
        self.cli = cli
        self.validate_callback = validate_callback
        self.append_output = append_output_callback

    def format_command_display(
        self, command_text: str, has_error: bool = False, has_warning: bool = False
    ) -> List[Any]:
        """Format command for display with icons and styling.

        Creates formatted text representation of a command with appropriate
        icons (✓, ✗, ⚠) and color styling based on success/error/warning state.

        Args:
            command_text: The full command text (with or without /)
            has_error: Whether the command resulted in an error
            has_warning: Whether the command has a warning

        Returns:
            List of formatted text lines, each a list of (style, text) tuples

        Example:
            >>> executor = CommandExecutor(config, cli, validate_cb, append_cb)
            >>> lines = executor.format_command_display("/hello world")
            >>> len(lines) >= 1
            True
            >>> error_lines = executor.format_command_display("/bad", has_error=True)
            >>> any("✗" in str(line) for line in error_lines)
            True
        """
        # Remove leading / if present
        if command_text.startswith("/"):
            command_text = command_text[1:]

        # Parse command and arguments
        parts = command_text.split(maxsplit=1)
        if not parts:
            return []

        cmd_name = parts[0]
        has_args = len(parts) > 1
        args_text = parts[1] if has_args else ""

        # Parse subcommands from args
        subcommand_chain = []
        remaining_text = args_text

        if has_args and hasattr(self.cli, "commands"):
            current_cmd = self.cli.commands.get(cmd_name)
            arg_words = args_text.split()

            for i, word in enumerate(arg_words):
                if (
                    current_cmd
                    and hasattr(current_cmd, "commands")
                    and word in current_cmd.commands
                ):
                    subcommand_chain.append(word)
                    current_cmd = current_cmd.commands[word]
                else:
                    remaining_text = " ".join(arg_words[i:])
                    break
            else:
                remaining_text = ""

        # Choose icon based on command structure and status
        if has_warning:
            icon = self.config.symbols.warning
            icon_color = self.config.colors.warning
        elif has_args:
            icon = self.config.symbols.command_with_args
            icon_color = self.config.colors.grey
        else:
            if has_error:
                icon = self.config.symbols.command_error
                icon_color = self.config.colors.error
            else:
                icon = self.config.symbols.command_success
                icon_color = self.config.colors.success

        # Build command display line with subcommands
        cmd_display = [
            (icon_color, icon + " "),
            (self.config.colors.grey, "/" + cmd_name),
        ]

        # Add subcommands with arrow icons
        arrow = " → "
        for subcmd in subcommand_chain:
            cmd_display.append((self.config.colors.grey, arrow + subcmd))

        # If no remaining text, return single line
        if not remaining_text:
            return [cmd_display]

        # Add remaining text with indent
        lines = [cmd_display]
        indent_symbol = self.config.symbols.indent
        indent_prefix = [(self.config.colors.grey, indent_symbol + " ")]

        # Handle multi-line remaining text
        text_lines = remaining_text.split("\n")
        for i, text_line in enumerate(text_lines):
            if i == 0:
                lines.append(indent_prefix + [("", text_line)])
            else:
                lines.append([("", "  " + text_line)])

        return lines

    def execute_command(
        self,
        text: str,
        input_buffer: Buffer,
        enable_agent_mode: bool,
        event: Any,
    ) -> None:
        """Execute a command entered by the user.

        Args:
            text: The command text to execute
            input_buffer: Input buffer for history and clearing
            enable_agent_mode: If True, allows free text input
            event: The key event (for app.invalidate() and app.exit())
        """
        # Parse command name and args
        if text.startswith("/"):
            command = text[1:]
        elif enable_agent_mode:
            self.append_output([("cyan", "Echo: "), ("", text)])
            self.append_output([("", "")])
            event.app.invalidate()
            return
        else:
            command = text

        args = command.split()
        if not args:
            return

        cmd_name = args[0]
        cmd_args = args[1:]

        # Check if command exists
        command_exists = cmd_name in [
            "quit",
            "exit",
            "status",
            "info",
        ] or (hasattr(self.cli, "commands") and cmd_name in self.cli.commands)

        # Validate command
        validation_result, validation_level = self.validate_callback(cmd_name, cmd_args)

        # Determine display state
        should_block = False
        has_warning = False
        has_error = False

        if not command_exists:
            has_error = True
        elif validation_level == "required" and validation_result.should_block():
            should_block = True
            has_error = True
        elif validation_level == "optional" and validation_result.should_warn():
            has_warning = True
        else:
            has_error = False

        # Format and display command
        formatted_lines = self.format_command_display(
            text, has_error=has_error, has_warning=has_warning
        )
        for line in formatted_lines:
            self.append_output(line)

        # Display validation message
        if validation_result.message:
            if should_block:
                self.append_output(
                    [
                        (
                            "red",
                            f"{self.config.symbols.error} {validation_result.message}",
                        )
                    ]
                )
            elif has_warning:
                self.append_output(
                    [
                        (
                            "yellow",
                            f"{self.config.symbols.warning} {validation_result.message}",
                        )
                    ]
                )

        # Block execution if validation failed
        if should_block:
            self.append_output([("", "")])
            event.app.invalidate()
            return

        # Add to history
        input_buffer.append_to_history()

        # Handle quit/exit
        if cmd_name in ["quit", "exit"]:
            self.append_output([("", "Goodbye!")])
            event.app.invalidate()
            event.app.exit()
            return

        # Execute command
        if hasattr(self.cli, "commands") and cmd_name in self.cli.commands:
            cmd = self.cli.commands[cmd_name]
            if hasattr(cmd, "commands"):
                # Group command
                if cmd_args and cmd_args[0] in cmd.commands:
                    subcmd = cmd.commands[cmd_args[0]]
                    subcmd_args = cmd_args[1:]
                    self._execute_click_command(subcmd, subcmd_args)
                else:
                    self.append_output([("", "")])
            else:
                # Regular command
                self._execute_click_command(cmd, cmd_args)
        else:
            self.append_output([("red", f"Unknown command: {cmd_name}")])

        # Add empty line after output
        self.append_output([("", "")])
        event.app.invalidate()

    def _execute_click_command(self, cmd: click.Command, args: List[str]) -> None:
        """Execute a Click command and capture output.

        Args:
            cmd: The Click command to execute
            args: Command arguments
        """
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        try:
            ctx = click.Context(cmd)

            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                # Map args to Click parameter names (ctx.invoke requires kwargs)
                if hasattr(cmd, "params"):
                    # Get all argument parameters (not options)
                    arguments = [
                        p for p in cmd.params if isinstance(p, click.Argument)
                    ]

                    if arguments:
                        kwargs = {}
                        arg_idx = 0

                        for param in arguments:
                            if param.nargs == -1:
                                # This parameter takes all remaining args as tuple
                                kwargs[param.name] = tuple(args[arg_idx:])
                                break
                            else:
                                # This parameter takes 1 arg (nargs=1 is default)
                                if arg_idx < len(args):
                                    kwargs[param.name] = args[arg_idx]
                                    arg_idx += 1

                        ctx.invoke(cmd, **kwargs)
                    else:
                        # No arguments, invoke without args
                        ctx.invoke(cmd)
                else:
                    ctx.invoke(cmd)
        except SystemExit:
            pass
        except click.exceptions.MissingParameter as e:
            self.append_output([("red", f"Missing argument: {e.param.name}")])
        except Exception as e:
            self.append_output([("red", f"Error: {str(e)}")])

        # Add output
        stdout_text = stdout_buf.getvalue()
        stderr_text = stderr_buf.getvalue()

        if stdout_text:
            for line in stdout_text.rstrip().split("\n"):
                self.append_output([("", line)])
        if stderr_text:
            for line in stderr_text.rstrip().split("\n"):
                self.append_output([("red", line)])
