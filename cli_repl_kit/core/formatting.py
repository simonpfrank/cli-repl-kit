"""Text formatting and ANSI conversion utilities.

This module provides functions for converting between prompt_toolkit's FormattedText
structure and ANSI-escaped strings, as well as lexing ANSI codes back into styled text.
"""
from typing import Any, Callable, List, Tuple, cast

from prompt_toolkit.formatted_text import ANSI, StyleAndTextTuples
from prompt_toolkit.lexers import Lexer


def formatted_text_to_ansi_string(
    formatted_text: List[Tuple[str, str]], config: Any
) -> str:
    r"""Convert FormattedText list to ANSI-escaped string.

    Takes a list of (style, text) tuples and converts them to a string with
    ANSI escape codes for terminal display. Styles are looked up in the config's
    ansi_colors object.

    Args:
        formatted_text: List of (style, text) tuples
        config: Config object with ansi_colors attribute

    Returns:
        String with ANSI escape codes

    Example:
        >>> formatted_text = [("red", "Error: "), ("", "Something failed")]
        >>> result = formatted_text_to_ansi_string(formatted_text, config)
        >>> # Returns: "\x1b[31mError: \x1b[0mSomething failed"
    """
    if not formatted_text:
        return ""

    ansi_colors = config.ansi_colors
    reset = ansi_colors.reset

    result = []
    for style, text in formatted_text:
        # Handle empty style
        if not style or style == "":
            result.append(text)
            continue

        # Try to look up style in config
        # Replace spaces with underscores for combined styles like "cyan bold" -> "cyan_bold"
        style_key = style.replace(" ", "_")

        # Try to get ANSI code from config
        ansi_code = None
        if hasattr(ansi_colors, style_key):
            ansi_code = getattr(ansi_colors, style_key)
        elif hasattr(ansi_colors, style):
            ansi_code = getattr(ansi_colors, style)

        if ansi_code:
            result.append(f"{ansi_code}{text}{reset}")
        else:
            # Unknown style, just append text without ANSI codes
            result.append(text)

    return "".join(result)


class ANSILexer(Lexer):
    """Lexer that interprets ANSI escape codes and returns styled fragments.

    This lexer parses terminal output containing ANSI escape codes and converts
    them back into prompt_toolkit's FormattedText structure for display.
    """

    def lex_document(self, document) -> Callable[[int], StyleAndTextTuples]:
        r"""Return a function that returns styled fragments for a line.

        Args:
            document: prompt_toolkit Document

        Returns:
            Function that takes line number and returns FormattedText

        Example:
            >>> lexer = ANSILexer()
            >>> doc = Document("\x1b[31mRed text\x1b[0m")
            >>> get_line = lexer.lex_document(doc)
            >>> fragments = get_line(0)  # Returns styled fragments
        """
        lines = document.lines

        def get_line(lineno: int) -> StyleAndTextTuples:
            """Get styled fragments for a specific line number.

            Args:
                lineno: Line number (0-indexed)

            Returns:
                List of (style, text) tuples (FormattedText)
            """
            if lineno < len(lines):
                line = lines[lineno]
                # Parse ANSI codes and return FormattedText
                return ANSI(line).__pt_formatted_text__()
            return []

        return get_line
