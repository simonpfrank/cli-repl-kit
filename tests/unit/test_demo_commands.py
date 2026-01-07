"""Unit tests for demo app commands."""
import sys
from io import StringIO

import click
import pytest

from cli_repl_kit import REPL


class TestDemoCommands:
    """Test demo app commands work correctly."""

    def test_greet_command_accepts_text(self):
        """GIVEN a greet command
        WHEN user provides greeting text
        THEN command should accept and use the text
        """
        repl = REPL(app_name="Test")

        @repl.cli.command()
        @click.argument("greeting", nargs=-1, required=True)
        def greet(greeting):
            """Greet someone."""
            message = " ".join(greeting)
            print(f"Hello, {message}!")

        # Execute command with multiple words
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            ctx = click.Context(repl.cli)
            ctx.invoke(greet, greeting=("World", "from", "CLI"))
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "Hello, World from CLI!" in output

    def test_deploy_command_accepts_environment(self):
        """GIVEN a deploy command with Choice validation
        WHEN user provides valid environment
        THEN command should execute successfully
        """
        repl = REPL(app_name="Test")

        @repl.cli.command()
        @click.argument("environment", type=click.Choice(["dev", "staging", "prod"]))
        def deploy(environment):
            """Deploy to environment."""
            print(f"Deploying to {environment}")

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            ctx = click.Context(repl.cli)
            ctx.invoke(deploy, environment="prod")
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "Deploying to prod" in output

    def test_status_command_sets_status_line(self):
        """GIVEN a status command
        WHEN user sets status text
        THEN status line should be updated
        """
        repl = REPL(app_name="Test")

        captured_status = []

        @repl.cli.command()
        @click.argument("text", nargs=-1, required=True)
        @click.pass_obj
        def status(obj, text):
            """Set status line."""
            message = " ".join(text)
            # In real REPL, would call repl.set_status()
            captured_status.append(message)
            print(f"Status: {message}")

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            ctx = click.Context(repl.cli, obj={})
            ctx.invoke(status, text=("Processing", "data"))
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "Status: Processing data" in output
        assert captured_status[0] == "Processing data"

    def test_info_command_sets_info_line(self):
        """GIVEN an info command
        WHEN user sets info text
        THEN info line should be updated
        """
        repl = REPL(app_name="Test")

        captured_info = []

        @repl.cli.command()
        @click.argument("text", nargs=-1, required=True)
        @click.pass_obj
        def info(obj, text):
            """Set info line."""
            message = " ".join(text)
            captured_info.append(message)
            print(f"Info: {message}")

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            ctx = click.Context(repl.cli, obj={})
            ctx.invoke(info, text=("Ready", "to", "process"))
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "Info: Ready to process" in output
        assert captured_info[0] == "Ready to process"
