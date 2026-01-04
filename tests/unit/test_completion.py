"""Unit tests for slash command completion."""
import pytest
import click
from unittest.mock import Mock
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent

from cli_repl_kit.core.completion import SlashCommandCompleter


def test_completer_initialization():
    """Test that SlashCommandCompleter can be initialized with commands."""
    commands = {
        "help": "Show help",
        "quit": "Exit the REPL"
    }
    completer = SlashCommandCompleter(commands)

    assert completer.commands == commands
    assert completer.cli_group is None


def test_completer_initialization_with_cli_group():
    """Test that SlashCommandCompleter accepts optional CLI group."""
    commands = {"help": "Show help"}
    cli_group = click.Group()

    completer = SlashCommandCompleter(commands, cli_group=cli_group)

    assert completer.commands == commands
    assert completer.cli_group is cli_group


def test_no_completions_without_slash():
    """Test that completions only show when input starts with /."""
    commands = {"help": "Show help", "quit": "Exit"}
    completer = SlashCommandCompleter(commands)

    # Test various inputs without /
    for text in ["help", "h", "hel", "  /help", "x/help"]:
        document = Document(text, cursor_position=len(text))
        event = CompleteEvent()
        completions = list(completer.get_completions(document, event))
        assert len(completions) == 0, f"Should not complete for '{text}'"


def test_top_level_command_completion():
    """Test completion of top-level commands."""
    commands = {
        "help": "Show help",
        "history": "Show history",
        "quit": "Exit"
    }
    completer = SlashCommandCompleter(commands)

    # Test partial completion
    document = Document("/h", cursor_position=2)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    # Should match "help" and "history"
    assert len(completions) == 2
    completion_texts = [c.text for c in completions]
    assert "help" in completion_texts
    assert "history" in completion_texts
    assert "quit" not in completion_texts


def test_case_insensitive_completion():
    """Test that command completion is case-insensitive."""
    commands = {
        "help": "Show help",
        "History": "Show history"
    }
    completer = SlashCommandCompleter(commands)

    # Test uppercase input
    document = Document("/H", cursor_position=2)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    assert len(completions) == 2
    completion_texts = [c.text for c in completions]
    assert "help" in completion_texts
    assert "History" in completion_texts


def test_exact_match_completion():
    """Test completion when input exactly matches a command."""
    commands = {
        "help": "Show help",
        "helper": "Show helper"
    }
    completer = SlashCommandCompleter(commands)

    document = Document("/help", cursor_position=5)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    # Should match both "help" and "helper"
    assert len(completions) == 2


def test_completion_start_position():
    """Test that completions have correct start_position for replacement."""
    commands = {"help": "Show help"}
    completer = SlashCommandCompleter(commands)

    document = Document("/hel", cursor_position=4)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    assert len(completions) == 1
    # Should replace "hel" with "help" (start_position = -3)
    assert completions[0].start_position == -3
    assert completions[0].text == "help"


def test_completion_display_format():
    """Test that completions have proper display format with meta."""
    commands = {"help": "Show available commands"}
    completer = SlashCommandCompleter(commands)

    document = Document("/h", cursor_position=2)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    assert len(completions) == 1
    # Display should have / prefix (check if text is in display)
    display_str = str(completions[0].display)
    assert "/help" in display_str
    # Meta should show help text (check if text is in meta)
    meta_str = str(completions[0].display_meta)
    assert "Show available commands" in meta_str


def test_empty_search_shows_all_commands():
    """Test that just '/' shows all available commands."""
    commands = {
        "help": "Show help",
        "quit": "Exit",
        "config": "Configure"
    }
    completer = SlashCommandCompleter(commands)

    document = Document("/", cursor_position=1)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    # Should show all 3 commands
    assert len(completions) == 3
    completion_texts = [c.text for c in completions]
    assert set(completion_texts) == {"help", "quit", "config"}


def test_subcommand_completion():
    """Test completion of subcommands for Click groups."""
    commands = {"config": "Configuration"}

    # Create Click group with subcommands
    @click.group()
    def config():
        """Configuration commands."""
        pass

    @config.command()
    def show():
        """Show configuration."""
        pass

    @config.command()
    def load():
        """Load configuration."""
        pass

    # Create CLI group and add config command
    cli_group = click.Group()
    cli_group.add_command(config, name="config")

    completer = SlashCommandCompleter(commands, cli_group=cli_group)

    # Test subcommand completion with space after base command
    document = Document("/config ", cursor_position=8)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    # Should show both subcommands
    assert len(completions) == 2
    completion_texts = [c.text for c in completions]
    assert "show" in completion_texts
    assert "load" in completion_texts


