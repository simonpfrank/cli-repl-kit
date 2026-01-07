"""Core REPL class with plugin discovery."""

import io
import sys
import re
from contextlib import redirect_stderr, redirect_stdout
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import click
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.margins import Margin, ScrollbarMargin
from prompt_toolkit.lexers import Lexer

from cli_repl_kit.core.banner_builder import BannerBuilder
from cli_repl_kit.core.command_executor import CommandExecutor
from cli_repl_kit.core.formatting import ANSILexer, formatted_text_to_ansi_string
from cli_repl_kit.core.key_bindings import KeyBindingManager
from cli_repl_kit.core.layout import ConditionalScrollbarMargin, LayoutBuilder
from cli_repl_kit.core.output_capture import OutputCapture
from cli_repl_kit.core.state import REPLState
from cli_repl_kit.core.validation_manager import ValidationManager
from cli_repl_kit.plugins.base import ValidationResult
from cli_repl_kit.plugins.validation import ValidationRule


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
        plugin_group: str = "repl.commands",
        config_path: Optional[str] = None,
    ):
        """Initialize the REPL.

        Args:
            app_name: Name of the application (used in prompts, history, etc.)
            context_factory: Function that returns context dict for dependency injection.
                           Defaults to returning empty dict.
            cli_group: Existing Click group to use. If None, creates a new one.
            plugin_group: Entry point group name for discovering plugins.
                        Defaults to "repl.commands".
            config_path: Optional path to custom config file. If None, uses default.
        """
        self.app_name = app_name
        self.context_factory = context_factory or (lambda: {})
        self.cli = cli_group or click.Group()
        self.plugin_group = plugin_group

        # Add built-in test commands
        self._register_builtin_commands()

        # Load config
        import cli_repl_kit
        from cli_repl_kit.core.config import Config

        if config_path:
            self.config = Config.load(config_path, app_name=app_name)
        else:
            # Use default config from package
            default_config = Path(cli_repl_kit.__file__).parent / "config.yaml"
            self.config = Config.load(str(default_config), app_name=app_name)

        # Initialize validation system
        self.plugins: List[Any] = []  # List of loaded plugin instances
        self.validation_manager = ValidationManager(self.cli)

        # Discover and load plugins
        self._load_plugins()

    def _register_builtin_commands(self):
        """Register built-in test commands."""

        @self.cli.command(name="print")
        @click.argument("text", nargs=-1, required=True)
        def print_command(text):
            """Test stdout capture by printing text."""
            message = " ".join(text)
            print(message)

        @self.cli.command(name="error")
        @click.argument("text", nargs=-1, required=True)
        def error_command(text):
            """Test stderr capture by writing to stderr."""
            message = " ".join(text)
            sys.stderr.write(message + "\n")

    def _load_plugins(self):
        """Discover and register plugins from entry points."""
        discovered = entry_points(group=self.plugin_group)

        for ep in discovered:
            # Load the plugin class
            plugin_class = ep.load()

            # Instantiate the plugin
            plugin = plugin_class()

            # Store plugin instance
            self.plugins.append(plugin)

            # Register the plugin's commands
            plugin.register(self.cli, self.context_factory)

        # AUTO-GENERATE validation rules from Click commands
        self.validation_manager.introspect_commands()

    def _validate_command(
        self, cmd_name: str, cmd_args: List[str]
    ) -> Tuple[ValidationResult, Optional[str]]:
        """Validate command before execution.

        Args:
            cmd_name: Command name (e.g., "deploy", "config.set")
            cmd_args: List of command arguments

        Returns:
            Tuple of (ValidationResult, validation_level or None)
        """
        return self.validation_manager.validate_command(cmd_name, cmd_args)

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
        """Start interactive REPL session with custom layout.

        Args:
            prompt_text: Prompt string
            enable_agent_mode: If True, allows free text input
        """
        from cli_repl_kit.core.completion import SlashCommandCompleter

        # Build command dictionary for completion
        commands_dict = {}
        if hasattr(self.cli, "commands"):
            for name, cmd in self.cli.commands.items():
                commands_dict[name] = cmd.help or "No description"

        # Create completer
        completer = SlashCommandCompleter(commands_dict, cli_group=self.cli)

        # Setup history file from config
        history_location = self.config.history.file_location
        history_file = Path(history_location).expanduser()

        # Create parent directory if it doesn't exist
        if history_file.parent != Path("."):
            history_file.parent.mkdir(parents=True, exist_ok=True)

        # Build intro banner
        banner_builder = BannerBuilder(self.config, self.app_name)
        intro_text = banner_builder.build()

        # State - typed state object (replaces mutable dict)
        state = REPLState()

        # Create output buffer (not read_only so we can write, but focusable=False prevents user edits)
        output_buffer = Buffer(name="output")

        # Convert intro banner to ANSI for buffer
        intro_text_ansi = ""
        for line in intro_text:
            if isinstance(line, list):
                intro_text_ansi += formatted_text_to_ansi_string(line, self.config) + "\n"
            else:
                intro_text_ansi += str(line) + "\n"

        # Initialize buffer with intro banner
        output_buffer.document = Document(
            text=intro_text_ansi, cursor_position=len(intro_text_ansi)
        )

        # Helper to add output to buffer with auto-scroll
        def append_to_output_buffer(line):
            """Add a line to output buffer with auto-scroll behavior.

            Args:
                line: Either a string or FormattedText list [(style, text), ...]
            """
            if isinstance(line, list):
                # FormattedText - convert to ANSI string
                text = formatted_text_to_ansi_string(line, self.config)
            else:
                text = str(line)

            # Append to buffer using Document
            current = output_buffer.text
            if current:
                new_text = current + text + "\n"
            else:
                new_text = text + "\n"

            # Update buffer document with auto-scroll to bottom
            output_buffer.document = Document(
                text=new_text, cursor_position=len(new_text)
            )

        # Create command executor
        command_executor = CommandExecutor(
            config=self.config,
            cli=self.cli,
            validate_callback=self._validate_command,
            append_output_callback=append_to_output_buffer,
        )

        # Update completions on text change
        def on_text_changed(_):
            text = input_buffer.text

            # Update state tracking
            state.slash_command_active = text.startswith("/")
            state.is_multiline = "\n" in text

            # Handle placeholder removal when user starts typing
            if state.placeholder_active and bool(
                re.search("<[a-z0-9_]+>", text)
            ):  # SF 6/1 for any text arg
                # if state.placeholder_active and "<text>" in text:
                cursor_pos = input_buffer.cursor_position
                # If user is typing after the placeholder start position
                if cursor_pos > state.placeholder_start:
                    # Find and remove the <text> placeholder
                    placeholder = re.search(
                        "<[a-z0-9_]+>", text
                    )  # SF 6/1 for any text arg
                    # placeholder_idx = text.find("<text>")
                    if bool(placeholder):
                        # if placeholder_idx >= 0:
                        # Remove the placeholder from the buffer
                        new_text = (
                            text[: placeholder.span()[0]]
                            + text[placeholder.span()[1] + 6 :]
                        )
                        # Adjust cursor position
                        new_cursor = (
                            cursor_pos - 6
                            if cursor_pos > placeholder.start()
                            else cursor_pos
                        )
                        input_buffer.text = new_text
                        input_buffer.cursor_position = new_cursor
                        state.placeholder_active = False
                        return  # Exit early since we modified the buffer

            if text.startswith("/"):
                from prompt_toolkit.completion import CompleteEvent
                from prompt_toolkit.document import Document

                doc = Document(text, len(text))
                completions = list(completer.get_completions(doc, CompleteEvent()))
                state.completions = completions
                state.selected_idx = 0 if completions else -1

                # Set menu_keep_visible when menu is shown
                if completions:
                    state.menu_keep_visible = True
            else:
                state.completions = []
                state.selected_idx = -1
                # Clear menu_keep_visible when user types non-slash
                state.menu_keep_visible = False

        # Create input buffer
        input_buffer = Buffer(
            multiline=True,
            complete_while_typing=True,
            completer=completer,
            history=FileHistory(str(history_file)),
            on_text_changed=on_text_changed,
        )

        # Create layout using LayoutBuilder
        layout_builder = LayoutBuilder(self.config, state, self.cli)
        layout = layout_builder.build(input_buffer, output_buffer)

        # Command execution callback for key bindings
        def execute_command_callback(text: str, event: Any) -> None:
            """Execute a command via CommandExecutor."""
            command_executor.execute_command(text, input_buffer, enable_agent_mode, event)

        # Create key bindings using KeyBindingManager
        key_manager = KeyBindingManager(
            config=self.config,
            state=state,
            input_buffer=input_buffer,
            output_buffer=output_buffer,
            cli=self.cli,
            layout_builder=layout_builder,
            execute_callback=execute_command_callback,
        )
        kb = key_manager.create_bindings()

        # Create application
        app: Application[None] = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=True,
            mouse_support=True,  # Enable mouse scrolling
        )

        # Store references for API methods
        self._current_app = app
        self._current_state = state

        # Force immediate layout recalculation to fix input height timing issue
        # This ensures get_input_height() is evaluated with proper application context
        app.invalidate()

        # Global stdout/stderr capture
        stdout_capture = OutputCapture("stdout", append_to_output_buffer, self.config)
        stderr_capture = OutputCapture("stderr", append_to_output_buffer, self.config)

        # Redirect global stdout/stderr
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        try:
            app.run()
        finally:
            # Restore original streams
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    # API methods for status and info lines

    def _substitute_ansi_codes(self, text: str) -> str:
        r"""Substitute ${ansi.COLOR} patterns with ANSI escape codes from config.

        Args:
            text: Text containing ${ansi.COLOR} patterns

        Returns:
            Text with ANSI codes substituted

        Example:
            "${ansi.red}Error${ansi.reset}" -> "\x1b[31mError\x1b[0m"
        """
        import re

        # Find all ${ansi.XXX} patterns
        pattern = r"\$\{ansi\.([^}]+)\}"

        def replace_ansi(match):
            color_name = match.group(1)
            return self.config.ansi_colors.get(color_name, match.group(0))

        return re.sub(pattern, replace_ansi, text)

    def set_status(self, text: str, style: str = ""):
        """Update status line content.

        Args:
            text: Text to display (supports ${ansi.COLOR} substitution)
            style: Optional style (e.g., "yellow", "green bold")

        Example:
            set_status("${ansi.red}Error occurred${ansi.reset}")
        """
        # Substitute ANSI color codes
        text = self._substitute_ansi_codes(text)

        if hasattr(self, "_current_state"):
            if style:
                self._current_state.status_text = [(style, text)]
            else:
                self._current_state.status_text = [("", text)]
            if hasattr(self, "_current_app"):
                self._current_app.invalidate()

    def clear_status(self):
        """Clear status line."""
        if hasattr(self, "_current_state"):
            self._current_state.status_text = []
            if hasattr(self, "_current_app"):
                self._current_app.invalidate()

    def set_info(self, text: str, style: str = ""):
        """Update info line content.

        Args:
            text: Text to display (supports ${ansi.COLOR} substitution)
            style: Optional style (e.g., "cyan", "bold")

        Example:
            set_info("${ansi.cyan}Tip: ${ansi.reset}Try /help")
        """
        # Substitute ANSI color codes
        text = self._substitute_ansi_codes(text)

        if hasattr(self, "_current_state"):
            if style:
                self._current_state.info_text = [(style, text)]
            else:
                self._current_state.info_text = [("", text)]
            if hasattr(self, "_current_app"):
                self._current_app.invalidate()

    def clear_info(self):
        """Clear info line."""
        if hasattr(self, "_current_state"):
            self._current_state.info_text = []
            if hasattr(self, "_current_app"):
                self._current_app.invalidate()
