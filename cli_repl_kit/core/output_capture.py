"""Output capture utilities for redirecting stdout/stderr.

This module provides the OutputCapture class for capturing and redirecting
terminal output (stdout/stderr) to the REPL's output buffer with appropriate
styling.
"""
import io
from typing import Any, Callable, List, Tuple


class OutputCapture(io.StringIO):
    """Capture stdout/stderr and redirect to output buffer.

    This class intercepts writes to stdout or stderr and forwards them to
    a callback function with appropriate styling (e.g., red for stderr).
    Inherits from io.StringIO to be compatible as a file-like object.

    Example:
        >>> def output_callback(formatted_text):
        ...     print(formatted_text)
        >>> capture = OutputCapture("stderr", output_callback, config)
        >>> capture.write("Error message")  # Calls callback with styled text
    """

    def __init__(
        self,
        stream_type: str,
        output_callback: Callable[[List[Tuple[str, str]]], None],
        config: Any,
    ):
        """Initialize capture.

        Args:
            stream_type: "stdout" or "stderr"
            output_callback: Function to call with captured text (FormattedText)
            config: Config object with colors attribute for styling
        """
        super().__init__()
        self.stream_type = stream_type
        self.output_callback = output_callback
        self.config = config

    def write(self, text: str) -> None:
        """Capture text and send to output.

        Args:
            text: Text to capture
        """
        if not text or text == "\n":
            return

        # Add to output with appropriate styling
        if self.stream_type == "stderr":
            # Use error color from config
            self.output_callback([(self.config.colors.error, text)])
        else:
            # Default (no style) for stdout
            self.output_callback([("", text)])

    def flush(self) -> None:
        """Flush (no-op for our purposes)."""
        pass
