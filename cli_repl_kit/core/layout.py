"""UI layout components for REPL.

This module provides layout-related classes and utilities for building
the REPL user interface with prompt_toolkit.
"""
from typing import Any, Callable, List, Tuple

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.margins import Margin, ScrollbarMargin


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
    ) -> Callable[..., List[Tuple[str, str]]]:
        """Render scrollbar only if at max lines.

        Args:
            window_render_info: Window render information from prompt_toolkit
            width: Available width for the margin
            height: Available height for the margin

        Returns:
            Callable that returns formatted text for the margin
        """
        line_count = (
            max(1, self.buffer.text.count("\n") + 1) if self.buffer.text else 1
        )
        if line_count >= self.max_lines:
            return self.scrollbar.create_margin(window_render_info, width, height)
        # Return a function that returns empty formatted text (accept any args)
        return lambda *args, **kwargs: []
