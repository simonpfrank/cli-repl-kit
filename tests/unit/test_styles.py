"""Unit tests for Rich styling and themes."""
import pytest
from rich.theme import Theme
from rich.console import Console

from cli_repl_kit.ui.styles import (
    APP_THEME,
    SYMBOLS,
    format_success,
    format_error,
    format_warning,
    format_info,
)


def test_app_theme_exists():
    """Test that APP_THEME is defined."""
    assert APP_THEME is not None


def test_app_theme_is_rich_theme():
    """Test that APP_THEME is a Rich Theme instance."""
    assert isinstance(APP_THEME, Theme)


def test_app_theme_has_success_style():
    """Test that APP_THEME defines success style."""
    assert "success" in APP_THEME.styles


def test_app_theme_has_error_style():
    """Test that APP_THEME defines error style."""
    assert "error" in APP_THEME.styles


def test_app_theme_has_warning_style():
    """Test that APP_THEME defines warning style."""
    assert "warning" in APP_THEME.styles


def test_app_theme_has_info_style():
    """Test that APP_THEME defines info style."""
    assert "info" in APP_THEME.styles


def test_app_theme_has_dim_style():
    """Test that APP_THEME defines dim style."""
    assert "dim" in APP_THEME.styles


def test_app_theme_has_highlight_style():
    """Test that APP_THEME defines highlight style."""
    assert "highlight" in APP_THEME.styles


def test_app_theme_has_prompt_style():
    """Test that APP_THEME defines prompt style."""
    assert "prompt" in APP_THEME.styles


def test_symbols_dictionary_exists():
    """Test that SYMBOLS dictionary is defined."""
    assert SYMBOLS is not None
    assert isinstance(SYMBOLS, dict)


def test_symbols_has_success():
    """Test that SYMBOLS contains success symbol."""
    assert "success" in SYMBOLS
    assert isinstance(SYMBOLS["success"], str)
    assert len(SYMBOLS["success"]) > 0


def test_symbols_has_error():
    """Test that SYMBOLS contains error symbol."""
    assert "error" in SYMBOLS
    assert isinstance(SYMBOLS["error"], str)
    assert len(SYMBOLS["error"]) > 0


def test_symbols_has_warning():
    """Test that SYMBOLS contains warning symbol."""
    assert "warning" in SYMBOLS
    assert isinstance(SYMBOLS["warning"], str)
    assert len(SYMBOLS["warning"]) > 0


def test_symbols_has_info():
    """Test that SYMBOLS contains info symbol."""
    assert "info" in SYMBOLS
    assert isinstance(SYMBOLS["info"], str)
    assert len(SYMBOLS["info"]) > 0


def test_symbols_has_arrow():
    """Test that SYMBOLS contains arrow symbol."""
    assert "arrow" in SYMBOLS
    assert isinstance(SYMBOLS["arrow"], str)


def test_symbols_has_bullet():
    """Test that SYMBOLS contains bullet symbol."""
    assert "bullet" in SYMBOLS
    assert isinstance(SYMBOLS["bullet"], str)


def test_format_success_returns_string():
    """Test that format_success returns a string."""
    result = format_success("Test message")
    assert isinstance(result, str)


def test_format_success_contains_message():
    """Test that format_success includes the message."""
    message = "Operation completed"
    result = format_success(message)
    assert message in result


def test_format_success_contains_success_markup():
    """Test that format_success includes Rich success markup."""
    result = format_success("Test")
    assert "[success]" in result
    assert "[/success]" in result


def test_format_success_contains_success_symbol():
    """Test that format_success includes success symbol."""
    result = format_success("Test")
    assert SYMBOLS["success"] in result


def test_format_error_returns_string():
    """Test that format_error returns a string."""
    result = format_error("Test message")
    assert isinstance(result, str)


def test_format_error_contains_message():
    """Test that format_error includes the message."""
    message = "Something went wrong"
    result = format_error(message)
    assert message in result


def test_format_error_contains_error_markup():
    """Test that format_error includes Rich error markup."""
    result = format_error("Test")
    assert "[error]" in result
    assert "[/error]" in result


