"""Keyboard event handlers for REPL.

This module provides the KeyBindingManager class that handles all keyboard
input for the REPL, including navigation, editing, completion, and command execution.
"""
from typing import Any, Callable

import click
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings

from cli_repl_kit.core.config import Config
from cli_repl_kit.core.layout import LayoutBuilder
from cli_repl_kit.core.state import REPLState


class KeyBindingManager:
    """Manages keyboard bindings for REPL.

    Extracts key binding logic from massive _start_repl method.
    Each binding is a focused, testable method.

    Attributes:
        config: REPL configuration
        state: REPL state
        input_buffer: Input buffer
        output_buffer: Output buffer
        cli: Click CLI group
        layout_builder: Layout builder for command introspection
        execute_callback: Callback to execute commands
    """

    def __init__(
        self,
        config: Config,
        state: REPLState,
        input_buffer: Buffer,
        output_buffer: Buffer,
        cli: click.Group,
        layout_builder: LayoutBuilder,
        execute_callback: Callable[[str], None],
    ):
        """Initialize key binding manager.

        Args:
            config: REPL configuration
            state: REPL state object
            input_buffer: Input buffer
            output_buffer: Output buffer
            cli: Click CLI group
            layout_builder: Layout builder instance
            execute_callback: Function to call to execute commands
        """
        self.config = config
        self.state = state
        self.input_buffer = input_buffer
        self.output_buffer = output_buffer
        self.cli = cli
        self.layout_builder = layout_builder
        self.execute_callback = execute_callback
        self.page_scroll_lines = 10  # Lines to scroll per page

    def create_bindings(self) -> KeyBindings:
        """Create all key bindings.

        Returns:
            KeyBindings object with all handlers registered
        """
        kb = KeyBindings()

        # Register all handlers
        kb.add("c-c")(lambda event: event.app.exit())
        kb.add("escape")(self._handle_escape)
        kb.add("c-j")(self._handle_ctrl_j)
        kb.add("up")(self._handle_up)
        kb.add("down")(self._handle_down)
        kb.add("pageup")(self._handle_pageup)
        kb.add("pagedown")(self._handle_pagedown)
        kb.add("tab")(self._handle_tab)
        kb.add("space")(self._handle_space)
        kb.add("enter")(self._handle_enter)

        return kb

    def _handle_escape(self, event: Any) -> None:
        """Clear the input buffer on ESC."""
        event.current_buffer.text = ""
        event.current_buffer.cursor_position = 0
        self.state.placeholder_active = False
        self.state.menu_keep_visible = False
        event.app.invalidate()

    def _handle_ctrl_j(self, event: Any) -> None:
        """Insert newline on Ctrl-J."""
        event.current_buffer.insert_text("\n")

    def _handle_up(self, event: Any) -> None:
        """Handle up arrow navigation.

        Context-dependent:
        - If menu visible: navigate menu
        - If at start: navigate history
        - Otherwise: move cursor
        """
        buffer = event.current_buffer

        # Context 1: Slash command active with > 1 option - navigate menu
        if self.state.slash_command_active and len(self.state.completions) > 1:
            if self.state.selected_idx > 0:
                self.state.selected_idx -= 1
                event.app.invalidate()
            return

        # Context 2: Multi-line input - move cursor up one line
        if self.state.is_multiline:
            buffer.cursor_up()
            event.app.invalidate()
            return

        # Context 3: Single-line, cursor at start - navigate history
        if buffer.cursor_position == 0:
            buffer.history_backward()
            event.app.invalidate()
            return

        # Context 4: Single-line, cursor not at start - move to start
        buffer.cursor_position = 0
        event.app.invalidate()

    def _handle_down(self, event: Any) -> None:
        """Handle down arrow navigation."""
        buffer = event.current_buffer

        # Context 1: Slash command active with > 1 option - navigate menu
        if self.state.slash_command_active and len(self.state.completions) > 1:
            if self.state.selected_idx < len(self.state.completions) - 1:
                self.state.selected_idx += 1
                event.app.invalidate()
            return

        # Context 2: Multi-line input - move cursor down one line
        if self.state.is_multiline:
            buffer.cursor_down()
            event.app.invalidate()
            return

        # Context 3: Single-line, cursor at start - navigate history
        if buffer.cursor_position == 0:
            buffer.history_forward()
            event.app.invalidate()
            return

        # Context 4: Single-line, cursor not at start - move to start
        buffer.cursor_position = 0
        event.app.invalidate()

    def _handle_pageup(self, event: Any) -> None:
        """Scroll output buffer up by one page."""
        self.output_buffer.cursor_up(count=self.page_scroll_lines)
        event.app.invalidate()

    def _handle_pagedown(self, event: Any) -> None:
        """Scroll output buffer down by one page."""
        self.output_buffer.cursor_down(count=self.page_scroll_lines)
        event.app.invalidate()

    def _handle_tab(self, event: Any) -> None:
        """Complete command and add argument placeholder if needed."""
        if not self.state.completions or self.state.selected_idx < 0:
            return

        comp = self.state.completions[self.state.selected_idx]
        buffer = event.current_buffer

        # Delete what the completion replaces
        if comp.start_position:
            buffer.delete_before_cursor(-comp.start_position)

        # Insert completion
        buffer.insert_text(comp.text)

        # Check if this command/subcommand needs arguments
        parts = buffer.text.lstrip("/").split()
        cmd_name = parts[0] if parts else ""
        subcmd_name = parts[1] if len(parts) > 1 else None

        # Check if it's a group (needs subcommand)
        is_group = False
        if hasattr(self.cli, "commands") and cmd_name in self.cli.commands:
            cmd = self.cli.commands[cmd_name]
            is_group = hasattr(cmd, "commands")

        if is_group and not subcmd_name:
            # It's a group, add space to trigger subcommand completions
            buffer.insert_text(" ")
        else:
            # Check for argument placeholder
            arg_placeholder = self.layout_builder.get_argument_placeholder_text(
                cmd_name, subcmd_name
            )
            if arg_placeholder:
                buffer.insert_text(" " + arg_placeholder)
                # Position cursor at start of placeholder (on the <)
                cursor_pos = buffer.cursor_position - len(arg_placeholder)
                buffer.cursor_position = cursor_pos
                self.state.placeholder_active = True
                self.state.placeholder_start = cursor_pos

        event.app.invalidate()

    def _handle_space(self, event: Any) -> None:
        """Handle space - may trigger placeholder after command."""
        buffer = event.current_buffer
        text = buffer.text.strip()

        # Check if we're completing a command with space
        if text.startswith("/") and " " not in text:
            # First space after /command - check for exact match
            cmd_name = text[1:]  # Remove /
            if hasattr(self.cli, "commands") and cmd_name in self.cli.commands:
                cmd = self.cli.commands[cmd_name]

                # Check if it's a group
                if hasattr(cmd, "commands"):
                    # Group - just add space for subcommand
                    buffer.insert_text(" ")
                else:
                    # Regular command - check for args
                    arg_placeholder = self.layout_builder.get_argument_placeholder_text(
                        cmd_name
                    )
                    if arg_placeholder:
                        buffer.insert_text(" " + arg_placeholder)
                        cursor_pos = buffer.cursor_position - len(arg_placeholder)
                        buffer.cursor_position = cursor_pos
                        self.state.placeholder_active = True
                        self.state.placeholder_start = cursor_pos
                    else:
                        buffer.insert_text(" ")
                event.app.invalidate()
                return

        # Check if this is space after a subcommand
        parts = text.lstrip("/").split()
        if len(parts) == 2:  # /cmd subcmd<space>
            cmd_name, subcmd_name = parts
            if hasattr(self.cli, "commands") and cmd_name in self.cli.commands:
                cmd = self.cli.commands[cmd_name]
                if hasattr(cmd, "commands") and subcmd_name in cmd.commands:
                    arg_placeholder = self.layout_builder.get_argument_placeholder_text(
                        cmd_name, subcmd_name
                    )
                    if arg_placeholder:
                        buffer.insert_text(" " + arg_placeholder)
                        cursor_pos = buffer.cursor_position - len(arg_placeholder)
                        buffer.cursor_position = cursor_pos
                        self.state.placeholder_active = True
                        self.state.placeholder_start = cursor_pos
                        event.app.invalidate()
                        return

        # Default: just insert space
        buffer.insert_text(" ")
        event.app.invalidate()

    def _handle_enter(self, event: Any) -> None:
        """Execute command."""
        buffer = event.current_buffer
        text = buffer.text.strip()

        # Remove placeholder if still present
        if "<text>" in text:
            text = text.replace(" <text>", "").replace("<text>", "")

        # Auto-complete if partial match or just "/"
        if (
            self.state.completions
            and self.state.selected_idx >= 0
            and text.startswith("/")
        ):
            comp = self.state.completions[self.state.selected_idx]
            parts = text.split(maxsplit=1)
            first_word = parts[0][1:] if parts else ""  # Remove /
            rest_of_text = parts[1] if len(parts) > 1 else ""

            # Auto-complete if just "/" or if it's a partial match
            should_autocomplete = text == "/" or (
                first_word and first_word != comp.text and comp.text.startswith(first_word)
            )

            if should_autocomplete:
                text = "/" + comp.text
                if rest_of_text:
                    text += " " + rest_of_text

        if not text:
            return

        # Clear buffer and reset state
        buffer.text = ""
        buffer.cursor_position = 0
        self.state.placeholder_active = False
        self.state.menu_keep_visible = False
        self.state.reset_completions()

        # Execute via callback
        self.execute_callback(text, event)
