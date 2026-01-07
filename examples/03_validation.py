"""
Example 03 - Automatic Validation

Shows how cli-repl-kit automatically validates commands.
Demonstrates: Click.Choice, required arguments, validation errors.

Run:
    python examples/03_validation.py              # REPL mode
    python examples/03_validation.py deploy prod  # CLI mode

In REPL:
    > /deploy
    ❌ Missing required argument: env
    > /deploy staging
    ❌ Invalid value for 'env': 'staging' is not one of 'dev', 'test', 'prod'
    > /deploy prod
    ✅ Deploying to: prod
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from cli_repl_kit import REPL


def main():
    """Create REPL with validated commands."""
    repl = REPL(app_name="Example 03 - Validation")

    @repl.cli.command()
    @click.argument("env", type=click.Choice(["dev", "test", "prod"]))
    def deploy(env):
        """Deploy to an environment (dev, test, or prod)."""
        print(f"Deploying to: {env}")

    @repl.cli.command()
    @click.argument("level", type=click.Choice(["debug", "info", "warning", "error"]))
    def loglevel(level):
        """Set log level."""
        print(f"Log level set to: {level}")

    @repl.cli.command()
    @click.argument("filename", required=True)
    def read(filename):
        """Read a file (demonstrates required argument)."""
        print(f"Reading file: {filename}")
        # In a real app, you would read the actual file here

    @repl.cli.command()
    @click.argument("count", type=int, required=True)
    @click.argument("message", nargs=-1, required=True)
    def repeat(count, message):
        """Repeat a message N times."""
        text = " ".join(message)
        for i in range(count):
            print(f"{i+1}. {text}")

    repl.start()


if __name__ == "__main__":
    main()
