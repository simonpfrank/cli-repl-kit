"""Banner builder for REPL intro display.

This module provides the BannerBuilder class that generates
the intro banner with ASCII art and instructions.
"""
from typing import List

from prompt_toolkit.formatted_text import StyleAndTextTuples

from cli_repl_kit.core.config import Config


class BannerBuilder:
    """Builds intro banner for REPL.

    Creates a formatted intro banner with ASCII art, app name,
    version, and usage instructions.

    Attributes:
        config: REPL configuration
        app_name: Application name for display
    """

    # ASCII art mappings for common text values
    ASCII_ART_MAP = {
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

    def __init__(self, config: Config, app_name: str):
        """Initialize banner builder.

        Args:
            config: REPL configuration
            app_name: Application name for display
        """
        self.config = config
        self.app_name = app_name

    def build(self) -> List[StyleAndTextTuples]:
        """Build intro banner with ASCII art and instructions.

        Returns:
            List of formatted text lines for the banner
        """
        box_width = self.config.appearance.box_width
        banner_text = self.config.appearance.ascii_art_text

        # Get ASCII art or use plain text
        if banner_text in self.ASCII_ART_MAP:
            ascii_art = self.ASCII_ART_MAP[banner_text]
        else:
            ascii_art = [banner_text]

        # Create intro banner
        intro_lines = [
            [("cyan", "╭" + "─" * box_width + "╮")],
            [("cyan", "│" + " " * box_width + "│")],
        ]

        # Add ASCII art lines
        for art_line in ascii_art:
            padding = box_width - len(art_line) - 2
            intro_lines.append(
                [
                    ("cyan", "│  "),
                    ("cyan bold", art_line),
                    ("", " " * padding),
                    ("cyan", "│"),
                ]
            )

        # Add app info and instructions
        intro_lines.extend(
            [
                [("cyan", "│" + " " * box_width + "│")],
                [
                    ("cyan", "│"),
                    ("bold", f"    {self.app_name}"),
                    ("yellow", " v0.1.0"),
                    ("", " " * (box_width - len(self.app_name) - 11)),
                    ("cyan", "│"),
                ],
                [
                    ("cyan", "│"),
                    ("", "    Type "),
                    ("green", "/quit"),
                    ("", " to exit or "),
                    ("green", "/hello <text>"),
                    ("", " to greet"),
                    ("", " " * (box_width - 48)),
                    ("cyan", "│"),
                ],
                [
                    ("cyan", "│"),
                    ("", "    Press "),
                    ("yellow", "Ctrl+J"),
                    ("", " for multi-line input, "),
                    ("yellow", "Enter"),
                    ("", " to submit"),
                    ("", " " * (box_width - 54)),
                    ("cyan", "│"),
                ],
                [("cyan", "│" + " " * box_width + "│")],
                [("cyan", "╰" + "─" * box_width + "╯")],
                [("", "")],
                [
                    ("green bold", "Ready!"),
                    ("", " (/ for commands). Use "),
                    ("yellow", "↑↓"),
                    ("", " arrows to navigate menu, "),
                    ("yellow", "Tab"),
                    ("", " or "),
                    ("yellow", "Enter"),
                    ("", " to select"),
                ],
                [("", "")],
            ]
        )

        return intro_lines
