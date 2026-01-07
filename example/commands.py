"""Commands for Hello World demo app."""

import subprocess

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
            target_path = " ".join(path) if path else "."

            try:
                # Run ls command and capture output
                result = subprocess.run(
                    ["ls", "-la", target_path],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Print the output - this will be captured by the REPL
                print(result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"Error listing files: {e.stderr}")
            except FileNotFoundError:
                print("Error: 'ls' command not found")

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
        @click.argument("how_do_you_want_be_greeted")
        def greet(how_do_you_want_be_greeted):
            """Greet someone (no validation needed - has default)."""
            print(f"Hello, {how_do_you_want_be_greeted}!")

        # deploy
        @click.command()
        @click.argument("environment", type=click.Choice(["dev", "staging", "prod"]))
        def deploy(environment):
            """Deploy to an environment (automatically validated!) - Valid environments: dev, staging, prod."""
            if environment == "prod":
                click.echo("WARNING: Deploying to PRODUCTION - use extreme caution!")

            print(f"Deploying to {environment}...")
            print(f"Deployment to {environment} successful!")

        # Register commands
        cli.add_command(deploy, name="deploy")
        cli.add_command(echo, name="echo")
        cli.add_command(greet, name="greet")
        cli.add_command(quit, name="quit")
        cli.add_command(hello, name="hello")
        cli.add_command(list_files, name="list_files")
        cli.add_command(sub, name="sub")