def test_subcommand_partial_completion():
    """Test partial completion of subcommands."""
    commands = {"config": "Configuration"}

    @click.group()
    def config():
        """Configuration commands."""
        pass

    @config.command()
    def show():
        """Show configuration."""
        pass

    @config.command()
    def save():
        """Save configuration."""
        pass

    cli_group = click.Group()
    cli_group.add_command(config, name="config")

    completer = SlashCommandCompleter(commands, cli_group=cli_group)

    # Test partial subcommand completion
    document = Document("/config s", cursor_position=9)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    # Should match both "show" and "save"
    assert len(completions) == 2
    completion_texts = [c.text for c in completions]
    assert "show" in completion_texts
    assert "save" in completion_texts


def test_subcommand_start_position():
    """Test that subcommand completions have correct start_position."""
    commands = {"config": "Configuration"}

    @click.group()
    def config():
        pass

    @config.command()
    def show():
        pass

    cli_group = click.Group()
    cli_group.add_command(config, name="config")

    completer = SlashCommandCompleter(commands, cli_group=cli_group)

    # Test with partial subcommand
    document = Document("/config sh", cursor_position=10)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    assert len(completions) == 1
    # Should replace "sh" with "show" (start_position = -2)
    assert completions[0].start_position == -2
    assert completions[0].text == "show"


def test_option_completion_for_subcommands():
    """Test completion of options for subcommands."""
    commands = {"config": "Configuration"}

    @click.group()
    def config():
        pass

    @config.command()
    @click.option("--file", "-f", help="Config file path")
    @click.option("--verbose", "-v", is_flag=True, help="Verbose output")
    def load(file, verbose):
        pass

    cli_group = click.Group()
    cli_group.add_command(config, name="config")

    completer = SlashCommandCompleter(commands, cli_group=cli_group)

    # Test option completion after subcommand
    document = Document("/config load ", cursor_position=13)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    # Should show both options (long form preferred)
    assert len(completions) == 2
    completion_texts = [c.text.strip() for c in completions]
    assert "--file" in completion_texts
    assert "--verbose" in completion_texts


def test_option_partial_completion():
    """Test partial completion of options."""
    commands = {"config": "Configuration"}

    @click.group()
    def config():
        pass

    @config.command()
    @click.option("--file", "-f", help="Config file")
    @click.option("--force", help="Force update")
    def load(file, force):
        pass

    cli_group = click.Group()
    cli_group.add_command(config, name="config")

    completer = SlashCommandCompleter(commands, cli_group=cli_group)

    # Test partial option completion
    document = Document("/config load --f", cursor_position=16)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    # Should match both --file and --force
    assert len(completions) == 2
    completion_texts = [c.text.strip() for c in completions]
    assert "--file" in completion_texts
    assert "--force" in completion_texts


def test_no_completions_for_unknown_command():
    """Test that no completions shown for unknown base command."""
    commands = {"help": "Show help"}
    completer = SlashCommandCompleter(commands)

    document = Document("/unknown subcommand", cursor_position=19)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    assert len(completions) == 0


def test_no_completions_for_command_without_subcommands():
    """Test that no subcommand completions for regular commands."""
    commands = {"help": "Show help"}

    # Regular command (not a group)
    @click.command()
    def help():
        pass

    cli_group = click.Group()
    cli_group.add_command(help, name="help")

    completer = SlashCommandCompleter(commands, cli_group=cli_group)

    document = Document("/help ", cursor_position=6)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    # Should not show any subcommands
    assert len(completions) == 0


def test_empty_input_after_slash_space():
    """Test handling of '/ ' (slash followed by space)."""
    commands = {"help": "Show help"}
    completer = SlashCommandCompleter(commands)

    document = Document("/ ", cursor_position=2)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    # Should handle gracefully without crashing
    # This tests the guard clause in the code
    assert len(completions) == 0


def test_sorted_completion_results():
    """Test that completions are returned in sorted order."""
    commands = {
        "quit": "Exit",
        "help": "Show help",
        "agent": "Agent commands"
    }
    completer = SlashCommandCompleter(commands)

    document = Document("/", cursor_position=1)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    # Should be in alphabetical order
    completion_texts = [c.text for c in completions]
    assert completion_texts == ["agent", "help", "quit"]


def test_subcommand_help_text_normalization():
    """Test that subcommand help text is normalized (first line only)."""
    commands = {"config": "Configuration"}

    @click.group()
    def config():
        pass

    @config.command()
    def show():
        """Show configuration.

        This is additional help text
        that should be stripped.
        """
        pass

    cli_group = click.Group()
    cli_group.add_command(config, name="config")

    completer = SlashCommandCompleter(commands, cli_group=cli_group)

    document = Document("/config ", cursor_position=8)
    event = CompleteEvent()
    completions = list(completer.get_completions(document, event))

    assert len(completions) == 1
    # Should only show first line of help text (check if text is in meta)
    meta_str = str(completions[0].display_meta)
    assert "Show configuration." in meta_str
    assert "additional help" not in meta_str.lower()
