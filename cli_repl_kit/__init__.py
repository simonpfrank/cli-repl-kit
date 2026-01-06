"""
cli-repl-kit: A reusable CLI/REPL framework with plugin support.

This package provides a framework for building interactive command-line tools
with both REPL (Read-Eval-Print Loop) and traditional CLI modes. It features:

- Plugin-based architecture using Python entry points
- Slash command completion (Claude Code style)
- Rich console output with customizable themes
- Context injection for shared state
- Dual-mode support (interactive REPL + CLI commands)
- Agent mode for free text input
"""

__version__ = "0.1.0"

# Main exports
from cli_repl_kit.core.repl import REPL
from cli_repl_kit.plugins.base import CommandPlugin, ValidationResult
from cli_repl_kit.core.completion import SlashCommandCompleter

__all__ = [
    "REPL",
    "CommandPlugin",
    "ValidationResult",
    "SlashCommandCompleter",
]
