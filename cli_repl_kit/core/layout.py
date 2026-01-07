"""UI layout components for REPL.

This module provides layout-related classes and utilities for building
the REPL user interface with prompt_toolkit.
"""
import shutil
from typing import Any, Callable, Optional

import click
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.margins import Margin, ScrollbarMargin

from cli_repl_kit.core.config import Config
from cli_repl_kit.core.formatting import ANSILexer, formatted_text_to_ansi_string
from cli_repl_kit.core.state import REPLState


class LayoutBuilder:
    """Builds prompt_toolkit Layout for REPL.

    Separates layout construction from REPL orchestration.
    Makes UI components testable and reusable.

    Attributes:
        config: Configuration for dimensions, colors
        state: REPLState for dynamic content
        cli: Click CLI group for command introspection
    """

    def __init__(self, config: Config, state: REPLState, cli: click.Group):
        """Initialize layout builder.

        Args:
            config: REPL configuration
            state: REPL state object
            cli: Click CLI group
        """
        self.config = config
        self.state = state
        self.cli = cli

    def build(self, input_buffer: Buffer, output_buffer: Buffer) -> Layout:
        """Build complete REPL layout.

        Args:
            input_buffer: Buffer for user input
            output_buffer: Buffer for command output

        Returns:
            Complete Layout with all windows
        """
        return Layout(
            HSplit(
                [
                    self._create_output_window(output_buffer),
                    self._create_status_window(),
                    self._create_divider_window(),
                    self._create_input_window(input_buffer),
                    self._create_divider_window(),
                    self._create_info_window(),
                    self._create_menu_window(input_buffer),
                    self._create_spacer_window(),
                ]
            )
        )

    def _create_output_window(self, output_buffer: Buffer) -> Window:
        """Create output display window.

        Args:
            output_buffer: Buffer containing command output

        Returns:
            Window for displaying output with ANSI rendering
        """
        return Window(
            content=BufferControl(
                buffer=output_buffer,
                focusable=False,  # Display-only
                include_default_input_processors=False,
                lexer=ANSILexer(),  # Render ANSI codes as styled text
            ),
            height=D(weight=1),  # Take remaining space
            wrap_lines=True,
            always_hide_cursor=True,  # No cursor in display-only area
        )

    def _create_input_window(self, input_buffer: Buffer) -> Window:
        """Create input window with dynamic height.

        Args:
            input_buffer: Buffer for user input

        Returns:
            Window for user input with prompt and dynamic sizing
        """
        prompt_char = self.config.prompt.character

        def get_input_prompt(line_number, wrap_count):
            """Show configurable prompt on first line, indent on continuation."""
            if line_number == 0 and wrap_count == 0:
                return [("bold", prompt_char)]
            else:
                # Continuation spacing matches prompt length
                return [("", " " * len(prompt_char))]

        return Window(
            content=BufferControl(
                buffer=input_buffer,
                lexer=None,
                input_processors=[],
                include_default_input_processors=False,
            ),
            height=lambda: self._get_input_height(input_buffer),
            wrap_lines=True,
            get_line_prefix=get_input_prompt,
            dont_extend_height=True,
        )

    def _create_status_window(self) -> Window:
        """Create status line window.

        Returns:
            Window for displaying status line
        """
        return Window(
            content=FormattedTextControl(text=self._render_status),
            height=self.config.windows.status.height,
            wrap_lines=False,  # Truncate overflow
        )

    def _create_info_window(self) -> Window:
        """Create info line window with dynamic height.

        Returns:
            Window for displaying info line (collapses when empty)
        """
        return Window(
            content=FormattedTextControl(text=self._render_info),
            height=self._get_info_height,
            wrap_lines=False,  # Truncate overflow
        )

    def _create_menu_window(self, input_buffer: Buffer) -> Window:
        """Create completion menu window with dynamic height.

        Args:
            input_buffer: Input buffer to check text for rendering

        Returns:
            Window for displaying completion menu
        """
        return Window(
            content=FormattedTextControl(
                text=lambda: self._render_completions(input_buffer)
            ),
            height=self._get_menu_height,
            wrap_lines=True,
        )

    def _create_divider_window(self) -> Window:
        """Create horizontal divider line.

        Returns:
            Window with single-line divider using terminal width
        """
        divider_color = self.config.colors.divider

        def get_divider_text():
            """Generate divider text based on current terminal width."""
            width = shutil.get_terminal_size().columns
            return [(divider_color, "─" * width)]

        return Window(
            height=1,
            content=FormattedTextControl(text=get_divider_text),
        )

    def _create_spacer_window(self) -> Window:
        """Create empty spacer line below menu.

        Returns:
            Window with single empty line for spacing
        """
        return Window(
            height=D(min=1, max=1, preferred=1),
            content=FormattedTextControl(text=lambda: [("", "")]),
        )

    def _get_input_height(self, input_buffer: Buffer) -> D:
        """Calculate input height based on buffer content.

        Args:
            input_buffer: Input buffer to measure

        Returns:
            Dimension for input window height
        """
        text = input_buffer.text
        if not text:
            return D(preferred=self.config.windows.input.initial_height)
        else:
            line_count = max(1, text.count("\n") + 1)
            return D(preferred=line_count)

    def _get_info_height(self) -> D:
        """Calculate info height based on whether info is set.

        Returns:
            Dimension for info window (1 line or 0)
        """
        if self.state.info_text:
            return D(preferred=1, min=1, max=1)
        else:
            return D(preferred=0, min=0, max=0)

    def _get_menu_height(self) -> D:
        """Calculate menu height - always uses configured height.

        The menu always occupies its configured height to prevent layout
        shifting. Content visibility is controlled by the rendering function,
        not by collapsing the window height.

        Returns:
            Dimension for menu window height (always configured value)
        """
        menu_preferred_height = self.config.windows.menu.height

        # Always use configured height - menu content controls visibility
        return D(preferred=menu_preferred_height)

    def _render_status(self) -> StyleAndTextTuples:
        """Render status line content.

        Returns:
            Formatted text for status line
        """
        if not self.state.status_text:
            return []
        return self.state.status_text

    def _render_info(self) -> StyleAndTextTuples:
        """Render info line content.

        Returns:
            Formatted text for info line
        """
        if not self.state.info_text:
            return []
        return self.state.info_text

    def _render_completions(self, input_buffer: Buffer) -> StyleAndTextTuples:
        """Render completion menu.

        Args:
            input_buffer: Input buffer to check text context

        Returns:
            Formatted text for completion menu
        """
        if not self.state.completions:
            return []

        text = input_buffer.text
        is_top_level = " " not in text.rstrip()

        # Calculate visible window of completions
        menu_height = self.config.windows.menu.height
        total_completions = len(self.state.completions)
        selected_idx = self.state.selected_idx

        # Calculate window to show
        if total_completions <= menu_height:
            start_idx = 0
            end_idx = total_completions
        else:
            # Center around selected item
            half_window = menu_height // 2
            start_idx = max(0, selected_idx - half_window)
            end_idx = min(total_completions, start_idx + menu_height)

            # Adjust if we hit the end
            if end_idx == total_completions:
                start_idx = max(0, end_idx - menu_height)

        lines = []
        for i in range(start_idx, end_idx):
            comp = self.state.completions[i]
            cmd_text = str(comp.text)
            help_text = comp.display_meta if hasattr(comp, "display_meta") else ""
            if isinstance(help_text, list):
                help_text = "".join(t for _, t in help_text)
            else:
                help_text = str(help_text) if help_text else ""

            prefix = "/" if is_top_level else ""
            formatted = f"{prefix}{cmd_text:<19} {help_text}"

            highlight_color = self.config.colors.highlight
            grey_color = self.config.colors.grey
            style = (
                f"{highlight_color} bold" if i == self.state.selected_idx else grey_color
            )
            lines.append((style, formatted))
            if i < end_idx - 1:
                lines.append(("", "\n"))
        return lines

    def get_argument_placeholder_text(
        self, cmd_name: str, subcmd_name: Optional[str] = None
    ) -> Optional[str]:
        """Get placeholder text for a command's first argument.

        Args:
            cmd_name: Name of the top-level command
            subcmd_name: Name of subcommand if cmd_name is a group

        Returns:
            Placeholder text like "<environment>" or None if no arguments
        """
        if not hasattr(self.cli, "commands"):
            return None
        if cmd_name not in self.cli.commands:
            return None

        cmd = self.cli.commands[cmd_name]

        # If it's a group and we have a subcommand
        if subcmd_name and hasattr(cmd, "commands"):
            if subcmd_name in cmd.commands:
                cmd = cmd.commands[subcmd_name]
            else:
                return None

        # Check for arguments
        if hasattr(cmd, "params"):
            for param in cmd.params:
                if isinstance(param, click.Argument):
                    if param.name is None:
                        continue
                    return f"<{param.name}>"
        return None