def test_format_error_contains_error_symbol():
    """Test that format_error includes error symbol."""
    result = format_error("Test")
    assert SYMBOLS["error"] in result


def test_format_error_contains_error_label():
    """Test that format_error includes 'Error:' label."""
    result = format_error("Test")
    assert "Error:" in result


def test_format_warning_returns_string():
    """Test that format_warning returns a string."""
    result = format_warning("Test message")
    assert isinstance(result, str)


def test_format_warning_contains_message():
    """Test that format_warning includes the message."""
    message = "Please be careful"
    result = format_warning(message)
    assert message in result


def test_format_warning_contains_warning_markup():
    """Test that format_warning includes Rich warning markup."""
    result = format_warning("Test")
    assert "[warning]" in result
    assert "[/warning]" in result


def test_format_warning_contains_warning_symbol():
    """Test that format_warning includes warning symbol."""
    result = format_warning("Test")
    assert SYMBOLS["warning"] in result


def test_format_warning_contains_warning_label():
    """Test that format_warning includes 'Warning:' label."""
    result = format_warning("Test")
    assert "Warning:" in result


def test_format_info_returns_string():
    """Test that format_info returns a string."""
    result = format_info("Test message")
    assert isinstance(result, str)


def test_format_info_contains_message():
    """Test that format_info includes the message."""
    message = "Here is some information"
    result = format_info(message)
    assert message in result


def test_format_info_contains_info_markup():
    """Test that format_info includes Rich info markup."""
    result = format_info("Test")
    assert "[info]" in result
    assert "[/info]" in result


def test_format_info_contains_info_symbol():
    """Test that format_info includes info symbol."""
    result = format_info("Test")
    assert SYMBOLS["info"] in result


def test_theme_can_be_applied_to_console():
    """Test that APP_THEME can be applied to a Rich Console."""
    # Should not raise an exception
    console = Console(theme=APP_THEME)
    # Verify console was created successfully
    assert console is not None
    assert isinstance(console, Console)


def test_formatted_messages_render_correctly_in_console():
    """Test that formatted messages can be rendered by Rich Console."""
    console = Console(theme=APP_THEME, record=True)

    # Test each formatter
    console.print(format_success("Success test"))
    console.print(format_error("Error test"))
    console.print(format_warning("Warning test"))
    console.print(format_info("Info test"))

    # Get rendered output (this verifies no rendering errors)
    output = console.export_text()

    # Verify messages are in output
    assert "Success test" in output
    assert "Error test" in output
    assert "Warning test" in output
    assert "Info test" in output


def test_format_success_with_empty_string():
    """Test that format_success handles empty string."""
    result = format_success("")
    assert isinstance(result, str)
    assert SYMBOLS["success"] in result


def test_format_error_with_empty_string():
    """Test that format_error handles empty string."""
    result = format_error("")
    assert isinstance(result, str)
    assert SYMBOLS["error"] in result


def test_format_warning_with_empty_string():
    """Test that format_warning handles empty string."""
    result = format_warning("")
    assert isinstance(result, str)
    assert SYMBOLS["warning"] in result


def test_format_info_with_empty_string():
    """Test that format_info handles empty string."""
    result = format_info("")
    assert isinstance(result, str)
    assert SYMBOLS["info"] in result


def test_format_success_with_special_characters():
    """Test that format_success handles special characters."""
    message = "Test with [brackets] and {braces}"
    result = format_success(message)
    # Rich markup should be preserved separately
    assert "Test with" in result


def test_format_error_with_multiline_message():
    """Test that format_error handles multiline messages."""
    message = "Line 1\nLine 2\nLine 3"
    result = format_error(message)
    assert "Line 1" in result
    assert "Line 2" in result
    assert "Line 3" in result


def test_symbols_are_unicode():
    """Test that symbols use Unicode characters (not ASCII)."""
    # Success symbol should be a checkmark (Unicode)
    assert SYMBOLS["success"] == "✓"

    # Error symbol should be a cross (Unicode)
    assert SYMBOLS["error"] == "✗"

    # Warning symbol should be a warning sign (Unicode)
    assert SYMBOLS["warning"] == "⚠"

    # Info symbol should be an info sign (Unicode)
    assert SYMBOLS["info"] == "ℹ"
