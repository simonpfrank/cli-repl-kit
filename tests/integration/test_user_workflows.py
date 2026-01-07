"""Integration tests for user workflows (BDD-style).

These tests verify actual user scenarios work end-to-end without mocking
internal REPL components. They test the real integration of all modules.
"""
import sys
from io import StringIO
from pathlib import Path

import click
import pytest

from cli_repl_kit import REPL


class TestBasicCommandExecution:
    """Test user can execute basic commands."""

    def test_user_can_register_and_execute_simple_command(self):
        """GIVEN a REPL with a simple command
        WHEN user executes the command via CLI mode
        THEN command output is captured correctly
        """
        # Given: REPL with hello command
        repl = REPL(app_name="Test App")

        output_captured = []

        @repl.cli.command()
        def hello():
            """Say hello."""
            print("Hello, World!")

        # When: Execute via CLI mode (simulated)
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Invoke the command directly
            ctx = click.Context(repl.cli)
            ctx.invoke(hello)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        # Then: Output should contain hello message
        assert "Hello, World!" in output

    def test_user_can_execute_command_with_arguments(self):
        """GIVEN a REPL with a command that takes arguments
        WHEN user executes the command with arguments
        THEN arguments are passed correctly
        """
        repl = REPL(app_name="Test App")

        @repl.cli.command()
        @click.argument("name")
        def greet(name):
            """Greet someone."""
            print(f"Hello, {name}!")

        # Execute command
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            ctx = click.Context(repl.cli)
            ctx.invoke(greet, name="Alice")
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "Hello, Alice!" in output

    def test_user_can_execute_command_with_multiple_arguments(self):
        """GIVEN a command with nargs=-1
        WHEN user provides multiple arguments
        THEN all arguments are received
        """
        repl = REPL(app_name="Test App")

        @repl.cli.command()
        @click.argument("words", nargs=-1)
        def echo(words):
            """Echo words."""
            print(" ".join(words))

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            ctx = click.Context(repl.cli)
            ctx.invoke(echo, words=("hello", "world", "test"))
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "hello world test" in output


class TestValidationWorkflow:
    """Test automatic validation works correctly."""

    def test_user_gets_validation_error_for_missing_required_argument(self):
        """GIVEN a command with required argument
        WHEN user executes without providing the argument
        THEN validation error is raised
        """
        repl = REPL(app_name="Test App")

        @repl.cli.command()
        @click.argument("name", required=True)
        def greet(name):
            """Greet someone."""
            print(f"Hello, {name}!")

        # Introspect to generate validation rules
        repl.validation_manager.introspect_commands()

        # Validate command with missing argument
        result, level = repl.validation_manager.validate_command("greet", [])

        assert result.status == "invalid"
        assert "name" in result.message.lower() or "missing" in result.message.lower()

    def test_user_gets_validation_error_for_invalid_choice(self):
        """GIVEN a command with Click.Choice
        WHEN user provides invalid choice
        THEN validation error is raised
        """
        repl = REPL(app_name="Test App")

        @repl.cli.command()
        @click.argument("env", type=click.Choice(["dev", "prod"]))
        def deploy(env):
            """Deploy to environment."""
            print(f"Deploying to {env}")

        repl.validation_manager.introspect_commands()

        # Validate with invalid choice
        result, level = repl.validation_manager.validate_command("deploy", ["staging"])

        assert result.status == "invalid"
        assert "staging" in result.message or "choice" in result.message.lower()

    def test_user_command_passes_validation_with_valid_input(self):
        """GIVEN a command with validation
        WHEN user provides valid input
        THEN validation passes
        """
        repl = REPL(app_name="Test App")

        @repl.cli.command()
        @click.argument("env", type=click.Choice(["dev", "prod"]))
        def deploy(env):
            """Deploy to environment."""
            print(f"Deploying to {env}")

        repl.validation_manager.introspect_commands()

        # Validate with valid choice
        result, level = repl.validation_manager.validate_command("deploy", ["prod"])

        assert result.status == "valid"
        assert level == "required"


