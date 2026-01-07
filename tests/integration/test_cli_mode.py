"""Integration tests for CLI mode (non-REPL) command execution."""

import subprocess
import sys


def test_hello_command_cli_mode():
    """Test hello command execution in CLI mode."""
    result = subprocess.run(
        [sys.executable, "-m", "demo.cli", "hello", "World"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
    assert "hello - World" in result.stdout


def test_hello_command_with_multiple_args():
    """Test hello command with multiple arguments in CLI mode."""
    result = subprocess.run(
        [sys.executable, "-m", "demo.cli", "hello", "Hello", "from", "CLI"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
    assert "hello - Hello from CLI" in result.stdout


def test_sub_red_command_cli_mode():
    """Test subcommand execution in CLI mode."""
    result = subprocess.run(
        [sys.executable, "-m", "demo.cli", "sub", "red", "This", "is", "red"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
    assert "RED: This is red" in result.stdout


def test_sub_blue_command_cli_mode():
    """Test blue subcommand execution in CLI mode."""
    result = subprocess.run(
        [sys.executable, "-m", "demo.cli", "sub", "blue", "Blue", "text"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
    assert "BLUE: Blue text" in result.stdout


def test_list_files_command_cli_mode():
    """Test list_files command execution in CLI mode."""
    result = subprocess.run(
        [sys.executable, "-m", "demo.cli", "list_files"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
    # Should list files in current directory
    assert "total" in result.stdout or "." in result.stdout


def test_list_files_with_path_cli_mode():
    """Test list_files command with specific path in CLI mode."""
    result = subprocess.run(
        [sys.executable, "-m", "demo.cli", "list_files", "demo"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
    # Should list files in demo directory
    assert "commands.py" in result.stdout or "cli.py" in result.stdout


def test_unknown_command_cli_mode():
    """Test unknown command shows appropriate error in CLI mode."""
    result = subprocess.run(
        [sys.executable, "-m", "demo.cli", "unknown_command"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Unknown command should exit with non-zero code
    assert result.returncode != 0
    assert "Error" in result.stderr or "No such command" in result.stderr


def test_help_command_cli_mode():
    """Test help output in CLI mode."""
    result = subprocess.run(
        [sys.executable, "-m", "demo.cli", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0
    # Should show available commands
    assert "hello" in result.stdout
    assert "sub" in result.stdout
    assert "list_files" in result.stdout


def test_subcommand_help_cli_mode():
    """Test subcommand help output in CLI mode."""
    result = subprocess.run(
        [sys.executable, "-m", "demo.cli", "sub", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0
    # Should show subcommands
    assert "red" in result.stdout
    assert "blue" in result.stdout
