"""Base class for REPL command plugins."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Literal, Optional

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

    Validation is now automatic! Commands are validated based on Click decorators:
    - Required arguments (required=True) trigger "required" validation (blocks if missing)
    - Optional arguments (with defaults) trigger "optional" validation (warns if issues)
    - Choice types (click.Choice) automatically validate against allowed values
    - No manual validation methods needed!

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
                @click.argument("env", type=click.Choice(["dev", "prod"]))
                def deploy(env):
                    '''Deploy to environment (validated automatically!)'''
                    print(f"Deploying to {env}")

                cli.add_command(deploy, name="deploy")
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

        Validation is automatic based on Click decorators:
        - Use required=True for required arguments
        - Use type=click.Choice([...]) for enum validation
        - Use default=value for optional arguments

        Args:
            cli: Click group to register commands with.
            context_factory: Function that returns the context dict/object for dependency injection.
                           This can be called to get access to shared state (e.g., config, managers).
        """
        pass
