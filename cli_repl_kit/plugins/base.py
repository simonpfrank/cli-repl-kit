"""Base class for REPL command plugins."""
from abc import ABC, abstractmethod
from typing import Callable, Dict, Any
import click


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
