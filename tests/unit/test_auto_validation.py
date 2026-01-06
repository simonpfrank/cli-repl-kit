"""Unit tests for automatic validation system."""
import click

from cli_repl_kit.plugins.validation import ValidationRule


class TestValidationRuleDataclass:
    """Test ValidationRule dataclass creation and behavior."""

    def test_validation_rule_creation_with_all_fields(self):
        """Test creating ValidationRule with all fields specified."""
        cmd = click.Command("test")
        rule = ValidationRule(
            level="required",
            required_args=["name", "email"],
            optional_args=["age"],
            arg_count_min=2,
            arg_count_max=3,
            choice_params={"env": ["dev", "prod"]},
            type_params={"port": click.INT},
            required_options=["config"],
            option_names={"config": ["--config", "-c"]},
            click_command=cmd,
        )

        assert rule.level == "required"
        assert rule.required_args == ["name", "email"]
        assert rule.optional_args == ["age"]
        assert rule.arg_count_min == 2
        assert rule.arg_count_max == 3
        assert rule.choice_params == {"env": ["dev", "prod"]}
        assert rule.type_params == {"port": click.INT}
        assert rule.required_options == ["config"]
        assert rule.option_names == {"config": ["--config", "-c"]}
        assert rule.click_command == cmd

    def test_validation_rule_defaults(self):
        """Test ValidationRule with default values."""
        rule = ValidationRule(level="none")

        assert rule.level == "none"
        assert rule.required_args == []
        assert rule.optional_args == []
        assert rule.arg_count_min == 0
        assert rule.arg_count_max == 0
        assert rule.choice_params == {}
        assert rule.type_params == {}
        assert rule.required_options == []
        assert rule.option_names == {}
        assert rule.click_command is None

    def test_validation_rule_required_level(self):
        """Test ValidationRule with required level."""
        rule = ValidationRule(
            level="required",
            required_args=["name"],
        )

        assert rule.level == "required"
        assert "name" in rule.required_args

    def test_validation_rule_optional_level(self):
        """Test ValidationRule with optional level."""
        rule = ValidationRule(
            level="optional",
            optional_args=["name"],
        )

        assert rule.level == "optional"
        assert "name" in rule.optional_args

    def test_validation_rule_none_level_for_no_params(self):
        """Test ValidationRule with none level when no parameters."""
        rule = ValidationRule(level="none")

        assert rule.level == "none"
        assert len(rule.required_args) == 0
        assert len(rule.optional_args) == 0

    def test_validation_rule_choice_params(self):
        """Test ValidationRule stores choice parameters correctly."""
        rule = ValidationRule(
            level="required",
            choice_params={
                "environment": ["dev", "staging", "prod"],
                "log_level": ["debug", "info", "warning", "error"],
            },
        )

        assert "environment" in rule.choice_params
        assert rule.choice_params["environment"] == ["dev", "staging", "prod"]
        assert "log_level" in rule.choice_params
        assert len(rule.choice_params["log_level"]) == 4

    def test_validation_rule_arg_count_constraints(self):
        """Test ValidationRule arg count min/max."""
        rule = ValidationRule(
            level="required",
            arg_count_min=1,
            arg_count_max=3,
        )

        assert rule.arg_count_min == 1
        assert rule.arg_count_max == 3

    def test_validation_rule_unlimited_args(self):
        """Test ValidationRule with unlimited args (nargs=-1)."""
        rule = ValidationRule(
            level="required",
            arg_count_min=0,
            arg_count_max=-1,  # -1 means unlimited
        )

        assert rule.arg_count_min == 0
        assert rule.arg_count_max == -1

    def test_validation_rule_stores_click_command_reference(self):
        """Test ValidationRule stores reference to Click command."""

        @click.command()
        @click.argument("name")
        def test_cmd(name):
            pass

        rule = ValidationRule(
            level="required",
            click_command=test_cmd,
        )

        assert rule.click_command is test_cmd
        assert isinstance(rule.click_command, click.Command)

    def test_validation_rule_option_names(self):
        """Test ValidationRule stores option name variants."""
        rule = ValidationRule(
            level="required",
            option_names={
                "config": ["--config", "-c"],
                "verbose": ["--verbose", "-v"],
            },
        )

        assert "config" in rule.option_names
        assert "--config" in rule.option_names["config"]
        assert "-c" in rule.option_names["config"]
        assert "verbose" in rule.option_names
        assert len(rule.option_names["verbose"]) == 2


