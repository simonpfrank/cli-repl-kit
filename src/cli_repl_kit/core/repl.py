"""Core REPL class with plugin discovery."""
from importlib.metadata import entry_points
from typing import Callable, Dict, Any, Optional
from pathlib import Path
import sys
import click
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from click_repl import repl


class REPL:
    """Main REPL class that discovers and loads command plugins.

    This class provides the core REPL functionality:
    - Discovers plugins via Python entry points
    - Registers plugin commands with a Click CLI group
    - Supports both interactive REPL mode and traditional CLI mode
    - Provides context injection for shared state

    Example:
        ```python
        from cli_repl_kit import REPL

        def my_context_factory():
            return {
                "config": load_config(),
                "database": connect_db()
            }

        repl = REPL(
            app_name="My App",
            context_factory=my_context_factory,
            plugin_group="my_app.commands"
        )

        repl.start()
        ```
    """

    def __init__(
        self,
        app_name: str,
        context_factory: Optional[Callable[[], Dict[str, Any]]] = None,
        cli_group: Optional[click.Group] = None,
        plugin_group: str = "repl.commands"
    ):
        """Initialize the REPL.

        Args:
            app_name: Name of the application (used in prompts, history, etc.)
            context_factory: Function that returns context dict for dependency injection.
                           Defaults to returning empty dict.
            cli_group: Existing Click group to use. If None, creates a new one.
            plugin_group: Entry point group name for discovering plugins.
                        Defaults to "repl.commands".
        """
        self.app_name = app_name
        self.context_factory = context_factory or (lambda: {})
        self.cli = cli_group or click.Group()
        self.plugin_group = plugin_group

        # Discover and load plugins
        self._load_plugins()

    def _load_plugins(self):
        """Discover and register plugins from entry points."""
        discovered = entry_points(group=self.plugin_group)

        for ep in discovered:
            # Load the plugin class
            plugin_class = ep.load()

            # Instantiate the plugin
            plugin = plugin_class()

            # Register the plugin's commands
            plugin.register(self.cli, self.context_factory)

    def start(self, prompt_text: str = "> ", enable_agent_mode: bool = False):
        """Start the REPL or execute CLI command.

        Args:
            prompt_text: Prompt string for interactive mode
            enable_agent_mode: If True, allows free text input (echoes back)

        This method:
        - Checks if CLI arguments were provided (traditional CLI mode)
        - If args provided: Executes command and exits
        - If no args: Starts interactive REPL mode with completion and history
        """
        # Check if we're in CLI mode (arguments provided) or REPL mode
        if len(sys.argv) > 1:
            # CLI mode: Execute command directly
            self.cli.main(standalone_mode=False, obj=self.context_factory())
        else:
            # REPL mode: Start interactive session
            self._start_repl(prompt_text, enable_agent_mode)

    def _start_repl(self, prompt_text: str, enable_agent_mode: bool):
        """Start interactive REPL session.

        Args:
            prompt_text: Prompt string
            enable_agent_mode: If True, allows free text input
        """
        from cli_repl_kit.core.completion import SlashCommandCompleter
        from rich.console import Console
        from cli_repl_kit.ui.styles import APP_THEME

        console = Console(theme=APP_THEME)

        # Show welcome message
        console.print(f"\n[bold cyan]{self.app_name}[/bold cyan]")
        console.print(f"[dim]Type /help for commands, /quit to exit[/dim]\n")

        # Build command dictionary for completion
        commands_dict = {}
        if hasattr(self.cli, "commands"):
            for name, cmd in self.cli.commands.items():
                commands_dict[name] = cmd.help or "No description"

        # Create completer
        completer = SlashCommandCompleter(commands_dict, cli_group=self.cli)

        # Setup history file
        history_dir = Path.home() / f".{self.app_name.lower().replace(' ', '-')}"
        history_dir.mkdir(exist_ok=True)
        history_file = history_dir / "history"

        # Completion styling (simple purple theme)
        completion_style = Style.from_dict({
            "completion-menu.completion": "noinherit #808080",
            "completion-menu.completion.current": "noinherit #6B4FBB bold",
        })

        # Prompt kwargs for click_repl
        prompt_kwargs = {
            "message": prompt_text,
            "history": FileHistory(str(history_file)),
            "completer": completer,
            "complete_while_typing": True,
            "style": completion_style,
        }

        # Monkey-patch click_repl to strip leading slash
        import click_repl._repl as repl_module
        original_execute = repl_module._execute_internal_and_sys_cmds

        def execute_with_slash_stripping(command, allow_internal, allow_system):
            """Strip leading / and handle agent mode."""
            # Strip leading / if present
            if command.startswith("/"):
                command = command[1:]
            elif enable_agent_mode and command.strip():
                # Agent mode: echo back the input
                console.print(f"[dim]Echo:[/dim] {command}")
                return None

            try:
                return original_execute(command, allow_internal, allow_system)
            except click.exceptions.ClickException as e:
                console.print(f"[red]Error:[/red] {e.format_message()}")
                return None
            except Exception as e:
                error_msg = str(e)
                if "No such command" in error_msg or "no command named" in error_msg.lower():
                    console.print(f"[red]Unknown command.[/red] Try /help")
                else:
                    console.print(f"[red]Error:[/red] {error_msg}")
                return None

        # Temporarily replace the function
        repl_module._execute_internal_and_sys_cmds = execute_with_slash_stripping

        # Create context with factory
        ctx = click.Context(self.cli, obj=self.context_factory())

        try:
            # Start the REPL
            repl(ctx, prompt_kwargs=prompt_kwargs)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            sys.exit(0)
        except Exception:
            # Clean exit from /quit or /exit
            sys.exit(0)
        finally:
            # Restore original function
            repl_module._execute_internal_and_sys_cmds = original_execute
