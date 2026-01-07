"""
Example 02 - Commands with Arguments

Shows how to create commands that accept arguments.
Demonstrates: Arguments, nargs, joining text.

Run:
    python examples/02_with_arguments.py          # REPL mode
    python examples/02_with_arguments.py greet Alice  # CLI mode

In REPL:
    > /greet Alice
    Hello, Alice!
    > /greet Alice Bob Charlie
    Hello, Alice Bob Charlie!
    > /echo testing 123
    Echo: testing 123
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from cli_repl_kit import REPL


def main():
    """Create REPL with argument-based commands."""
    repl = REPL(app_name="Example 02 - With Arguments")

    @repl.cli.command()
    @click.argument("name", nargs=-1, required=True)
    def greet(name):
        """Greet someone by name."""
        full_name = " ".join(name)
        print(f"Hello, {full_name}!")

    @repl.cli.command()
    @click.argument("text", nargs=-1, required=True)
    def echo(text):
        """Echo back the provided text."""
        message = " ".join(text)
        print(f"Echo: {message}")

    @repl.cli.command()
    @click.argument("x", type=int)
    @click.argument("y", type=int)
    def add(x, y):
        """Add two numbers together."""
        result = x + y
        print(f"{x} + {y} = {result}")

    repl.start()


if __name__ == "__main__":
    main()
