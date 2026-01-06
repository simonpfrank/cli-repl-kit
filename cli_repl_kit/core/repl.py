"""Core REPL class with plugin discovery."""

import io
import sys
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

from cli_repl_kit.plugins.base import ValidationResult


def formatted_to_ansi(formatted_text, config):
    """Convert FormattedText list to ANSI-escaped string.

    Args:
        formatted_text: List of (style, text) tuples
        config: Config object with ansi_colors

    Returns:
        String with ANSI escape codes
    """
    if not formatted_text:
        return ""

    ansi_colors = config.ansi_colors
    reset = ansi_colors.reset

    result = []
    for style, text in formatted_text:
        # Handle empty style
        if not style or style == "":
            result.append(text)
            continue

        # Try to look up style in config
        # Replace spaces with underscores for combined styles like "cyan bold" -> "cyan_bold"
        style_key = style.replace(" ", "_")

        # Try to get ANSI code from config
        ansi_code = None
        if hasattr(ansi_colors, style_key):
            ansi_code = getattr(ansi_colors, style_key)
        elif hasattr(ansi_colors, style):
            ansi_code = getattr(ansi_colors, style)

        if ansi_code:
            result.append(f"{ansi_code}{text}{reset}")
        else:
            # Unknown style, just append text without ANSI codes
            result.append(text)

    return "".join(result)


class ANSILexer(Lexer):
    """Lexer that interprets ANSI escape codes and returns styled fragments."""

    def lex_document(self, document):
        """Return a function that returns styled fragments for a line.

        Args:
            document: prompt_toolkit Document

        Returns:
            Function that takes line number and returns FormattedText
        """
        lines = document.lines

        def get_line(lineno):
            """Get styled fragments for a specific line number.

            Args:
                lineno: Line number (0-indexed)

            Returns:
                List of (style, text) tuples (FormattedText)
            """
            if lineno < len(lines):
                line = lines[lineno]
                # Parse ANSI codes and return FormattedText
                return list(ANSI(line).__pt_formatted_text__())
            return []

        return get_line


class OutputCapture(io.StringIO):
    """Capture stdout/stderr and redirect to output buffer."""

    def __init__(self, stream_type, output_callback, config):
        """Initialize capture.

        Args:
            stream_type: "stdout" or "stderr"
            output_callback: Function to call with captured text (FormattedText)
            config: Config for styling
        """
        super().__init__()
        self.stream_type = stream_type
        self.output_callback = output_callback
        self.config = config

    def write(self, text):
        """Capture text and send to output.

        Args:
            text: Text to capture
        """
        if not text or text == "\n":
            return

        # Add to output with appropriate styling
        if self.stream_type == "stderr":
            # Use error color from config
            self.output_callback([(self.config.colors.error, text)])
        else:
            # Default (no style) for stdout
            self.output_callback([("", text)])

    def flush(self):
        """Flush (no-op for our purposes)."""
        pass


