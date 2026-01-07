"""
Example 01 - Basic Hello World

The simplest possible cli-repl-kit application.
Shows: Single command, basic output.

Run:
    python examples/01_basic_hello.py      # Start REPL mode
    python examples/01_basic_hello.py hello  # CLI mode

In REPL:
    > /hello
    Hello, World!
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from cli_repl_kit import REPL


def main():
    """Create and start the REPL."""
    # Create REPL instance
    repl = REPL(app_name="Example 01 - Basic Hello")

    # Register a simple command
    @repl.cli.command()
    def hello():
        """Say hello!"""
        print("Hello, World!")

    # Start the REPL
    repl.start()


if __name__ == "__main__":
    main()
