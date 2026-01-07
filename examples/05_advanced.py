"""
Example 05 - Advanced Features

Shows advanced cli-repl-kit features including context injection,
subprocess execution, and custom styling.

Demonstrates: Context factory, dependency injection, subprocess, rich output.

Run:
    python examples/05_advanced.py                # REPL mode
    python examples/05_advanced.py whoami         # CLI mode

In REPL:
    > /whoami
    Current user: alice
    Session ID: abc123
    > /shell ls -la
    (executes ls -la and shows output)
    > /status System is running
    [Sets status line at bottom of REPL]
"""
import sys
from pathlib import Path
import subprocess
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from cli_repl_kit import REPL


def create_context():
    """Context factory that provides shared state to commands.

    This function is called once when the REPL starts. The returned
    dictionary is passed to all commands via Click's context mechanism.
    """
    return {
        "user": "alice",
        "session_id": "abc123",
        "start_time": datetime.now(),
        "config": {
            "debug": False,
            "verbose": True,
        }
    }


def main():
    """Create REPL with advanced features."""
    repl = REPL(
        app_name="Example 05 - Advanced",
        context_factory=create_context
    )

    @repl.cli.command()
    @click.pass_context
    def whoami(ctx):
        """Show current user and session info (demonstrates context injection)."""
        user = ctx.obj["user"]
        session = ctx.obj["session_id"]
        start_time = ctx.obj["start_time"]
        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"Current user: {user}")
        print(f"Session ID: {session}")
        print(f"Session duration: {elapsed:.1f} seconds")

    @repl.cli.command()
    @click.argument("command", nargs=-1, required=True)
    def shell(command):
        """Execute a shell command (demonstrates subprocess).

        WARNING: This command executes arbitrary system commands.
        In production, you should whitelist allowed commands or add
        additional security checks.
        """
        cmd = list(command)

        # Security warning for demonstration purposes
        if not cmd:
            print("Error: No command specified")
            return

        # Optional: Add command whitelist for production use
        # DANGEROUS_COMMANDS = ["rm", "del", "format", "mkfs"]
        # if cmd[0] in DANGEROUS_COMMANDS:
        #     print(f"Error: Command '{cmd[0]}' is not allowed")
        #     return

        try:
            # Note: shell=False ensures no shell injection possible
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"Error: {result.stderr}", file=sys.stderr)
            if result.returncode != 0:
                print(f"Command exited with code {result.returncode}")
        except subprocess.TimeoutExpired:
            print("Error: Command timed out after 10 seconds")
        except FileNotFoundError:
            print(f"Error: Command not found: {cmd[0]}")
        except (OSError, ValueError) as e:
            print(f"Error executing command: {e}")

    @repl.cli.command()
    @click.argument("text", nargs=-1, required=True)
    def status(text):
        """Set the status line (demonstrates REPL API)."""
        message = " ".join(text)
        repl.set_status(f"${{{message}}}", style="yellow")
        print(f"Status set to: {message}")

    @repl.cli.command()
    def clearstatus():
        """Clear the status line."""
        repl.clear_status()
        print("Status cleared")

    @repl.cli.command()
    @click.pass_context
    def debug(ctx):
        """Toggle debug mode (demonstrates context modification)."""
        ctx.obj["config"]["debug"] = not ctx.obj["config"]["debug"]
        state = "enabled" if ctx.obj["config"]["debug"] else "disabled"
        print(f"Debug mode {state}")

    @repl.cli.command()
    @click.pass_context
    def showconfig(ctx):
        """Show current configuration."""
        print("Configuration:")
        for key, value in ctx.obj["config"].items():
            print(f"  {key}: {value}")

    repl.start()


if __name__ == "__main__":
    main()