class TestClickIntrospection:
    """Test automatic validation rule extraction from Click commands."""

    def test_extract_required_argument(self):
        """Test extracting rule from command with required argument."""
        from cli_repl_kit import REPL

        @click.command()
        @click.argument("name", required=True)
        def cmd(name):
            pass

        repl = REPL(app_name="test")
        rule = repl._extract_validation_rule(cmd, "cmd")

        assert rule.level == "required"
        assert "name" in rule.required_args
        assert rule.arg_count_min == 1

    def test_extract_optional_argument(self):
        """Test extracting rule from command with optional argument (has default)."""
        from cli_repl_kit import REPL

        @click.command()
        @click.argument("name", default="World")
        def cmd(name):
            pass

        repl = REPL(app_name="test")
        rule = repl._extract_validation_rule(cmd, "cmd")

        assert rule.level == "optional"
        assert "name" in rule.optional_args

    def test_extract_choice_parameter(self):
        """Test extracting choice constraints from click.Choice type."""
        from cli_repl_kit import REPL

        @click.command()
        @click.argument("env", type=click.Choice(["dev", "prod"]))
        def cmd(env):
            pass

        repl = REPL(app_name="test")
        rule = repl._extract_validation_rule(cmd, "cmd")

        assert rule.level == "required"
        assert "env" in rule.choice_params
        assert rule.choice_params["env"] == ["dev", "prod"]

    def test_extract_multiple_required_args(self):
        """Test extracting multiple required arguments."""
        from cli_repl_kit import REPL

        @click.command()
        @click.argument("source", required=True)
        @click.argument("dest", required=True)
        def cmd(source, dest):
            pass

        repl = REPL(app_name="test")
        rule = repl._extract_validation_rule(cmd, "cmd")

        assert rule.level == "required"
        assert "source" in rule.required_args
        assert "dest" in rule.required_args
        assert rule.arg_count_min == 2

    def test_extract_variable_args_nargs(self):
        """Test extracting nargs=-1 parameter handling."""
        from cli_repl_kit import REPL

        @click.command()
        @click.argument("files", nargs=-1, required=True)
        def cmd(files):
            pass

        repl = REPL(app_name="test")
        rule = repl._extract_validation_rule(cmd, "cmd")

        assert rule.level == "required"
        assert "files" in rule.required_args
        assert rule.arg_count_max == -1  # Unlimited

    def test_extract_required_option(self):
        """Test extracting required option (--flag with required=True)."""
        from cli_repl_kit import REPL

        @click.command()
        @click.option("--config", "-c", required=True)
        def cmd(config):
            pass

        repl = REPL(app_name="test")
        rule = repl._extract_validation_rule(cmd, "cmd")

        assert rule.level == "required"
        assert "config" in rule.required_options
        assert "--config" in rule.option_names["config"]
        assert "-c" in rule.option_names["config"]

    def test_extract_command_with_no_params(self):
        """Test command with no parameters has 'none' level."""
        from cli_repl_kit import REPL

        @click.command()
        def cmd():
            pass

        repl = REPL(app_name="test")
        rule = repl._extract_validation_rule(cmd, "cmd")

        assert rule.level == "none"
        assert len(rule.required_args) == 0
        assert len(rule.optional_args) == 0

    def test_extract_subcommand_path(self):
        """Test subcommands use dot notation (config.set)."""
        from cli_repl_kit import REPL

        @click.group()
        def config():
            pass

        @config.command()
        @click.argument("key")
        @click.argument("value")
        def set(key, value):
            pass

        repl = REPL(app_name="test")
        rule = repl._extract_validation_rule(set, "config.set")

        assert rule.level == "required"
        assert rule.click_command == set


