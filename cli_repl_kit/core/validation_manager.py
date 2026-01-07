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
    provides validation for commands before execution.

    Attributes:
        cli: Click CLI group containing commands
        validation_rules: Dict mapping command_path -> ValidationRule
    """

    def __init__(self, cli: click.Group):
        """Initialize validation manager.

        Args:
            cli: Click CLI group to introspect for validation rules
        """
        self.cli = cli
        self.validation_rules: Dict[str, ValidationRule] = {}

    def introspect_commands(self) -> None:
        """Walk command tree and extract validation rules for all commands."""
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

        Args:
            cmd: Click command object
            cmd_path: Full command path (e.g., "config.set" for subcommands)

        Returns:
            ValidationRule with inferred constraints
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

        Args:
            cmd_path: Command path (e.g., "deploy" or "config.set")
            cmd_args: Raw argument list from user

        Returns:
            Tuple of (ValidationResult, validation_level or None)
        """
        # Check if command has validation rule
        if cmd_path not in self.validation_rules:
            return (ValidationResult(status="valid"), None)

        rule = self.validation_rules[cmd_path]

        # No validation needed
        if rule.level == "none" or rule.click_command is None:
            return (ValidationResult(status="valid"), None)

        # Use Click's native validation by attempting to parse args
        try:
            ctx = click.Context(rule.click_command)
            rule.click_command.parse_args(ctx, cmd_args)
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