class ConditionalScrollbarMargin(Margin):
    """Scrollbar margin that only renders when a condition is met.

    This margin wraps a ScrollbarMargin and only displays it when the
    buffer content exceeds a specified number of lines. This prevents
    showing a scrollbar for short content where it's not needed.

    Example:
        >>> buffer = Buffer()
        >>> margin = ConditionalScrollbarMargin(buffer, max_lines=10)
        >>> # Scrollbar only shows when buffer has >= 10 lines
    """

    def __init__(
        self, buffer: Buffer, max_lines: int = 10, display_arrows: bool = True
    ):
        """Initialize conditional scrollbar margin.

        Args:
            buffer: The buffer to monitor for line count
            max_lines: Minimum lines before showing scrollbar (default: 10)
            display_arrows: Whether to display scroll arrows (default: True)
        """
        self.buffer = buffer
        self.max_lines = max_lines
        self.scrollbar = ScrollbarMargin(display_arrows=display_arrows)

    def get_width(self, ui_content: Any) -> int:
        """Return width only if condition is met.

        Args:
            ui_content: UI content information from prompt_toolkit

        Returns:
            Scrollbar width if line count >= max_lines, otherwise 0
        """
        line_count = (
            max(1, self.buffer.text.count("\n") + 1) if self.buffer.text else 1
        )
        if line_count >= self.max_lines:
            return self.scrollbar.get_width(ui_content)
        return 0

    def create_margin(
        self, window_render_info: Any, width: int, height: int
    ) -> StyleAndTextTuples:
        """Render scrollbar only if at max lines.

        Args:
            window_render_info: Window render information from prompt_toolkit
            width: Available width for the margin
            height: Available height for the margin

        Returns:
            Formatted text for the margin
        """
        line_count = (
            max(1, self.buffer.text.count("\n") + 1) if self.buffer.text else 1
        )
        if line_count >= self.max_lines:
            return self.scrollbar.create_margin(window_render_info, width, height)
        # Return empty formatted text
        return []