class TestCommandTreeWalking:
    """Test command tree introspection."""

    def test_introspect_simple_commands(self):
        """Test walking flat command list."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.command()
        @click.argument("name")
        def hello(name):
            pass

        @click.command()
        def quit():
            pass

        repl.cli.add_command(hello, name="hello")
        repl.cli.add_command(quit, name="quit")

        repl._introspect_commands()

        assert "hello" in repl.validation_rules
        assert "quit" in repl.validation_rules
        assert repl.validation_rules["hello"].level == "required"
        assert repl.validation_rules["quit"].level == "none"

    def test_introspect_command_groups(self):
        """Test walking Click groups with subcommands."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.group()
        def config():
            pass

        @config.command()
        @click.argument("key")
        def get(key):
            pass

        @config.command()
        @click.argument("key")
        @click.argument("value")
        def set(key, value):
            pass

        repl.cli.add_command(config, name="config")

        repl._introspect_commands()

        assert "config.get" in repl.validation_rules
        assert "config.set" in repl.validation_rules
        assert repl.validation_rules["config.get"].level == "required"
        assert repl.validation_rules["config.set"].level == "required"

    def test_introspect_stores_rules_correctly(self):
        """Test that rules are stored in dict with correct keys."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.command()
        @click.argument("text", nargs=-1, required=True)
        def print_cmd(text):
            pass

        repl.cli.add_command(print_cmd, name="print")

        repl._introspect_commands()

        # print command is already registered in _register_builtin_commands
        # so it should be in validation_rules
        assert "print" in repl.validation_rules
        rule = repl.validation_rules["print"]
        assert isinstance(rule, ValidationRule)
        assert rule.level == "required"


class TestAutoValidationExecution:
    """Test automatic validation execution."""

    def test_validate_command_valid(self):
        """Test validation succeeds for valid command."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.command()
        @click.argument("name", required=True)
        def hello(name):
            pass

        repl.cli.add_command(hello, name="hello")
        repl._introspect_commands()

        result, level = repl._validate_command_auto("hello", ["Alice"])

        assert result.status == "valid"
        assert level == "required"

    def test_validate_missing_required_arg(self):
        """Test validation fails when required arg missing."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.command()
        @click.argument("name", required=True)
        def hello(name):
            pass

        repl.cli.add_command(hello, name="hello")
        repl._introspect_commands()

        result, level = repl._validate_command_auto("hello", [])

        assert result.status == "invalid"
        assert "required" in result.message.lower() or "missing" in result.message.lower()
        assert level == "required"

    def test_validate_invalid_choice(self):
        """Test validation fails for invalid choice value."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.command()
        @click.argument("env", type=click.Choice(["dev", "prod"]))
        def deploy(env):
            pass

        repl.cli.add_command(deploy, name="deploy")
        repl._introspect_commands()

        result, level = repl._validate_command_auto("deploy", ["staging"])

        assert result.status == "invalid"
        assert level == "required"

    def test_validate_valid_choice(self):
        """Test validation succeeds for valid choice value."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.command()
        @click.argument("env", type=click.Choice(["dev", "prod"]))
        def deploy(env):
            pass

        repl.cli.add_command(deploy, name="deploy")
        repl._introspect_commands()

        result, level = repl._validate_command_auto("deploy", ["dev"])

        assert result.status == "valid"
        assert level == "required"

    def test_validate_optional_arg_missing(self):
        """Test validation succeeds when optional arg missing."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.command()
        @click.argument("name", default="World")
        def hello(name):
            pass

        repl.cli.add_command(hello, name="hello")
        repl._introspect_commands()

        result, level = repl._validate_command_auto("hello", [])

        assert result.status == "valid"
        assert level == "optional"

    def test_validate_none_level_skips(self):
        """Test commands with 'none' level skip validation."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.command()
        def quit():
            pass

        repl.cli.add_command(quit, name="quit")
        repl._introspect_commands()

        result, level = repl._validate_command_auto("quit", [])

        assert result.status == "valid"
        assert level is None  # none level returns None

    def test_validate_too_few_args(self):
        """Test validation fails when too few args provided."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.command()
        @click.argument("source", required=True)
        @click.argument("dest", required=True)
        def copy(source, dest):
            pass

        repl.cli.add_command(copy, name="copy")
        repl._introspect_commands()

        result, level = repl._validate_command_auto("copy", ["file.txt"])

        assert result.status == "invalid"
        assert level == "required"

    def test_validate_command_not_in_rules(self):
        """Test validation returns valid for unknown commands."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        result, level = repl._validate_command_auto("unknown", [])

        assert result.status == "valid"
        assert level is None

    def test_validate_command_wrapper(self):
        """Test that _validate_command calls _validate_command_auto."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.command()
        @click.argument("name", required=True)
        def hello(name):
            pass

        repl.cli.add_command(hello, name="hello")
        repl._introspect_commands()

        # Call the wrapper
        result, level = repl._validate_command("hello", ["Alice"])

        assert result.status == "valid"
        assert level == "required"

    def test_validate_multiple_args_valid(self):
        """Test validation succeeds with multiple valid args."""
        from cli_repl_kit import REPL

        repl = REPL(app_name="test")

        @click.command()
        @click.argument("source", required=True)
        @click.argument("dest", required=True)
        def copy(source, dest):
            pass

        repl.cli.add_command(copy, name="copy")
        repl._introspect_commands()

        result, level = repl._validate_command_auto("copy", ["file1.txt", "file2.txt"])

        assert result.status == "valid"
        assert level == "required"
