"""Example plugin demonstrating automatic validation.

This plugin showcases automatic validation based on Click decorators:
- Required validation: click.Choice automatically blocks invalid values (deploy)
- Optional validation: nargs=-1 without required=True allows empty (echo)
- No validation: default argument means no validation needed (greet)
"""

import click

from cli_repl_kit import CommandPlugin


class ValidatingCommandsPlugin(CommandPlugin):
    """Example plugin with automatic validation.

    Validation is now automatic! No validation methods needed.
    - deploy: Uses click.Choice to restrict to valid environments
    - echo: Optional args (nargs=-1 without required=True)
    - greet: Has default value, so optional
    """

    @property
    def name(self):
        return "validating_commands"

    def register(self, cli, context_factory):
        """Register demo commands with automatic validation."""

        @click.command()
        @click.argument("environment", type=click.Choice(["dev", "staging", "prod"]))
        def deploy(environment):
            """Deploy to an environment (automatically validated!).

            Valid environments: dev, staging, prod

            Click's Choice type automatically validates the environment.
            """
            if environment == "prod":
                click.echo("WARNING: Deploying to PRODUCTION - use extreme caution!")

            print(f"Deploying to {environment}...")
            print(f"Deployment to {environment} successful!")

        @click.command()
        @click.argument("message", nargs=-1)
        def echo(message):
            """Echo a message.

            DEPRECATED: Use '/print' instead.
            """
            click.echo("WARNING: The 'echo' command is deprecated, use '/print' instead")
            print(" ".join(message))

        @click.command()
        @click.argument("name", default="World")
        def greet(name):
            """Greet someone (no validation needed - has default)."""
            print(f"Hello, {name}!")

        cli.add_command(deploy, name="deploy")
        cli.add_command(echo, name="echo")
        cli.add_command(greet, name="greet")