class ConditionalScrollbarMargin(Margin):
    """Scrollbar margin that only renders when a condition is met."""

    def __init__(self, buffer, max_lines=10, display_arrows=True):
        self.buffer = buffer
        self.max_lines = max_lines
        self.scrollbar = ScrollbarMargin(display_arrows=display_arrows)

    def get_width(self, ui_content):
        """Return width only if condition is met."""
        line_count = max(1, self.buffer.text.count('\n') + 1) if self.buffer.text else 1
        if line_count >= self.max_lines:
            return self.scrollbar.get_width(ui_content)
        return 0

    def create_margin(self, window_render_info, width, height):
        """Render scrollbar only if at max lines."""
        line_count = max(1, self.buffer.text.count('\n') + 1) if self.buffer.text else 1
        if line_count >= self.max_lines:
            return self.scrollbar.create_margin(window_render_info, width, height)
        # Return a function that returns empty formatted text (accept any args)
        return lambda *args, **kwargs: []


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
        self.plugins = []  # List of loaded plugin instances
        self.command_validators = {}  # Maps command_name -> (plugin, validation_level)

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

        @self.cli.command(name="status")
        @click.argument("text", nargs=-1, required=False)
        def status_command(text):
            """Set or clear status line text."""
            # Note: This command needs access to set_status() from REPL
            # Will be called during REPL execution where set_status is available
            pass  # Implementation will be in REPL context

        @self.cli.command(name="info")
        @click.argument("text", nargs=-1, required=False)
        def info_command(text):
            """Set or clear info line text."""
            # Note: This command needs access to set_info() from REPL
            # Will be called during REPL execution where set_info is available
            pass  # Implementation will be in REPL context

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

            # Store validation configuration
            validation_config = plugin.get_validation_config()
            for cmd_name, validation_level in validation_config.items():
                if validation_level in ("required", "optional"):
                    self.command_validators[cmd_name] = (plugin, validation_level)

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
        # Check if command has validation configured
        if cmd_name not in self.command_validators:
            return (ValidationResult(status="valid"), None)

        plugin, validation_level = self.command_validators[cmd_name]

        # Call plugin's validation method
        try:
            # Note: parsed_args can be added later if needed
            result = plugin.validate_command(cmd_name, cmd_args, parsed_args=None)
            return (result, validation_level)
        except Exception as e:
            # If validation throws, treat as validation error
            return (
                ValidationResult(
                    status="invalid", message=f"Validation error: {str(e)}"
                ),
                validation_level,
            )

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

        # Box width (inner content area)
        box_width = self.config.appearance.box_width

        # Get banner text from config (allows customization)
        banner_text = self.config.appearance.ascii_art_text

        # ASCII art mappings for common text values
        # This allows nice ASCII art for known values, plain text for others
        ascii_art_map = {
            "Hello World": [
                "  _   _      _ _        __        __         _     _ ",
                " | | | | ___| | | ___   \\ \\      / /__  _ __| | __| |",
                " | |_| |/ _ \\ | |/ _ \\   \\ \\ /\\ / / _ \\| '__| |/ _` |",
                " |  _  |  __/ | | (_) |   \\ V  V / (_) | |  | | (_| |",
                " |_| |_|\\___|_|_|\\___/     \\_/\\_/ \\___/|_|  |_|\\__,_|",
            ],
            "CLI REPL Kit": [
                "   ____ _     ___   ____  _____ ____  _       _  ___ _   ",
                "  / ___| |   |_ _| |  _ \\| ____|  _ \\| |     | |/ (_) |_ ",
                " | |   | |    | |  | |_) |  _| | |_) | |     | ' /| | __|",
                " | |___| |___ | |  |  _ <| |___|  __/| |___  | . \\| | |_ ",
                "  \\____|_____|___| |_| \\_\\_____|_|   |_____| |_|\\_\\_|\\__|",
            ],
        }

        # Use ASCII art if available, otherwise just use the text centered
        if banner_text in ascii_art_map:
            ascii_art = ascii_art_map[banner_text]
        else:
            # Plain text fallback - center the text
            ascii_art = [banner_text]

        # Create intro banner
        intro_lines = [
            [("cyan", "╭" + "─" * box_width + "╮")],
            [("cyan", "│" + " " * box_width + "│")],
        ]

        # Add ASCII art lines
        for art_line in ascii_art:
            padding = box_width - len(art_line) - 2
            intro_lines.append([
                ("cyan", "│  "),
                ("cyan bold", art_line),
                ("", " " * padding),
                ("cyan", "│"),
            ])

        intro_lines.extend([
            [("cyan", "│" + " " * box_width + "│")],
            [("cyan", "│"), ("bold", f"    {self.app_name}"), ("yellow", " v0.1.0"), ("", " " * (box_width - len(self.app_name) - 11)), ("cyan", "│")],
            [("cyan", "│"), ("", "    Type "), ("green", "/quit"), ("", " to exit or "), ("green", "/hello <text>"), ("", " to greet"), ("", " " * (box_width - 48)), ("cyan", "│")],
            [("cyan", "│"), ("", "    Press "), ("yellow", "Ctrl+J"), ("", " for multi-line input, "), ("yellow", "Enter"), ("", " to submit"), ("", " " * (box_width - 54)), ("cyan", "│")],
            [("cyan", "│" + " " * box_width + "│")],
            [("cyan", "╰" + "─" * box_width + "╯")],
            [("", "")],
            [("green bold", "Ready!"), ("", " (/ for commands). Use "), ("yellow", "↑↓"), ("", " arrows to navigate menu, "), ("yellow", "Tab"), ("", " or "), ("yellow", "Enter"), ("", " to select")],
            [("", "")],
        ])

        intro_text = intro_lines

        # State - use a mutable container so closures can modify it
        state = {
            # PRESERVED Phase C.1: "output_lines": intro_text.copy(),
            # PRESERVED Phase C.1: "output_scroll_offset": 0,  # Track scroll position (0 = at bottom)
            # PRESERVED Phase C.1: "user_scrolled_output": False,  # True when user has scrolled up
            "completions": [],
            "selected_idx": 0,
            "placeholder_active": False,  # Track if <text> placeholder is shown
            "placeholder_start": 0,  # Cursor position where placeholder starts
            "status_text": [],  # Status line content (FormattedText)
            "info_text": [],  # Info line content (FormattedText)
            "slash_command_active": False,  # True when input starts with /
            "is_multiline": False,  # True when input has \n
            "menu_keep_visible": False,  # Keep menu expanded after command to avoid jarring jumps
        }

        # Helper to get argument info for a command
        def get_command_args(cmd_name, subcmd_name=None):
            """Get argument placeholder text for a command."""
            if not hasattr(self.cli, "commands"):
                return None
            if cmd_name not in self.cli.commands:
                return None

            cmd = self.cli.commands[cmd_name]

            # If it's a group and we have a subcommand
            if subcmd_name and hasattr(cmd, "commands"):
                if subcmd_name in cmd.commands:
                    cmd = cmd.commands[subcmd_name]
                else:
                    return None

            # Check for arguments
            if hasattr(cmd, "params"):
                for param in cmd.params:
                    if isinstance(param, click.Argument):
                        return f"<{param.name}>"
            return None

        # Grey divider
        divider_color = self.config.colors.divider
        def grey_line():
            return Window(
                height=1,
                content=FormattedTextControl(
                    text=lambda: [(divider_color, "─" * 200)]
                ),
            )

        # PRESERVED: Original FormattedText-based output rendering (Phase C.1)
        # # Helper to add output with auto-scroll support
        # def add_output_line(line):
        #     """Add a line to output with auto-scroll behavior.
        #
        #     If user hasn't scrolled up, reset scroll to bottom.
        #     If user has scrolled up (scroll lock), preserve their position.
        #     """
        #     state["output_lines"].append(line)
        #     # Auto-scroll to bottom unless user has scrolled up
        #     if not state["user_scrolled_output"]:
        #         state["output_scroll_offset"] = 0
        #
        # # Render output area - show recent lines
        # def render_output():
        #     """Render output with scroll offset support.
        #
        #     Scroll offset is from the bottom - 0 means show latest content at bottom.
        #     Positive offset means show earlier content (scrolled up).
        #     """
        #     lines = state["output_lines"]
        #     scroll_offset = state["output_scroll_offset"]
        #
        #     # If scrolled up, show content from (total - offset) position
        #     # Otherwise show all content (prompt_toolkit handles display from bottom)
        #     if scroll_offset > 0 and len(lines) > scroll_offset:
        #         # Show content up to (total - offset) lines from bottom
        #         end_idx = len(lines) - scroll_offset
        #         lines = lines[:end_idx]
        #
        #     result = []
        #     for line in lines:
        #         if isinstance(line, list):
        #             result.extend(line)
        #         else:
        #             result.append(("", str(line)))
        #         result.append(("", "\n"))
        #     return result

        # NEW Phase D: Buffer-based output with ANSI support
        # Create output buffer (not read_only since window is focusable=False)
        output_buffer = Buffer(name="output")

        # Convert intro banner to ANSI for buffer
        intro_text_ansi = ""
        for line in intro_text:
            if isinstance(line, list):
                intro_text_ansi += formatted_to_ansi(line, self.config) + "\n"
            else:
                intro_text_ansi += str(line) + "\n"

        # Initialize buffer with intro banner
        output_buffer.document = Document(
            text=intro_text_ansi,
            cursor_position=len(intro_text_ansi)
        )

        # Helper to add output to buffer with auto-scroll
        def add_output_line(line):
            """Add a line to output buffer with auto-scroll behavior.

            Args:
                line: Either a string or FormattedText list [(style, text), ...]
            """
            if isinstance(line, list):
                # FormattedText - convert to ANSI string
                text = formatted_to_ansi(line, self.config)
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
                text=new_text,
                cursor_position=len(new_text)
            )

        def format_command_display(command_text, has_error=False, has_warning=False):
            """Format command for display with icons and proper styling.

            Args:
                command_text: The full command text (with or without /)
                has_error: Whether the command resulted in an error (red bullet)
                has_warning: Whether the command has a warning (yellow warning icon)

            Returns:
                List of lines to display (each line is FormattedText)
            """
            # Remove leading / if present
            if command_text.startswith("/"):
                command_text = command_text[1:]

            # Parse command and arguments
            parts = command_text.split(maxsplit=1)
            if not parts:
                return []

            cmd_name = parts[0]
            has_args = len(parts) > 1
            args_text = parts[1] if has_args else ""

            # Parse subcommands from args
            subcommand_chain = []
            remaining_text = args_text

            if has_args and hasattr(self.cli, "commands"):
                # Try to find subcommands by walking the command tree
                current_cmd = self.cli.commands.get(cmd_name)
                arg_words = args_text.split()

                for i, word in enumerate(arg_words):
                    # Check if current command is a group with this subcommand
                    if current_cmd and hasattr(current_cmd, "commands") and word in current_cmd.commands:
                        subcommand_chain.append(word)
                        current_cmd = current_cmd.commands[word]
                    else:
                        # Rest is free text
                        remaining_text = " ".join(arg_words[i:])
                        break
                else:
                    # All args were subcommands
                    remaining_text = ""

            # Choose icon based on command structure and status
            if has_warning:
                # Optional validation warning - yellow warning icon
                icon = self.config.symbols.warning  # ⚠
                icon_color = self.config.colors.warning  # yellow
            elif has_args:
                # Command with arguments - grey square
                icon = self.config.symbols.command_with_args  # ■
                icon_color = self.config.colors.grey
            else:
                # Simple command - success/error icon with color
                if has_error:
                    icon = self.config.symbols.command_error  # ●
                    icon_color = self.config.colors.error  # red
                else:
                    icon = self.config.symbols.command_success  # ●
                    icon_color = self.config.colors.success  # green

            # Build command display line with subcommands
            cmd_display = [
                (icon_color, icon + " "),
                (self.config.colors.grey, "/" + cmd_name)
            ]

            # Add subcommands with arrow icons
            arrow = " → "
            for subcmd in subcommand_chain:
                cmd_display.append((self.config.colors.grey, arrow + subcmd))

            # If no remaining text, return single line
            if not remaining_text:
                return [cmd_display]

            # If has remaining text, add it on next line with indent
            lines = [cmd_display]

            # Add remaining text with indent symbol
            indent_symbol = self.config.symbols.indent  # ⎿
            indent_prefix = [(self.config.colors.grey, indent_symbol + " ")]

            # Handle multi-line remaining text
            text_lines = remaining_text.split("\n")
            for i, text_line in enumerate(text_lines):
                if i == 0:
                    # First line with indent symbol
                    lines.append(indent_prefix + [("", text_line)])
                else:
                    # Continuation lines indented by 2 spaces
                    lines.append([("", "  " + text_line)])

            return lines

        # Render status line
        def render_status():
            """Render status line content."""
            if not state["status_text"]:
                return []
            return state["status_text"]

        # Render info line
        def render_info():
            """Render info line content."""
            if not state["info_text"]:
                return []
            return state["info_text"]

        # Render completion menu
        def render_completions():
            if not state["completions"]:
                return []

            text = input_buffer.text
            is_top_level = " " not in text.rstrip()

            # Calculate visible window of completions based on menu height
            menu_height = self.config.windows.menu.height
            total_completions = len(state["completions"])
            selected_idx = state["selected_idx"]

            # Calculate the window of completions to show
            if total_completions <= menu_height:
                # Show all if they fit
                start_idx = 0
                end_idx = total_completions
            else:
                # Show a window centered around the selected item
                # Try to keep selected item in the middle
                half_window = menu_height // 2
                start_idx = max(0, selected_idx - half_window)
                end_idx = min(total_completions, start_idx + menu_height)

                # Adjust if we hit the end
                if end_idx == total_completions:
                    start_idx = max(0, end_idx - menu_height)

            lines = []
            for i in range(start_idx, end_idx):
                comp = state["completions"][i]
                cmd_text = str(comp.text)
                help_text = comp.display_meta if hasattr(comp, "display_meta") else ""
                if isinstance(help_text, list):
                    help_text = "".join(t for _, t in help_text)
                else:
                    help_text = str(help_text) if help_text else ""

                prefix = "/" if is_top_level else ""
                formatted = f"{prefix}{cmd_text:<19} {help_text}"

                highlight_color = self.config.colors.highlight
                grey_color = self.config.colors.grey
                style = f"{highlight_color} bold" if i == state["selected_idx"] else grey_color
                lines.append((style, formatted))
                if i < end_idx - 1:
                    lines.append(("", "\n"))
            return lines

        # Update completions on text change
        def on_text_changed(_):
            text = input_buffer.text

            # Update state tracking
            state["slash_command_active"] = text.startswith("/")
            state["is_multiline"] = "\n" in text

            # Handle placeholder removal when user starts typing
            if state["placeholder_active"] and "<text>" in text:
                cursor_pos = input_buffer.cursor_position
                # If user is typing after the placeholder start position
                if cursor_pos > state["placeholder_start"]:
                    # Find and remove the <text> placeholder
                    placeholder_idx = text.find("<text>")
                    if placeholder_idx >= 0:
                        # Remove the placeholder from the buffer
                        new_text = text[:placeholder_idx] + text[placeholder_idx + 6:]
                        # Adjust cursor position
                        new_cursor = cursor_pos - 6 if cursor_pos > placeholder_idx else cursor_pos
                        input_buffer.text = new_text
                        input_buffer.cursor_position = new_cursor
                        state["placeholder_active"] = False
                        return  # Exit early since we modified the buffer

            if text.startswith("/"):
                from prompt_toolkit.completion import CompleteEvent
                from prompt_toolkit.document import Document

                doc = Document(text, len(text))
                completions = list(completer.get_completions(doc, CompleteEvent()))
                state["completions"] = completions
                state["selected_idx"] = 0 if completions else -1

                # Set menu_keep_visible when menu is shown
                if completions:
                    state["menu_keep_visible"] = True
            else:
                state["completions"] = []
                state["selected_idx"] = -1
                # Clear menu_keep_visible when user types non-slash
                state["menu_keep_visible"] = False

        # Create input buffer
        input_buffer = Buffer(
            multiline=True,
            complete_while_typing=True,
            completer=completer,
            history=FileHistory(str(history_file)),
            on_text_changed=on_text_changed,
        )

        # PRESERVED: Original FormattedTextControl output_window (Phase C.1)
        # # Windows
        # output_window = Window(
        #     content=FormattedTextControl(text=render_output),
        #     height=D(weight=1),  # Take remaining space
        #     wrap_lines=True,
        #     always_hide_cursor=True,  # Display only - no cursor
        # )

        # NEW Phase D: Output window with BufferControl + ANSILexer
        output_window = Window(
            content=BufferControl(
                buffer=output_buffer,
                focusable=False,
                include_default_input_processors=False,
                lexer=ANSILexer(),  # Render ANSI codes as styled text
            ),
            height=D(weight=1),  # Take remaining space
            wrap_lines=True,
            always_hide_cursor=True,  # Display only - no cursor
        )

        # Function to show prompt (configurable, with dynamic continuation spacing)
        prompt_char = self.config.prompt.character  # e.g., "> " or "Agent >"

        def get_input_prompt(line_number, wrap_count):
            """Show configurable prompt on first line, matching indent on continuation lines."""
            if line_number == 0 and wrap_count == 0:
                return [("bold", prompt_char)]
            else:
                # Continuation spacing matches prompt length for alignment
                return [("", " " * len(prompt_char))]

        # Dynamic height based on buffer content (no max - grows endlessly)
        def get_input_height():
            """Calculate input height based on number of lines in buffer."""
            # Count newlines in buffer to determine line count
            text = input_buffer.text
            if not text:
                # Empty buffer - use initial height from config
                return D(preferred=self.config.windows.input.initial_height)
            else:
                # Calculate based on actual content
                line_count = max(1, text.count('\n') + 1)
                # No max limit - input can grow endlessly within terminal limits
                return D(preferred=line_count)

        input_window = Window(
            content=BufferControl(
                buffer=input_buffer,
                lexer=None,
                input_processors=[],
                include_default_input_processors=False,
            ),
            height=get_input_height,  # Dynamic height: 1 line when empty, grows endlessly
            wrap_lines=True,
            get_line_prefix=get_input_prompt,  # Add > prompt
            dont_extend_height=True,  # Don't extend beyond calculated height
            # NO scrollbar - input grows endlessly, no internal scrolling
            # NO scroll_offsets - was causing 4-line initial height bug
        )

        # Status and info windows
        status_window = Window(
            content=FormattedTextControl(text=render_status),
            height=self.config.windows.status.height,
            wrap_lines=False,  # Truncate overflow
        )

        # Dynamic info height - show 1 line when info text is set, otherwise 0
        def get_info_height():
            """Calculate info height dynamically based on whether info is set."""
            if state["info_text"]:
                return D(preferred=1, min=1, max=1)
            else:
                return D(preferred=0, min=0, max=0)

        info_window = Window(
            content=FormattedTextControl(text=render_info),
            height=get_info_height,  # Dynamic height based on info text
            wrap_lines=False,  # Truncate overflow
        )

        # Dynamic menu height - shows preferred height when slash command active,
        # otherwise minimal height to save space
        menu_preferred_height = self.config.windows.menu.height

        def get_menu_height():
            """Calculate menu height dynamically.

            When slash command is active with completions, show full menu height.
            Keep menu visible after command execution to avoid jarring position jumps.
            Only collapse when user explicitly types non-slash input or clears.
            """
            if (state["slash_command_active"] and state["completions"]) or state["menu_keep_visible"]:
                # Show full menu when slash command active OR when keeping visible after execution
                return D(preferred=menu_preferred_height)
            else:
                # Zero height when not active - completely hidden
                return D(preferred=0, min=0)

        menu_window = Window(
            content=FormattedTextControl(text=render_completions),
            height=get_menu_height,  # Dynamic height based on slash command state
            wrap_lines=True,
        )

        # Layout with 5 windows
        layout = Layout(
            HSplit([
                output_window,
                status_window,
                grey_line(),
                input_window,
                grey_line(),
                info_window,
                menu_window,
            ])
        )

        # Key bindings
        kb = KeyBindings()

        @kb.add("c-c")
        def exit_app(event):
            event.app.exit()

        @kb.add("escape")
        def clear_input(event):
            """Clear the input buffer on ESC."""
            event.current_buffer.text = ""
            event.current_buffer.cursor_position = 0
            state["placeholder_active"] = False
            state["menu_keep_visible"] = False  # Collapse menu when clearing input
            event.app.invalidate()

        @kb.add("c-j")
        def insert_newline(event):
            event.current_buffer.insert_text("\n")

        @kb.add("up")
        def handle_up(event):
            """Context-dependent up arrow handling."""
            buffer = event.current_buffer

            # Context 1: Slash command active with > 1 option - navigate menu
            if state["slash_command_active"] and len(state["completions"]) > 1:
                if state["selected_idx"] > 0:
                    state["selected_idx"] -= 1
                    event.app.invalidate()
                return

            # Context 2: Multi-line input - move cursor up one line
            if state["is_multiline"]:
                buffer.cursor_up()
                event.app.invalidate()
                return

            # Context 3: Single-line, cursor at start - navigate history
            if buffer.cursor_position == 0:
                # Navigate to previous command in history
                buffer.history_backward()
                event.app.invalidate()
                return

            # Context 4: Single-line, cursor not at start - move to start (safety)
            buffer.cursor_position = 0
            event.app.invalidate()

        @kb.add("down")
        def handle_down(event):
            """Context-dependent down arrow handling."""
            buffer = event.current_buffer

            # Context 1: Slash command active with > 1 option - navigate menu
            if state["slash_command_active"] and len(state["completions"]) > 1:
                if state["selected_idx"] < len(state["completions"]) - 1:
                    state["selected_idx"] += 1
                    event.app.invalidate()
                return

            # Context 2: Multi-line input - move cursor down one line
            if state["is_multiline"]:
                buffer.cursor_down()
                event.app.invalidate()
                return

            # Context 3: Single-line, cursor at start - navigate history
            if buffer.cursor_position == 0:
                # Navigate to next command in history
                buffer.history_forward()
                event.app.invalidate()
                return

            # Context 4: Single-line, cursor not at start - move to start (safety)
            buffer.cursor_position = 0
            event.app.invalidate()

        # Mouse wheel routing (context-dependent)
        # Note: Mouse wheel scrolling in prompt_toolkit is handled automatically
        # by the windows with mouse_support=True

        # Page Up/Down for output scrolling
        page_scroll_lines = 10  # Number of lines to scroll per page

        @kb.add("pageup")
        def scroll_output_up(event):
            """Scroll output buffer up by one page."""
            output_buffer.cursor_up(count=page_scroll_lines)
            event.app.invalidate()

        @kb.add("pagedown")
        def scroll_output_down(event):
            """Scroll output buffer down by one page."""
            output_buffer.cursor_down(count=page_scroll_lines)
            event.app.invalidate()

        @kb.add("tab")
        def do_tab(event):
            """Complete command and add argument placeholder if needed."""
            if not state["completions"] or state["selected_idx"] < 0:
                return

            comp = state["completions"][state["selected_idx"]]
            buffer = event.current_buffer

            # Delete what the completion replaces
            if comp.start_position:
                buffer.delete_before_cursor(-comp.start_position)

            # Insert completion
            buffer.insert_text(comp.text)

            # Check if this command/subcommand needs arguments
            parts = buffer.text.lstrip("/").split()
            cmd_name = parts[0] if parts else ""
            subcmd_name = parts[1] if len(parts) > 1 else None

            # Check if it's a group (needs subcommand)
            is_group = False
            if hasattr(self.cli, "commands") and cmd_name in self.cli.commands:
                cmd = self.cli.commands[cmd_name]
                is_group = hasattr(cmd, "commands")

            if is_group and not subcmd_name:
                # It's a group, add space to trigger subcommand completions
                buffer.insert_text(" ")
            else:
                # Check for argument placeholder
                arg_placeholder = get_command_args(cmd_name, subcmd_name)
                if arg_placeholder:
                    buffer.insert_text(" " + arg_placeholder)
                    # Position cursor at start of placeholder (on the <)
                    cursor_pos = buffer.cursor_position - len(arg_placeholder)
                    buffer.cursor_position = cursor_pos
                    state["placeholder_active"] = True
                    state["placeholder_start"] = cursor_pos

            event.app.invalidate()

        @kb.add("space")
        def do_space(event):
            """Handle space - may trigger placeholder after command."""
            buffer = event.current_buffer
            text = buffer.text.strip()

            # Check if we're completing a command with space
            if text.startswith("/") and " " not in text:
                # First space after /command - check for exact match
                cmd_name = text[1:]  # Remove /
                if hasattr(self.cli, "commands") and cmd_name in self.cli.commands:
                    cmd = self.cli.commands[cmd_name]

                    # Check if it's a group
                    if hasattr(cmd, "commands"):
                        # Group - just add space for subcommand
                        buffer.insert_text(" ")
                    else:
                        # Regular command - check for args
                        arg_placeholder = get_command_args(cmd_name)
                        if arg_placeholder:
                            buffer.insert_text(" " + arg_placeholder)
                            cursor_pos = buffer.cursor_position - len(arg_placeholder)
                            buffer.cursor_position = cursor_pos
                            state["placeholder_active"] = True
                            state["placeholder_start"] = cursor_pos
                        else:
                            buffer.insert_text(" ")
                    event.app.invalidate()
                    return

            # Check if this is space after a subcommand
            parts = text.lstrip("/").split()
            if len(parts) == 2:  # /cmd subcmd<space>
                cmd_name, subcmd_name = parts
                if hasattr(self.cli, "commands") and cmd_name in self.cli.commands:
                    cmd = self.cli.commands[cmd_name]
                    if hasattr(cmd, "commands") and subcmd_name in cmd.commands:
                        arg_placeholder = get_command_args(cmd_name, subcmd_name)
                        if arg_placeholder:
                            buffer.insert_text(" " + arg_placeholder)
                            cursor_pos = buffer.cursor_position - len(arg_placeholder)
                            buffer.cursor_position = cursor_pos
                            state["placeholder_active"] = True
                            state["placeholder_start"] = cursor_pos
                            event.app.invalidate()
                            return

            # Default: just insert space
            buffer.insert_text(" ")
            event.app.invalidate()

        @kb.add("enter")
        def do_enter(event):
            """Execute command."""
            buffer = event.current_buffer
            original_text = buffer.text  # Preserve original with blank lines
            text = original_text.strip()  # Use stripped for execution

            # Remove placeholder if still present
            if "<text>" in text:
                text = text.replace(" <text>", "").replace("<text>", "")

            # Auto-complete if partial match or just "/"
            if state["completions"] and state["selected_idx"] >= 0 and text.startswith("/"):
                comp = state["completions"][state["selected_idx"]]
                parts = text.split(maxsplit=1)
                first_word = parts[0][1:] if parts else ""  # Remove /
                rest_of_text = parts[1] if len(parts) > 1 else ""

                # Auto-complete if just "/" or if it's a partial match
                should_autocomplete = (
                    text == "/" or  # Just slash
                    (first_word and first_word != comp.text and comp.text.startswith(first_word))  # Partial match
                )

                if should_autocomplete:
                    text = "/" + comp.text
                    if rest_of_text:
                        text += " " + rest_of_text

            if not text:
                return

            # Parse command name and args early for validation
            if text.startswith("/"):
                command = text[1:]
            elif enable_agent_mode:
                add_output_line([("cyan", "Echo: "), ("", text)])
                add_output_line([("", "")])  # Add blank line for consistency
                event.app.invalidate()
                return
            else:
                command = text

            args = command.split()
            if not args:
                return

            cmd_name = args[0]
            cmd_args = args[1:]

            # Check if command exists (before validation, so we can show red bullet for unknown commands)
            command_exists = (
                cmd_name in ["quit", "exit", "status", "info"] or  # Built-in commands
                (hasattr(self.cli, "commands") and cmd_name in self.cli.commands)  # Registered commands
            )

            # Validate command before showing icon
            validation_result, validation_level = self._validate_command(cmd_name, cmd_args)

            # Determine if command should be blocked
            should_block = False
            has_warning = False
            has_error = False

            if not command_exists:
                # Unknown command - show red bullet
                has_error = True
            elif validation_level == "required" and validation_result.should_block():
                should_block = True
                has_error = True
            elif validation_level == "optional" and validation_result.should_warn():
                has_warning = True
                has_error = False
            else:
                has_error = False

            # Format and display command with appropriate icon
            formatted_lines = format_command_display(
                text, has_error=has_error, has_warning=has_warning
            )
            for line in formatted_lines:
                add_output_line(line)

            # Display validation message if present
            if validation_result.message:
                if should_block:
                    add_output_line(
                        [("red", f"{self.config.symbols.error} {validation_result.message}")]
                    )
                elif has_warning:
                    add_output_line(
                        [("yellow", f"{self.config.symbols.warning} {validation_result.message}")]
                    )

            # Reset scroll lock on new command submission
            state["user_scrolled_output"] = False
            state["output_scroll_offset"] = 0

            # Block execution if validation failed with required level
            if should_block:
                # Don't add to history, don't clear buffer, don't execute
                add_output_line([("", "")])  # Add blank line for consistency
                event.app.invalidate()
                return

            # Add to history before clearing buffer (only if not blocked)
            buffer.append_to_history()

            # Clear buffer
            buffer.text = ""
            state["placeholder_active"] = False

            # Handle quit/exit
            if cmd_name in ["quit", "exit"]:
                add_output_line([("", "Goodbye!")])
                event.app.invalidate()
                event.app.exit()
                return

            # Handle built-in status command
            if cmd_name == "status":
                if cmd_args:
                    message = " ".join(cmd_args)
                    self.set_status(message)
                else:
                    self.clear_status()
                add_output_line([("", "")])  # Add blank line for consistency
                event.app.invalidate()
                return

            # Handle built-in info command
            if cmd_name == "info":
                if cmd_args:
                    message = " ".join(cmd_args)
                    self.set_info(message)
                else:
                    self.clear_info()
                add_output_line([("", "")])  # Add blank line for consistency
                event.app.invalidate()
                return

            # Execute command
            if hasattr(self.cli, "commands") and cmd_name in self.cli.commands:
                cmd = self.cli.commands[cmd_name]

                # Handle group commands
                if hasattr(cmd, "commands"):
                    if cmd_args and cmd_args[0] in cmd.commands:
                        subcmd = cmd.commands[cmd_args[0]]
                        subcmd_args = cmd_args[1:]
                        self._execute_click_command(subcmd, subcmd_args, state, add_output_line)
                    else:
                        # Just the group name, no subcommand
                        add_output_line([("", "")])
                else:
                    # Regular command
                    self._execute_click_command(cmd, cmd_args, state, add_output_line)
            else:
                add_output_line([("red", f"Unknown command: {cmd_name}")])

            # Add empty line after command output
            add_output_line([("", "")])

            event.app.invalidate()

        # Create application
        app = Application(
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
        stdout_capture = OutputCapture("stdout", add_output_line, self.config)
        stderr_capture = OutputCapture("stderr", add_output_line, self.config)

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

    def _execute_click_command(self, cmd, args, state, add_output_line=None):
        """Execute a Click command and capture output.

        Args:
            cmd: The Click command to execute
            args: Command arguments
            state: State dictionary
            add_output_line: Optional callback to add output with auto-scroll
        """
        # Fallback to direct append if no callback provided
        if add_output_line is None:

            def add_output_line(line):
                state["output_lines"].append(line)

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        try:
            ctx = click.Context(cmd)

            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                # For commands with nargs=-1, pass args as tuple
                if hasattr(cmd, "params"):
                    for param in cmd.params:
                        if isinstance(param, click.Argument) and param.nargs == -1:
                            # Pass as keyword argument with tuple
                            ctx.invoke(cmd, **{param.name: tuple(args)})
                            break
                    else:
                        # No nargs=-1 args, invoke normally
                        ctx.invoke(cmd, *args)
                else:
                    ctx.invoke(cmd, *args)
        except SystemExit:
            pass
        except click.exceptions.MissingParameter as e:
            add_output_line([("red", f"Missing argument: {e.param.name}")])
        except Exception as e:
            add_output_line([("red", f"Error: {str(e)}")])

        # Add output
        stdout_text = stdout_buf.getvalue()
        stderr_text = stderr_buf.getvalue()

        if stdout_text:
            for line in stdout_text.rstrip().split("\n"):
                add_output_line([("", line)])
        if stderr_text:
            for line in stderr_text.rstrip().split("\n"):
                add_output_line([("red", line)])

    # API methods for status and info lines

    def _substitute_ansi_codes(self, text: str) -> str:
        """Substitute ${ansi.COLOR} patterns with ANSI escape codes from config.

        Args:
            text: Text containing ${ansi.COLOR} patterns

        Returns:
            Text with ANSI codes substituted

        Example:
            "${ansi.red}Error${ansi.reset}" -> "\x1b[31mError\x1b[0m"
        """
        import re

        # Find all ${ansi.XXX} patterns
        pattern = r'\$\{ansi\.([^}]+)\}'

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
                self._current_state["status_text"] = [(style, text)]
            else:
                self._current_state["status_text"] = [("", text)]
            if hasattr(self, "_current_app"):
                self._current_app.invalidate()

    def clear_status(self):
        """Clear status line."""
        if hasattr(self, "_current_state"):
            self._current_state["status_text"] = []
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
                self._current_state["info_text"] = [(style, text)]
            else:
                self._current_state["info_text"] = [("", text)]
            if hasattr(self, "_current_app"):
                self._current_app.invalidate()

    def clear_info(self):
        """Clear info line."""
        if hasattr(self, "_current_state"):
            self._current_state["info_text"] = []
            if hasattr(self, "_current_app"):
                self._current_app.invalidate()
