"""Example plugin demonstrating command validation.

This plugin showcases the three validation levels:
- Required: Blocks invalid commands (deploy)
- Optional: Warns but allows execution (echo)
- None: No validation (greet)
"""

import click

from cli_repl_kit import CommandPlugin, ValidationResult


class ValidatingCommandsPlugin(CommandPlugin):
    """Example plugin with validation."""

    @property
    def name(self):
        return "validating_commands"

    def register(self, cli, context_factory):
        """Register demo commands with different validation levels."""

        @click.command()
        @click.argument("environment")
        def deploy(environment):
            """Deploy to an environment (required validation).

            Valid environments: dev, staging, prod
            """
            print(f"Deploying to {environment}...")
            print(f"Deployment to {environment} successful!")

        @click.command()
        @click.argument("message", nargs=-1)
        def echo(message):
            """Echo a message (optional validation - deprecation warning)."""
            print(" ".join(message))

        @click.command()
        @click.argument("name", default="World")
        def greet(name):
            """Greet someone (no validation)."""
            print(f"Hello, {name}!")

        cli.add_command(deploy, name="deploy")
        cli.add_command(echo, name="echo")
        cli.add_command(greet, name="greet")

    def get_validation_config(self):
        """Configure validation levels for commands."""
        return {
            "deploy": "required",  # Block invalid environments
            "echo": "optional",    # Warn about deprecation but allow
            # "greet" not specified - defaults to no validation
        }

    def validate_command(self, cmd_name, cmd_args, parsed_args):
        """Validate command arguments."""

        if cmd_name == "deploy":
            # Required validation - block invalid environments
            allowed = ["dev", "staging", "prod"]

            if not cmd_args:
                return ValidationResult(
                    status="invalid",
                    message="Environment argument is required"
                )

            env = cmd_args[0]
            if env not in allowed:
                return ValidationResult(
                    status="invalid",
                    message=f"Environment must be one of: {', '.join(allowed)}"
                )

            # Additional warning for production deployments
            if env == "prod":
                return ValidationResult(
                    status="warning",
                    message="Deploying to PRODUCTION - use extreme caution!"
                )

            return ValidationResult(status="valid")

        elif cmd_name == "echo":
            # Optional validation - warn about deprecation
            return ValidationResult(
                status="warning",
                message="The 'echo' command is deprecated, use '/print' instead"
            )

        return ValidationResult(status="valid")
