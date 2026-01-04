"""
Rich styling and themes for terminal output.
"""

from rich.theme import Theme


# Custom theme for the application
APP_THEME = Theme(
    {
        "success": "bold green",
        "error": "bold red",
        "warning": "bold yellow",
        "info": "bold blue",
        "dim": "dim",
        "highlight": "bold cyan",
        "prompt": "bold magenta",
    }
)


# Common symbols
SYMBOLS = {
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    "info": "ℹ",
    "arrow": "-",
    "bullet": "•",
}


def format_success(message: str) -> str:
    """Format a success message."""
    return f"[success]{SYMBOLS['success']}[/success] {message}"


def format_error(message: str) -> str:
    """Format an error message."""
    return f"[error]{SYMBOLS['error']} Error:[/error] {message}"


def format_warning(message: str) -> str:
    """Format a warning message."""
    return f"[warning]{SYMBOLS['warning']} Warning:[/warning] {message}"


def format_info(message: str) -> str:
    """Format an info message."""
    return f"[info]{SYMBOLS['info']}[/info] {message}"