class TestSubcommandWorkflow:
    """Test user can work with command groups and subcommands."""

    def test_user_can_execute_subcommand(self):
        """GIVEN a command group with subcommands
        WHEN user executes a subcommand
        THEN subcommand executes correctly
        """
        repl = REPL(app_name="Test App")

        @repl.cli.group()
        def config():
            """Config commands."""
            pass

        @config.command()
        @click.argument("key")
        def get(key):
            """Get config value."""
            print(f"Config: {key} = value")

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Execute subcommand
            ctx = click.Context(config)
            subcommand = config.commands["get"]
            ctx.invoke(subcommand, key="theme")
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "Config: theme" in output

    def test_user_subcommand_validation_works(self):
        """GIVEN a subcommand with validation
        WHEN user validates the subcommand
        THEN validation works correctly
        """
        repl = REPL(app_name="Test App")

        @repl.cli.group()
        def db():
            """Database commands."""
            pass

        @db.command()
        @click.argument("table", required=True)
        def drop(table):
            """Drop a table."""
            print(f"Dropping {table}")

        # Introspect to build rules for subcommands
        repl.validation_manager.introspect_commands()

        # Validate subcommand - missing argument
        result, level = repl.validation_manager.validate_command("db.drop", [])

        assert result.status == "invalid"

        # Validate subcommand - with argument
        result, level = repl.validation_manager.validate_command("db.drop", ["users"])

        assert result.status == "valid"


class TestContextInjection:
    """Test context factory and dependency injection."""

    def test_user_can_access_shared_context_in_commands(self):
        """GIVEN a REPL with context factory
        WHEN user executes command that uses context
        THEN context is available
        """

        def create_context():
            return {"user": "alice", "session_id": "test123"}

        repl = REPL(app_name="Test App", context_factory=create_context)

        @repl.cli.command()
        @click.pass_context
        def whoami(ctx):
            """Show current user."""
            user = ctx.obj["user"]
            print(f"User: {user}")

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Create context and invoke
            context = create_context()
            ctx = click.Context(repl.cli, obj=context)
            ctx.invoke(whoami)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "User: alice" in output

    def test_user_context_is_shared_across_commands(self):
        """GIVEN multiple commands using context
        WHEN commands modify context
        THEN changes are visible to other commands
        """

        def create_context():
            return {"counter": 0}

        repl = REPL(app_name="Test App", context_factory=create_context)

        @repl.cli.command()
        @click.pass_context
        def increment(ctx):
            """Increment counter."""
            ctx.obj["counter"] += 1
            print(f"Counter: {ctx.obj['counter']}")

        @repl.cli.command()
        @click.pass_context
        def show(ctx):
            """Show counter."""
            print(f"Counter: {ctx.obj['counter']}")

        context = create_context()
        ctx = click.Context(repl.cli, obj=context)

        # Increment
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            ctx.invoke(increment)
            output1 = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "Counter: 1" in output1

        # Show (should see updated value)
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            ctx.invoke(show)
            output2 = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "Counter: 1" in output2


class TestPluginDiscovery:
    """Test plugin discovery and registration."""

    def test_repl_discovers_no_plugins_when_none_registered(self):
        """GIVEN a REPL with no plugins in entry points
        WHEN REPL is created
        THEN no plugins are loaded
        """
        repl = REPL(app_name="Test App", plugin_group="nonexistent.group")

        # Should have no plugins loaded
        assert len(repl.plugins) == 0

    def test_repl_has_builtin_commands(self):
        """GIVEN a newly created REPL
        WHEN REPL is initialized
        THEN built-in commands are registered
        """
        repl = REPL(app_name="Test App")

        # Should have built-in print and error commands
        assert "print" in repl.cli.commands
        assert "error" in repl.cli.commands

    def test_builtin_print_command_works(self):
        """GIVEN the built-in print command
        WHEN user executes it
        THEN it prints to stdout
        """
        repl = REPL(app_name="Test App")

        print_cmd = repl.cli.commands["print"]

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            ctx = click.Context(print_cmd)
            ctx.invoke(print_cmd, text=("Hello", "World"))
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "Hello World" in output

    def test_builtin_error_command_writes_to_stderr(self):
        """GIVEN the built-in error command
        WHEN user executes it
        THEN it writes to stderr
        """
        repl = REPL(app_name="Test App")

        error_cmd = repl.cli.commands["error"]

        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            ctx = click.Context(error_cmd)
            ctx.invoke(error_cmd, text=("Error", "message"))
            output = sys.stderr.getvalue()
        finally:
            sys.stderr = old_stderr

        assert "Error message" in output


