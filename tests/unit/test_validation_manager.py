"""Unit tests for ValidationManager module."""
import click
import pytest

from cli_repl_kit.core.validation_manager import ValidationManager
from cli_repl_kit.plugins.base import ValidationResult


class TestValidationManager:
    """Test ValidationManager class."""

    @pytest.fixture
    def cli_group(self):
        """Create a test CLI group with commands."""
        cli = click.Group()

        @cli.command()
        @click.argument("name", required=True)
        def greet(name):
            """Greet someone."""
            click.echo(f"Hello {name}")

        @cli.command()
        @click.argument("env", type=click.Choice(["dev", "staging", "prod"]))
        def deploy(env):
            """Deploy to environment."""
            click.echo(f"Deploying to {env}")

        @cli.command()
        def simple():
            """Simple command with no params."""
            click.echo("Simple")

        # Add a command group
        config_group = click.Group(name="config")

        @config_group.command()
        @click.argument("key")
        @click.argument("value")
        def set(key, value):
            """Set config value."""
            click.echo(f"Set {key}={value}")

        cli.add_command(config_group)

        return cli

    def test_initialization(self, cli_group):
        """Test ValidationManager initializes correctly."""
        manager = ValidationManager(cli_group)

        assert manager.cli == cli_group
        assert manager.validation_rules == {}

    def test_introspect_simple_command(self, cli_group):
        """Test introspection of simple command."""
        manager = ValidationManager(cli_group)
        manager.introspect_commands()

        # Simple command should have 'none' level
        assert "simple" in manager.validation_rules
        rule = manager.validation_rules["simple"]
        assert rule.level == "none"

    def test_introspect_required_argument(self, cli_group):
        """Test introspection of command with required argument."""
        manager = ValidationManager(cli_group)
        manager.introspect_commands()

        assert "greet" in manager.validation_rules
        rule = manager.validation_rules["greet"]
        assert rule.level == "required"
        assert "name" in rule.required_args

    def test_introspect_choice_parameter(self, cli_group):
        """Test introspection of command with choice parameter."""
        manager = ValidationManager(cli_group)
        manager.introspect_commands()

        assert "deploy" in manager.validation_rules
        rule = manager.validation_rules["deploy"]
        assert rule.level == "required"
        assert "env" in rule.choice_params
        assert set(rule.choice_params["env"]) == {"dev", "staging", "prod"}

    def test_introspect_subcommand(self, cli_group):
        """Test introspection of subcommand."""
        manager = ValidationManager(cli_group)
        manager.introspect_commands()

        assert "config.set" in manager.validation_rules
        rule = manager.validation_rules["config.set"]
        assert rule.level == "required"
        assert "key" in rule.required_args
        assert "value" in rule.required_args

    def test_validate_command_valid(self, cli_group):
        """Test validation of valid command."""
        manager = ValidationManager(cli_group)
        manager.introspect_commands()

        result, level = manager.validate_command("greet", ["Alice"])

        assert result.status == "valid"
        assert level == "required"

    def test_validate_command_missing_arg(self, cli_group):
        """Test validation of command with missing argument."""
        manager = ValidationManager(cli_group)
        manager.introspect_commands()

        result, level = manager.validate_command("greet", [])

        assert result.status == "invalid"
        assert "Missing required argument" in result.message
        assert level == "required"

    def test_validate_command_invalid_choice(self, cli_group):
        """Test validation of command with invalid choice."""
        manager = ValidationManager(cli_group)
        manager.introspect_commands()

        result, level = manager.validate_command("deploy", ["invalid"])

        assert result.status == "invalid"
        assert level == "required"

    def test_validate_command_valid_choice(self, cli_group):
        """Test validation of command with valid choice."""
        manager = ValidationManager(cli_group)
        manager.introspect_commands()

        result, level = manager.validate_command("deploy", ["dev"])

        assert result.status == "valid"
        assert level == "required"

    def test_validate_unknown_command(self, cli_group):
        """Test validation of unknown command."""
        manager = ValidationManager(cli_group)
        manager.introspect_commands()

        result, level = manager.validate_command("unknown", [])

        assert result.status == "valid"
        assert level is None

    def test_validate_subcommand(self, cli_group):
        """Test validation of subcommand."""
        manager = ValidationManager(cli_group)
        manager.introspect_commands()

        result, level = manager.validate_command("config.set", ["mykey", "myvalue"])

        assert result.status == "valid"
        assert level == "required"

    def test_validate_subcommand_missing_args(self, cli_group):
        """Test validation of subcommand with missing args."""
        manager = ValidationManager(cli_group)
        manager.introspect_commands()

        result, level = manager.validate_command("config.set", ["mykey"])

        assert result.status == "invalid"
        assert level == "required"
