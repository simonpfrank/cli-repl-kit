"""Commands for Hello World demo app."""
import click
from cli_repl_kit import CommandPlugin, ValidationResult


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

    def get_validation_config(self):
        """Configure validation levels for commands."""
        return {
            "print": "required",  # Built-in command - require text argument
            "hello": "optional",  # Plugin command - show friendly reminder
            # "status" and "info" default to "none" (no validation)
        }

    def validate_command(self, cmd_name, cmd_args, parsed_args):
        """Validate command arguments."""

        if cmd_name == "print":
            # Required validation - ensure text is provided
            if not cmd_args:
                return ValidationResult(
                    status="invalid",
                    message="Text argument is required for print command"
                )
            return ValidationResult(status="valid")

        elif cmd_name == "hello":
            # Optional validation - friendly reminder
            if not cmd_args:
                return ValidationResult(
                    status="warning",
                    message="Tip: Try '/hello World' with a name for a custom greeting!"
                )
            return ValidationResult(status="valid")

        return ValidationResult(status="valid")
