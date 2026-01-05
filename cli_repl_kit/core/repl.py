"""Core REPL class with plugin discovery."""

from importlib.metadata import entry_points
from typing import Callable, Dict, Any, Optional
from pathlib import Path
import sys
import io
import click
from prompt_toolkit.history import FileHistory
from prompt_toolkit.layout import Layout, HSplit, Window, ScrollOffsets
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.margins import ScrollbarMargin, Margin
from prompt_toolkit.layout.screen import WritePosition
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.buffer import Buffer
from contextlib import redirect_stdout, redirect_stderr


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

        # Setup history file
        history_dir = Path.home() / f".{self.app_name.lower().replace(' ', '-')}"
        history_dir.mkdir(exist_ok=True)
        history_file = history_dir / "history"

        # Box width (inner content area)
        box_width = 140

        # ASCII art for app name
        ascii_art = [
            "  _   _      _ _        __        __         _     _ ",
            " | | | | ___| | | ___   \\ \\      / /__  _ __| | __| |",
            " | |_| |/ _ \\ | |/ _ \\   \\ \\ /\\ / / _ \\| '__| |/ _` |",
            " |  _  |  __/ | | (_) |   \\ V  V / (_) | |  | | (_| |",
            " |_| |_|\\___|_|_|\\___/     \\_/\\_/ \\___/|_|  |_|\\__,_|",
        ]

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
            "output_lines": intro_text.copy(),
            "completions": [],
            "selected_idx": 0,
            "placeholder_active": False,  # Track if <text> placeholder is shown
            "placeholder_start": 0,  # Cursor position where placeholder starts
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
        def grey_line():
            return Window(
                height=1,
                content=FormattedTextControl(
                    text=lambda: [("#808080", "─" * 200)]
                ),
            )

        # Render output area - show recent lines
        def render_output():
            # Show all lines - let the window with height=D(weight=1) handle display
            # As input grows, output window shrinks automatically, creating scroll effect
            result = []
            for line in state["output_lines"]:
                if isinstance(line, list):
                    result.extend(line)
                else:
                    result.append(("", str(line)))
                result.append(("", "\n"))
            return result

        # Render completion menu
        def render_completions():
            if not state["completions"]:
                return []

            text = input_buffer.text
            is_top_level = " " not in text.rstrip()

            lines = []
            for i, comp in enumerate(state["completions"]):
                cmd_text = str(comp.text)
                help_text = comp.display_meta if hasattr(comp, "display_meta") else ""
                if isinstance(help_text, list):
                    help_text = "".join(t for _, t in help_text)
                else:
                    help_text = str(help_text) if help_text else ""

                prefix = "/" if is_top_level else ""
                formatted = f"{prefix}{cmd_text:<19} {help_text}"

                style = "#6B4FBB bold" if i == state["selected_idx"] else "#808080"
                lines.append((style, formatted))
                if i < len(state["completions"]) - 1:
                    lines.append(("", "\n"))
            return lines

        # Update completions on text change
        def on_text_changed(_):
            text = input_buffer.text

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
                from prompt_toolkit.document import Document
                from prompt_toolkit.completion import CompleteEvent

                doc = Document(text, len(text))
                completions = list(completer.get_completions(doc, CompleteEvent()))
                state["completions"] = completions
                state["selected_idx"] = 0 if completions else -1
            else:
                state["completions"] = []
                state["selected_idx"] = -1

        # Create input buffer
        input_buffer = Buffer(
            multiline=True,
            complete_while_typing=True,
            completer=completer,
            history=FileHistory(str(history_file)),
            on_text_changed=on_text_changed,
        )

        # Windows
        output_window = Window(
            content=FormattedTextControl(text=render_output),
            height=D(weight=1),  # Take remaining space
            wrap_lines=True,
        )

        # Function to show prompt (> for first line, indent for continuation)
        def get_input_prompt(line_number, wrap_count):
            """Show > prompt on first line, indent on continuation lines."""
            if line_number == 0 and wrap_count == 0:
                return [("bold", "> ")]
            else:
                return [("", "  ")]  # Indent continuation lines

        # Dynamic height based on buffer content
        def get_input_height():
            """Calculate input height based on number of lines in buffer."""
            # Count newlines in buffer to determine line count
            line_count = max(1, input_buffer.text.count('\n') + 1) if input_buffer.text else 1
            return D(preferred=line_count, max=10)

        input_window = Window(
            content=BufferControl(
                buffer=input_buffer,
                lexer=None,
                input_processors=[],
                include_default_input_processors=False,
            ),
            height=get_input_height,  # Dynamic height: 1 line when empty, grows with content
            wrap_lines=True,
            get_line_prefix=get_input_prompt,  # Add > prompt
            right_margins=[ConditionalScrollbarMargin(input_buffer, max_lines=10, display_arrows=True)],
            scroll_offsets=ScrollOffsets(top=1, bottom=1),  # Keep cursor visible with some padding
        )

        menu_window = Window(
            content=FormattedTextControl(text=render_completions),
            height=D(preferred=5),
            wrap_lines=True,
        )

        # Layout
        layout = Layout(
            HSplit([
                output_window,
                grey_line(),
                input_window,
                grey_line(),
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
            event.app.invalidate()

        @kb.add("c-j")
        def insert_newline(event):
            event.current_buffer.insert_text("\n")

        @kb.add("down")
        def nav_down(event):
            if state["completions"] and state["selected_idx"] < len(state["completions"]) - 1:
                state["selected_idx"] += 1
                event.app.invalidate()

        @kb.add("up")
        def nav_up(event):
            if state["completions"] and state["selected_idx"] > 0:
                state["selected_idx"] -= 1
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
            text = buffer.text.strip()

            # Remove placeholder if still present
            if "<text>" in text:
                text = text.replace(" <text>", "").replace("<text>", "")

            # Auto-complete if partial match
            if state["completions"] and state["selected_idx"] >= 0 and text.startswith("/"):
                comp = state["completions"][state["selected_idx"]]
                parts = text.split(maxsplit=1)
                first_word = parts[0][1:] if parts else ""  # Remove /

                # Only auto-complete if it's a partial match
                if first_word != comp.text and comp.text.startswith(first_word):
                    text = "/" + comp.text
                    if len(parts) > 1:
                        text += " " + parts[1]

            if not text:
                return

            # Add command to output
            state["output_lines"].append([("bold", "> "), ("", text)])

            # Clear buffer
            buffer.text = ""
            state["placeholder_active"] = False

            # Parse and execute
            if text.startswith("/"):
                command = text[1:]
            elif enable_agent_mode:
                state["output_lines"].append([("cyan", "Echo: "), ("", text)])
                event.app.invalidate()
                return
            else:
                command = text

            args = command.split()
            if not args:
                event.app.invalidate()
                return

            cmd_name = args[0]
            cmd_args = args[1:]

            # Handle quit/exit
            if cmd_name in ["quit", "exit"]:
                state["output_lines"].append([("", "Goodbye!")])
                event.app.invalidate()
                event.app.exit()
                return

            # Execute command
            if hasattr(self.cli, "commands") and cmd_name in self.cli.commands:
                cmd = self.cli.commands[cmd_name]

                # Handle group commands
                if hasattr(cmd, "commands"):
                    if cmd_args and cmd_args[0] in cmd.commands:
                        subcmd = cmd.commands[cmd_args[0]]
                        subcmd_args = cmd_args[1:]
                        self._execute_click_command(subcmd, subcmd_args, state)
                    else:
                        # Just the group name, no subcommand
                        state["output_lines"].append([("", "")])
                else:
                    # Regular command
                    self._execute_click_command(cmd, cmd_args, state)
            else:
                state["output_lines"].append([("red", f"Unknown command: {cmd_name}")])

            event.app.invalidate()

        # Create application
        app = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=True,
            mouse_support=True,  # Enable mouse scrolling
        )

        app.run()

    def _execute_click_command(self, cmd, args, state):
        """Execute a Click command and capture output."""
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
            state["output_lines"].append([("red", f"Missing argument: {e.param.name}")])
        except Exception as e:
            state["output_lines"].append([("red", f"Error: {str(e)}")])

        # Add output
        stdout_text = stdout_buf.getvalue()
        stderr_text = stderr_buf.getvalue()

        if stdout_text:
            for line in stdout_text.rstrip().split("\n"):
                state["output_lines"].append([("", line)])
        if stderr_text:
            for line in stderr_text.rstrip().split("\n"):
                state["output_lines"].append([("red", line)])
