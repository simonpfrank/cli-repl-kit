"""Commands for Hello World demo app."""
import click
from cli_repl_kit import CommandPlugin


class HelloCommandsPlugin(CommandPlugin):
    """Hello World demo commands."""

    @property
    def name(self):
        return "hello_commands"

    def register(self, cli, context_factory):
        """Register commands with the REPL."""

        @click.command()
        def quit():
            """Exit the application."""
            print("Goodbye!")
            raise SystemExit(0)

        @click.command()
        @click.argument("text", nargs=-1, required=True)
        def hello(text):
            """Say hello with custom text."""
            message = " ".join(text)
            print(f"hello - {message}")

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

        # Register commands
        cli.add_command(quit, name="quit")
        cli.add_command(hello, name="hello")
        cli.add_command(sub, name="sub")
