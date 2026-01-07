"""
Example 04 - Subcommands and Groups

Shows how to organize commands into groups with subcommands.
Demonstrates: Click.Group, nested commands, command organization.

Run:
    python examples/04_subcommands.py                    # REPL mode
    python examples/04_subcommands.py config get theme  # CLI mode

In REPL:
    > /config get theme
    Config value for 'theme': dark
    > /config set theme light
    Set 'theme' to 'light'
    > /db connect
    Connected to database
    > /db query SELECT * FROM users
    Executing query: SELECT * FROM users
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from cli_repl_kit import REPL


def main():
    """Create REPL with subcommands."""
    repl = REPL(app_name="Example 04 - Subcommands")

    # Create a group for config commands
    @repl.cli.group()
    def config():
        """Configuration management commands."""
        pass

    @config.command()
    @click.argument("key")
    def get(key):
        """Get a configuration value."""
        print(f"Config value for '{key}': dark")  # Mock value

    @config.command()
    @click.argument("key")
    @click.argument("value")
    def set(key, value):
        """Set a configuration value."""
        print(f"Set '{key}' to '{value}'")

    @config.command()
    def list():
        """List all configuration values."""
        print("Configuration:")
        print("  theme: dark")
        print("  language: en")
        print("  auto_save: true")

    # Create a group for database commands
    @repl.cli.group()
    def db():
        """Database management commands."""
        pass

    @db.command()
    def connect():
        """Connect to the database."""
        print("Connected to database")

    @db.command()
    @click.argument("query", nargs=-1, required=True)
    def query(query):
        """Execute a database query."""
        sql = " ".join(query)
        print(f"Executing query: {sql}")
        print("Results: (3 rows)")

    @db.command()
    def status():
        """Show database status."""
        print("Database status:")
        print("  Status: Connected")
        print("  Tables: 12")
        print("  Size: 1.2 GB")

    repl.start()


if __name__ == "__main__":
    main()
