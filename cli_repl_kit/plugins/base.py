"""Base class for REPL command plugins."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Dict, Any, Optional, Literal, List
import click


@dataclass
class ValidationResult:
    """Result of command validation.

    Attributes:
        status: "valid", "invalid", or "warning"
        message: Optional explanation of validation result
    """

    status: Literal["valid", "invalid", "warning"]
    message: Optional[str] = None

    def is_valid(self) -> bool:
        """Return True if validation passed (no blocking issues)."""
        return self.status in ("valid", "warning")

    def should_block(self) -> bool:
        """Return True if command should be blocked from execution."""
        return self.status == "invalid"

    def should_warn(self) -> bool:
        """Return True if warning should be displayed."""
        return self.status == "warning"


class CommandPlugin(ABC):
    """Base class for REPL command plugins.

    This abstract base class defines the interface that all command plugins must implement.
    Plugins are discovered via Python entry points and register their commands with the REPL.

    Example:
        ```python
        from cli_repl_kit.plugins.base import CommandPlugin
        import click

        class MyPlugin(CommandPlugin):
            @property
            def name(self):
                return "my_plugin"

            def register(self, cli, context_factory):
                @click.command()
                def hello():
                    '''Say hello!'''
                    print("Hello from my plugin!")

                cli.add_command(hello, name="hello")
        ```
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name for identification.

        Returns:
            str: A unique name for this plugin.
        """
        pass

    @abstractmethod
    def register(self, cli: click.Group, context_factory: Callable[[], Dict[str, Any]]) -> None:
        """Register commands with the CLI group.

        This method is called during REPL initialization to register the plugin's
        commands with the Click CLI group.

        Args:
            cli: Click group to register commands with.
            context_factory: Function that returns the context dict/object for dependency injection.
                           This can be called to get access to shared state (e.g., config, managers).
        """
        pass

    def get_validation_config(self) -> Dict[str, str]:
        """Return validation configuration for plugin commands.

        Maps command names to validation levels:
        - "required": Validate before execution, block if invalid
        - "optional": Validate before execution, warn but allow if invalid
        - "none": No validation (default)

        For subcommands, use dot notation: "config.set"

        Example:
            {
                "hello": "optional",        # Warning only
                "deploy": "required",       # Block if invalid
                "config.show": "none"       # No validation
            }

        Returns:
            Dict mapping command name -> validation level.
            Empty dict means no validation for any commands (default).
        """
        return {}

    def validate_command(
        self,
        cmd_name: str,
        cmd_args: List[str],
        parsed_args: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate command arguments before execution.

        Called when validation_config specifies validation for this command.

        Args:
            cmd_name: Name of the command (e.g., "deploy", "config.set")
            cmd_args: Raw argument list from user input
            parsed_args: Optional dict of parsed Click arguments (may be None)

        Returns:
            ValidationResult indicating valid, invalid, or warning status

        Example:
            def validate_command(self, cmd_name, cmd_args, parsed_args):
                if cmd_name == "deploy":
                    env = cmd_args[0] if cmd_args else None
                    if env not in ["dev", "staging", "prod"]:
                        return ValidationResult(
                            status="invalid",
                            message=f"Invalid environment: {env}"
                        )
                    if env == "prod":
                        return ValidationResult(
                            status="warning",
                            message="Deploying to production - use caution"
                        )
                return ValidationResult(status="valid")
        """
        return ValidationResult(status="valid")
