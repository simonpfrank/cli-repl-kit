"""Configuration loader for CLI REPL Kit."""

import re
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigDict(dict):
    """Dictionary that allows attribute access to nested values."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize ConfigDict with nested dictionaries converted to ConfigDict.

        Args:
            data: Dictionary data to wrap
        """
        super().__init__()
        for key, value in data.items():
            if isinstance(value, dict):
                self[key] = ConfigDict(value)
            else:
                self[key] = value

    def __getattr__(self, name: str) -> Any:
        """Allow attribute access to dictionary keys.

        Args:
            name: Key name to access

        Returns:
            Value at key

        Raises:
            AttributeError: If key doesn't exist
        """
        if name in self:
            return self[name]
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        """Allow attribute assignment to dictionary keys.

        Args:
            name: Key name
            value: Value to set
        """
        self[name] = value


class Config:
    """Configuration management for CLI REPL Kit."""

    _defaults = {
        "windows": {
            "output": {
                "scrollable": True,
                "auto_scroll_when_at_bottom": True,
                "stay_put_when_scrolled_up": True,
                "page_up_down_enabled": True,
                "history_limit": None,
                "wrap_lines": True,
            },
            "status": {
                "height": 1,
                "visible": True,
                "wrap_lines": False,
                "truncate_overflow": True,
            },
            "input": {
                "initial_height": 1,
                "max_height": None,
                "wrap_lines": True,
                "enable_multiline": True,
                "enable_history": True,
                "history_navigation_from_start_only": True,
            },
            "info": {
                "height": 0,  # Default 0 (hidden), configurable
                "visible": True,
                "wrap_lines": False,
                "truncate_overflow": True,
            },
            "menu": {
                "height": 5,
                "wrap_lines": True,
                "truncate_overflow": True,
                "min_bottom_buffer": 1,
                "can_push_down": True,
                "can_push_up": True,
            },
        },
        "colors": {
            "highlight": "#6B4FBB",
            "grey": "#808080",
            "error": "red",
            "success": "green",
            "warning": "yellow",
            "info": "cyan",
            "prompt": "bold",
            "divider": "#808080",
            "command_text": "dim",
        },
        "symbols": {
            # Command output formatting
            "command_success": "●",
            "command_error": "●",
            "command_with_args": "■",
            "indent": "⎿",
            "arrow": "→",
            # Status indicators
            "success": "✓",
            "error": "✗",
            "warning": "⚠",
            "info": "ℹ",
            "bullet": "•",
        },
        "status_line": {
            # Claude Code-style spinner animation frames
            "spinner_frames": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "spinner_interval": 100,  # Milliseconds between frames
            # Status text styling
            "processing_color": "yellow",  # Orange/yellow for "processing" status
            "processing_style": "bold",     # Bold for emphasis
        },
        "ansi_colors": {
            # Standard text styles
            "bold": "\x1b[1m",
            "dim": "\x1b[2m",
            "italic": "\x1b[3m",
            "underline": "\x1b[4m",
            # Foreground colors
            "black": "\x1b[30m",
            "red": "\x1b[31m",
            "green": "\x1b[32m",
            "yellow": "\x1b[33m",
            "blue": "\x1b[34m",
            "magenta": "\x1b[35m",
            "cyan": "\x1b[36m",
            "white": "\x1b[37m",
            # Combined styles
            "cyan_bold": "\x1b[36;1m",
            "green_bold": "\x1b[32;1m",
            "red_bold": "\x1b[31;1m",
            "yellow_bold": "\x1b[33;1m",
            # Semantic colors
            "stdout": "",
            "stderr": "\x1b[31m",
            "reset": "\x1b[0m",
        },
        "prompt": {
            "character": "> ",
            "continuation": "  ",
        },
        "keybindings": {
            "exit": "c-c",
            "clear_input": "escape",
            "newline": "c-j",
            "submit": "enter",
            "nav_up": "up",
            "nav_down": "down",
            "complete": "tab",
            "space": "space",
        },
        "history": {
            "enabled": True,
            "file_location": "history",
        },
        "mouse": {
            "enabled": True,
        },
        "appearance": {
            "box_width": 140,
            "full_screen": True,
            "ascii_art_text": "CLI REPL Kit",  # Default banner text
        },
    }

    def __init__(self, data: Dict[str, Any]):
        """Initialize Config with data.

        Args:
            data: Configuration data dictionary
        """
        self._data = ConfigDict(data)

    @classmethod
    def load(cls, config_path: str, app_name: Optional[str] = None) -> "Config":
        """Load configuration from YAML file.

        Args:
            config_path: Path to config YAML file
            app_name: Optional app name for runtime substitution

        Returns:
            Config instance

        Raises:
            yaml.YAMLError: If YAML is invalid
            ValueError: If config values fail validation
        """
        # Start with defaults
        config_data = cls._deep_copy(cls._defaults)

        # Load file if it exists
        path = Path(config_path)
        if path.exists():
            with open(path, "r") as f:
                loaded_data = yaml.safe_load(f)
                if loaded_data:
                    # Merge loaded data with defaults
                    config_data = cls._deep_merge(config_data, loaded_data)

        # Perform runtime substitution
        if app_name:
            config_data = cls._substitute_variables(config_data, {"app_name": app_name})

        # Validate
        cls._validate(config_data)

        return cls(config_data)

    @classmethod
    def get_defaults(cls) -> "Config":
        """Get default configuration.

        Returns:
            Config instance with default values
        """
        return cls(cls._deep_copy(cls._defaults))

    def get(self, path: str, default: Any = None) -> Any:
        """Get nested value using dot notation.

        Args:
            path: Dot-separated path to value (e.g., "windows.menu.height")
            default: Default value if path doesn't exist

        Returns:
            Value at path or default
        """
        parts = path.split(".")
        current = self._data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def __getattr__(self, name: str) -> Any:
        """Allow attribute access to config data.

        Args:
            name: Attribute name

        Returns:
            Value from config data
        """
        return getattr(self._data, name)

    @staticmethod
    def _deep_copy(data: Dict[str, Any]) -> Dict[str, Any]:
        """Create deep copy of dictionary.

        Args:
            data: Dictionary to copy

        Returns:
            Deep copy of dictionary
        """
        import copy

        return copy.deepcopy(data)

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Dictionary with values to override

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def _substitute_variables(data: Any, variables: Dict[str, str]) -> Any:
        """Substitute variables in strings recursively.

        Args:
            data: Data to process (dict, list, str, or other)
            variables: Variable name -> value mapping

        Returns:
            Data with variables substituted
        """
        if isinstance(data, dict):
            return {
                key: Config._substitute_variables(value, variables)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [Config._substitute_variables(item, variables) for item in data]
        elif isinstance(data, str):
            result = data
            for var_name, var_value in variables.items():
                result = result.replace(f"{{{var_name}}}", var_value)
            return result
        else:
            return data

    @staticmethod
    def _validate(data: Dict[str, Any]) -> None:
        """Validate configuration data.

        Args:
            data: Configuration data to validate

        Raises:
            ValueError: If validation fails
        """
        # Validate window heights (0 is allowed for info window)
        if "windows" in data:
            for window_name, window_config in data["windows"].items():
                if isinstance(window_config, dict) and "height" in window_config:
                    height = window_config["height"]
                    if height is not None and height < 0:
                        raise ValueError(
                            f"{window_name} height must be non-negative, got {height}"
                        )

        # Validate colors
        if "colors" in data:
            for color_name, color_value in data["colors"].items():
                if isinstance(color_value, str):
                    # Accept hex colors (#RRGGBB), named colors, or empty
                    if color_value and not (
                        color_value.startswith("#")
                        or color_value.isalpha()
                        or " " in color_value  # Allow "bold", "green bold", etc.
                    ):
                        raise ValueError(
                            f"Invalid color format for {color_name}: {color_value}"
                        )
