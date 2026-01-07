"""State management for REPL sessions.

This module provides the REPLState dataclass, which replaces the mutable
dictionary pattern with a typed, documented, testable state object.
"""
from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class REPLState:
    """Tracks the state of a REPL session.

    This replaces the mutable dict pattern with a typed, documented,
    testable state object. All state is mutable to allow updates during
    the REPL session.

    Attributes:
        completions: List of available command completions for current input
        selected_idx: Index of currently selected completion (0-based)
        placeholder_active: True if placeholder text (<text>) is being shown
        placeholder_start: Cursor position where placeholder begins
        status_text: Formatted text for status line display
        info_text: Formatted text for info line display
        slash_command_active: True when user input starts with /
        is_multiline: True when input contains newlines
        menu_keep_visible: Keep completion menu visible after command execution

    Example:
        >>> state = REPLState()
        >>> state.slash_command_active = True
        >>> state.selected_idx = 2
        >>> state.completions = ["hello", "help", "history"]
    """

    completions: List[str] = field(default_factory=list)
    selected_idx: int = 0
    placeholder_active: bool = False
    placeholder_start: int = 0
    status_text: List[Any] = field(default_factory=list)
    info_text: List[Any] = field(default_factory=list)
    slash_command_active: bool = False
    is_multiline: bool = False
    menu_keep_visible: bool = False

    def reset_completions(self) -> None:
        """Clear completion state.

        Resets both the completions list and the selected index.
        Used when user input changes and completions need to be regenerated.

        Example:
            >>> state = REPLState(completions=["hello", "help"], selected_idx=1)
            >>> state.reset_completions()
            >>> state.completions
            []
            >>> state.selected_idx
            0
        """
        self.completions = []
        self.selected_idx = 0

    def set_status(self, text: List[Any]) -> None:
        """Set status line content.

        Args:
            text: FormattedText list of (style, text) tuples

        Example:
            >>> state = REPLState()
            >>> state.set_status([("cyan", "Ready")])
            >>> state.status_text
            [('cyan', 'Ready')]
        """
        self.status_text = text

    def clear_status(self) -> None:
        """Clear status line.

        Example:
            >>> state = REPLState(status_text=[("cyan", "Status")])
            >>> state.clear_status()
            >>> state.status_text
            []
        """
        self.status_text = []

    def set_info(self, text: List[Any]) -> None:
        """Set info line content.

        Args:
            text: FormattedText list of (style, text) tuples

        Example:
            >>> state = REPLState()
            >>> state.set_info([("yellow", "Help available")])
            >>> state.info_text
            [('yellow', 'Help available')]
        """
        self.info_text = text

    def clear_info(self) -> None:
        """Clear info line.

        Example:
            >>> state = REPLState(info_text=[("yellow", "Info")])
            >>> state.clear_info()
            >>> state.info_text
            []
        """
        self.info_text = []
