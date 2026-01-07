"""Custom auto-completion for REPL (Claude Code style)."""

from typing import Any, Dict, Iterable, Optional

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document


class SlashCommandCompleter(Completer):
    """
    Custom completer for commands with / prefix (Claude Code style).

    Features:
    - Live dropdown as you type
    - Matches commands that start with typed text
    - Shows command descriptions
    - Supports subcommands (e.g., /config show)
    - Styled for better visibility
    """

    def __init__(self, commands: Dict[str, str], cli_group: Optional[Any] = None):
        """
        Initialize completer with command dictionary.

        Args:
            commands: Dict mapping command names to help text
                     e.g., {'help': 'Show available commands', ...}
            cli_group: Optional Click CLI group for subcommand support
        """
        self.commands = commands
        self.cli_group = cli_group

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """
        Get completions for the current input.

        Args:
            document: Current document/input
            complete_event: Completion event

        Yields:
            Completion objects for matching commands or subcommands
        """
        # Get current text before cursor
        text = document.text_before_cursor

        # Only show completions if we start with /
        if not text.startswith("/"):
            return

        # Get the part after /
        search_text = text[1:]

        # Check if we have a space - might be subcommand or option completion
        if " " in search_text:
            # Split into parts
            parts = search_text.split()

            # Guard: if parts is empty (e.g., "/ "), return early
            if not parts:
                return

            base_command = parts[0]

            # Determine if we're still typing something or have completed a word
            # If text ends with space, we've completed typing the last word
            # If text doesn't end with space, we're still typing
            typing_in_progress = not search_text.endswith(" ")

            # Get the part we're currently typing (after last space)
            current_part = parts[-1] if typing_in_progress else ""

            # Check if base command exists
            if self.cli_group and hasattr(self.cli_group, "commands"):
                base_cmd = self.cli_group.commands.get(base_command)

                # Case 1: Base command is a group with subcommands
                # We're in this case if:
                # - typing_in_progress and len(parts) == 2 (e.g., "/config s")
                # - OR not typing_in_progress and len(parts) == 1 (e.g., "/config ")
                if base_cmd and hasattr(base_cmd, "commands"):
                    if (typing_in_progress and len(parts) == 2) or (
                        not typing_in_progress and len(parts) == 1
                    ):
                        # Show subcommands
                        subcommand_lower = current_part.lower()

                        for subcmd_name, subcmd in sorted(base_cmd.commands.items()):
                            if subcmd_name.lower().startswith(subcommand_lower):
                                start_position = (
                                    -len(current_part) if current_part else 0
                                )

                                # Normalize help text - take first line only
                                help_text = (
                                    (subcmd.help or "No description")
                                    .split("\n")[0]
                                    .strip()
                                )

                                yield Completion(
                                    text=subcmd_name,
                                    start_position=start_position,
                                    display=f"{subcmd_name:<20}",
                                    display_meta=help_text,
                                )
                        return

                # Case 2: We have completed subcommand, show its options
                # We're in this case if:
                # - not typing_in_progress and len(parts) >= 2 (e.g., "/config load ")
                # - OR typing_in_progress and len(parts) >= 3 (e.g., "/config load --f")
                if base_cmd and hasattr(base_cmd, "commands"):
                    if (not typing_in_progress and len(parts) >= 2) or (
                        typing_in_progress and len(parts) >= 3
                    ):
                        subcommand_name = parts[1]
                        subcmd = base_cmd.commands.get(subcommand_name)

                        if subcmd and hasattr(subcmd, "params"):
                            # Show options for this subcommand
                            for param in subcmd.params:
                                if hasattr(param, "opts") and param.opts:
                                    # Prefer long form (--file) over short form (-f)
                                    long_opts = [
                                        opt
                                        for opt in param.opts
                                        if opt.startswith("--")
                                    ]
                                    short_opts = [
                                        opt
                                        for opt in param.opts
                                        if opt.startswith("-")
                                        and not opt.startswith("--")
                                    ]

                                    # Use long form if available, otherwise short form
                                    display_opt = (
                                        long_opts[0]
                                        if long_opts
                                        else (short_opts[0] if short_opts else None)
                                    )

                                    if display_opt and display_opt.startswith(
                                        current_part
                                    ):
                                        start_position = (
                                            -len(current_part) if current_part else 0
                                        )

                                        # Build help text showing type if available
                                        help_text = param.help or "Option"
                                        if hasattr(param, "type") and param.type:
                                            type_name = getattr(
                                                param.type, "name", str(param.type)
                                            )
                                            help_text = f"{help_text} ({type_name})"

                                        yield Completion(
                                            text=display_opt
                                            + " ",  # Add space after option
                                            start_position=start_position,
                                            display=f"{display_opt:<20}",
                                            display_meta=help_text,
                                        )
            return

        # No space - completing top-level commands
        # Convert to lowercase for case-insensitive matching
        search_lower = search_text.lower()

        # Find matching commands
        for cmd_name, cmd_help in sorted(self.commands.items()):
            if cmd_name.lower().startswith(search_lower):
                # Calculate how many characters to replace
                # If user typed "/c", we want to replace "c" with "config"
                start_position = -len(search_text) if search_text else 0

                yield Completion(
                    text=cmd_name,
                    start_position=start_position,
                    display=f"/{cmd_name:<20}",
                    display_meta=cmd_help or "",
                )
