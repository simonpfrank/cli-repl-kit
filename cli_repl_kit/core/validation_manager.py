"""Validation manager for REPL commands.

This module provides the ValidationManager class that handles automatic
validation rule extraction from Click commands and command validation.
"""
from typing import Dict, List, Optional, Tuple

import click

from cli_repl_kit.plugins.base import ValidationResult
from cli_repl_kit.plugins.validation import ValidationRule


class ValidationManager:
    """Manages command validation rules and validation execution.

    Extracts validation rules from Click command introspection and
    provides validation for commands before execution. Automatically
    analyzes Click commands to determine required arguments, optional
    parameters, and choice constraints.

    Attributes:
        cli: Click CLI group containing commands
        validation_rules: Dict mapping command_path -> ValidationRule

    Example:
        >>> import click
        >>> cli = click.Group()
        >>>
        >>> @cli.command()
        >>> @click.argument("name", required=True)
        >>> def hello(name):
        ...     print(f"Hello {name}")
        >>>
        >>> manager = ValidationManager(cli)
        >>> manager.introspect_commands()
        >>> result, level = manager.validate_command("hello", ["World"])
        >>> print(result.status)
        valid
    """

    def __init__(self, cli: click.Group):
        """Initialize validation manager.

        Args:
            cli: Click CLI group to introspect for validation rules

        Example:
            >>> import click
            >>> cli = click.Group()
            >>> manager = ValidationManager(cli)
            >>> manager.cli == cli
            True
        """
        self.cli = cli
        self.validation_rules: Dict[str, ValidationRule] = {}

    def introspect_commands(self) -> None:
        """Walk command tree and extract validation rules for all commands.

        Analyzes all commands and subcommands in the CLI group, extracting
        their parameter requirements and storing validation rules for later use.

        Example:
            >>> import click
            >>> cli = click.Group()
            >>> @cli.command()
            >>> @click.argument("file", required=True)
            >>> def read(file):
            ...     pass
            >>> manager = ValidationManager(cli)
            >>> manager.introspect_commands()
            >>> "read" in manager.validation_rules
            True
        """
        for cmd_name, cmd in self.cli.commands.items():
            if isinstance(cmd, click.Group):
                # Handle group with subcommands
                for subcmd_name, subcmd in cmd.commands.items():
                    subcmd_path = f"{cmd_name}.{subcmd_name}"
                    rule = self._extract_validation_rule(subcmd, subcmd_path)
                    self.validation_rules[subcmd_path] = rule
            else:
                # Regular command
                rule = self._extract_validation_rule(cmd, cmd_name)
                self.validation_rules[cmd_name] = rule

    def _extract_validation_rule(
        self, cmd: click.Command, cmd_path: str
    ) -> ValidationRule:
        """Extract validation rule from Click command.

        Analyzes a Click command's parameters to build a ValidationRule that
        captures argument requirements, option constraints, and type information.

        Args:
            cmd: Click command object
            cmd_path: Full command path (e.g., "config.set" for subcommands)

        Returns:
            ValidationRule with inferred constraints from command parameters

        Example:
            >>> import click
            >>> @click.command()
            >>> @click.argument("env", type=click.Choice(["dev", "prod"]))
            >>> def deploy(env):
            ...     pass
            >>> manager = ValidationManager(click.Group())
            >>> rule = manager._extract_validation_rule(deploy, "deploy")
            >>> rule.level
            'required'
            >>> "env" in rule.choice_params
            True
        """
        rule = ValidationRule(
            level="none",
            required_args=[],
            optional_args=[],
            arg_count_min=0,
            arg_count_max=0,
            choice_params={},
            type_params={},
            required_options=[],
            option_names={},
            click_command=cmd,
        )

        has_required_params = False
        has_optional_params = False

        for param in cmd.params:
            if isinstance(param, click.Argument):
                # Handle arguments
                if param.name is None:
                    continue

                is_required = param.required

                if is_required:
                    rule.required_args.append(param.name)
                    has_required_params = True
                else:
                    rule.optional_args.append(param.name)
                    has_optional_params = True

                # Track argument count constraints
                if param.nargs == -1:
                    rule.arg_count_max = -1  # Unlimited
                else:
                    nargs = param.nargs if param.nargs else 1
                    rule.arg_count_min += nargs if is_required else 0
                    if rule.arg_count_max != -1:
                        rule.arg_count_max += nargs

                # Track type constraints
                rule.type_params[param.name] = param.type

                # Track choice constraints
                if isinstance(param.type, click.Choice):
                    rule.choice_params[param.name] = list(param.type.choices)
                    has_required_params = True

            elif isinstance(param, click.Option):
                # Handle options
                if param.name is None:
                    continue

                if param.required:
                    rule.required_options.append(param.name)
                    has_required_params = True

                # Store option names (--env, -e)
                rule.option_names[param.name] = param.opts

                # Track type constraints
                rule.type_params[param.name] = param.type

                # Track choice constraints
                if isinstance(param.type, click.Choice):
                    rule.choice_params[param.name] = list(param.type.choices)

        # Infer validation level
        if has_required_params:
            rule.level = "required"
        elif has_optional_params:
            rule.level = "optional"
        else:
            rule.level = "none"

        return rule

    def validate_command(
        self, cmd_path: str, cmd_args: List[str]
    ) -> Tuple[ValidationResult, Optional[str]]:
        """Validate command using auto-generated rules.

        Uses Click's native validation by attempting to parse arguments
        against the command's expected parameters. Returns validation
        results without executing the command.

        Args:
            cmd_path: Command path (e.g., "deploy" or "config.set")
            cmd_args: Raw argument list from user

        Returns:
            Tuple of (ValidationResult, validation_level or None).
            ValidationResult has status "valid" or "invalid" and optional message.
            validation_level is "required", "optional", or None.

        Example:
            >>> import click
            >>> cli = click.Group()
            >>> @cli.command()
            >>> @click.argument("name", required=True)
            >>> def greet(name):
            ...     print(f"Hello {name}")
            >>> manager = ValidationManager(cli)
            >>> manager.introspect_commands()
            >>> result, level = manager.validate_command("greet", ["Alice"])
            >>> result.status
            'valid'
            >>> result, level = manager.validate_command("greet", [])
            >>> result.status
            'invalid'
        """
        # Check if command has validation rule
        if cmd_path not in self.validation_rules:
            return (ValidationResult(status="valid"), None)

        rule = self.validation_rules[cmd_path]

        # No validation needed
        if rule.level == "none" or rule.click_command is None:
            return (ValidationResult(status="valid"), None)

        # Use Click's native validation by attempting to parse args
        # IMPORTANT: parse_args modifies the list, so pass a copy
        try:
            ctx = click.Context(rule.click_command)
            rule.click_command.parse_args(ctx, cmd_args.copy())
            return (ValidationResult(status="valid"), rule.level)

        except click.exceptions.MissingParameter as e:
            param_name = e.param.name if e.param else "unknown"
            return (
                ValidationResult(
                    status="invalid",
                    message=f"Missing required argument: {param_name}",
                ),
                rule.level,
            )

        except click.exceptions.BadParameter as e:
            return (ValidationResult(status="invalid", message=str(e)), rule.level)

        except click.exceptions.UsageError as e:
            return (ValidationResult(status="invalid", message=str(e)), rule.level)

        except Exception as e:
            return (
                ValidationResult(
                    status="invalid", message=f"Validation error: {str(e)}"
                ),
                rule.level,
            )