class TestREPLConfiguration:
    """Test REPL configuration loading."""

    def test_repl_loads_default_config_when_no_path_provided(self):
        """GIVEN no config path
        WHEN REPL is created
        THEN default config is loaded
        """
        repl = REPL(app_name="Test App")

        # Should have config loaded
        assert repl.config is not None
        assert hasattr(repl.config, "appearance")
        assert hasattr(repl.config, "colors")

    def test_repl_loads_custom_config(self, tmp_path):
        """GIVEN a custom config file
        WHEN REPL is created with config path
        THEN custom config is loaded
        """
        config_file = tmp_path / "custom_config.yaml"
        config_file.write_text("""
appearance:
  ascii_art_text: "Test App"
  box_width: 80
colors:
  divider: "cyan"
""")

        repl = REPL(app_name="Test App", config_path=str(config_file))

        assert repl.config.appearance.ascii_art_text == "Test App"
        assert repl.config.appearance.box_width == 80


class TestValidationRuleExtraction:
    """Test validation rule extraction from Click commands."""

    def test_extraction_identifies_required_arguments(self):
        """GIVEN a command with required arguments
        WHEN validation rules are extracted
        THEN required arguments are identified
        """
        repl = REPL(app_name="Test App")

        @repl.cli.command()
        @click.argument("source", required=True)
        @click.argument("dest", required=True)
        def copy(source, dest):
            """Copy file."""
            pass

        repl.validation_manager.introspect_commands()

        rule = repl.validation_manager.validation_rules.get("copy")
        assert rule is not None
        assert rule.level == "required"
        assert "source" in rule.required_args
        assert "dest" in rule.required_args
        assert rule.arg_count_min == 2

    def test_extraction_identifies_optional_arguments(self):
        """GIVEN a command with optional arguments
        WHEN validation rules are extracted
        THEN optional arguments are identified
        """
        repl = REPL(app_name="Test App")

        @repl.cli.command()
        @click.argument("name", default="World")
        def hello(name):
            """Say hello."""
            pass

        repl.validation_manager.introspect_commands()

        rule = repl.validation_manager.validation_rules.get("hello")
        assert rule is not None
        assert rule.level == "optional"
        assert "name" in rule.optional_args

    def test_extraction_identifies_choice_constraints(self):
        """GIVEN a command with Click.Choice
        WHEN validation rules are extracted
        THEN choice constraints are captured
        """
        repl = REPL(app_name="Test App")

        @repl.cli.command()
        @click.argument("level", type=click.Choice(["debug", "info", "error"]))
        def setlevel(level):
            """Set log level."""
            pass

        repl.validation_manager.introspect_commands()

        rule = repl.validation_manager.validation_rules.get("setlevel")
        assert rule is not None
        assert "level" in rule.choice_params
        assert set(rule.choice_params["level"]) == {"debug", "info", "error"}

    def test_extraction_identifies_required_options(self):
        """GIVEN a command with required options
        WHEN validation rules are extracted
        THEN required options are identified
        """
        repl = REPL(app_name="Test App")

        @repl.cli.command()
        @click.option("--config", "-c", required=True)
        def run(config):
            """Run with config."""
            pass

        repl.validation_manager.introspect_commands()

        rule = repl.validation_manager.validation_rules.get("run")
        assert rule is not None
        assert rule.level == "required"
        assert "config" in rule.required_options
        assert "--config" in rule.option_names["config"]
        assert "-c" in rule.option_names["config"]
