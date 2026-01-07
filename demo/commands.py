"""Commands for Hello World demo app."""

import sys
import subprocess
from pathlib import Path

import click

from cli_repl_kit import CommandPlugin


class HelloCommandsPlugin(CommandPlugin):
    """Hello World demo commands.

    Validation is automatic based on Click decorators!
    - hello: required=True means validation blocks if no text provided
    - list_files: nargs=-1 with no required means optional (no validation)
    - sub red/blue: required=True means validation blocks if no text provided
    """

    @property
    def name(self):
        return "hello_commands"

    def register(self, cli, context_factory):
        """Register commands with the REPL."""

        # quit
        @click.command()
        def quit():
            """Exit the application."""
            print("Goodbye!")
            raise SystemExit(0)

        # hello
        @click.command()
        @click.argument("text", nargs=-1, required=True)
        def hello(text):
            """Say hello with custom text."""
            message = " ".join(text)
            print(f"hello - {message}")

        # list files
        @click.command()
        @click.argument("path", nargs=-1)
        def list_files(path):
            """List files in the specified directory (default: current directory)."""
            # Use current directory if no path provided
            target_path_str = " ".join(path) if path else "."

            try:
                # Validate path to prevent path traversal attacks
                target_path = Path(target_path_str).resolve()
                cwd = Path.cwd().resolve()

                # Security: Prevent path traversal outside current directory
                if not str(target_path).startswith(str(cwd)):
                    print(f"Error: Path '{target_path_str}' is outside current directory")
                    print(f"Access is restricted to: {cwd}")
                    return

                # Verify path exists
                if not target_path.exists():
                    print(f"Error: Path '{target_path_str}' does not exist")
                    return

                # Cross-platform command selection
                if sys.platform == "win32":
                    cmd = ["dir", "/W", str(target_path)]
                else:
                    cmd = ["ls", "-la", str(target_path)]

                # Run platform-specific command
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Print the output - this will be captured by the REPL
                print(result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"Error listing files: {e.stderr}")
            except FileNotFoundError:
                cmd_name = "dir" if sys.platform == "win32" else "ls"
                print(f"Error: '{cmd_name}' command not found")
            except (ValueError, OSError) as e:
                print(f"Error: Invalid path - {e}")

        # sub menus
        @click.group()
        def sub():
            """Colored text subcommands."""
            pass

        @sub.command()
        @click.argument("text", nargs=-1, required=True)
        def red(text):
            """Print text in red."""
            message = " ".join(text)
            print(f"RED: {message}")

        @sub.command()
        @click.argument("text", nargs=-1, required=True)
        def blue(text):
            """Print text in blue."""
            message = " ".join(text)
            print(f"BLUE: {message}")

        # echo
        @click.command()
        @click.argument("message", nargs=-1)
        def echo(message):
            """Echo a message. DEPRECATED: Use '/print' instead."""
            print(" ".join(message))

        @click.command()
        @click.argument("greeting", nargs=-1, required=True)
        def greet(greeting):
            """Greet someone with custom greeting text."""
            message = " ".join(greeting)
            print(f"Hello, {message}!")

        # deploy
        @click.command()
        @click.argument("environment", type=click.Choice(["dev", "staging", "prod"]))
        def deploy(environment):
            """Deploy to an environment (automatically validated!) - Valid environments: dev, staging, prod."""
            if environment == "prod":
                click.echo("WARNING: Deploying to PRODUCTION - use extreme caution!")

            print(f"Deploying to {environment}...")
            print(f"Deployment to {environment} successful!")

        # status - for setting the status line
        @click.command()
        @click.argument("text", nargs=-1, required=False)
        def status(text):
            """Set or clear the status line.

            Examples:
                /status Processing data...
                /status
            """
            if text:
                message = " ".join(text)
                print(f"[Status] {message}")
                # TODO: When REPL context is available, call repl.set_status()
            else:
                print("[Status] Cleared")
                # TODO: When REPL context is available, call repl.clear_status()

        # info - for setting the info line
        @click.command()
        @click.argument("text", nargs=-1, required=False)
        def info(text):
            """Set or clear the info line.

            Examples:
                /info Ready to process
                /info
            """
            if text:
                message = " ".join(text)
                print(f"[Info] {message}")
                # TODO: When REPL context is available, call repl.set_info()
            else:
                print("[Info] Cleared")
                # TODO: When REPL context is available, call repl.clear_info()

        # Register commands
        cli.add_command(deploy, name="deploy")
        cli.add_command(echo, name="echo")
        cli.add_command(greet, name="greet")
        cli.add_command(hello, name="hello")
        cli.add_command(info, name="info")
        cli.add_command(list_files, name="list_files")
        cli.add_command(quit, name="quit")
        cli.add_command(status, name="status")
        cli.add_command(sub, name="sub")
