"""Unit tests for Config class."""


import pytest
import yaml

from cli_repl_kit.core.config import Config


class TestConfigLoading:
    """Test config file loading and parsing."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid config file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "windows": {
                "output": {"scrollable": True, "wrap_lines": True},
                "status": {"height": 1, "visible": True},
                "input": {"initial_height": 1, "max_height": None},
                "info": {"height": 1, "visible": True},
                "menu": {"height": 5, "can_push_down": True},
            },
            "colors": {
                "highlight": "#6B4FBB",
                "grey": "#808080",
            },
        }
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(str(config_file))

        assert config.windows.output.scrollable is True
        assert config.windows.status.height == 1
        assert config.windows.input.max_height is None
        assert config.colors.highlight == "#6B4FBB"

    def test_load_missing_file_uses_defaults(self, tmp_path):
        """Test that missing config file uses default values."""
        config_file = tmp_path / "nonexistent.yaml"

        config = Config.load(str(config_file))

        # Should have default values
        assert config.windows.output.scrollable is True
        assert config.windows.status.height == 1
        assert config.windows.input.initial_height == 1
        assert config.colors.highlight == "#6B4FBB"

    def test_partial_config_uses_defaults(self, tmp_path):
        """Test that partial config merges with defaults."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "windows": {
                "menu": {"height": 10},  # Only override menu height
            }
        }
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(str(config_file))

        # Should have custom value
        assert config.windows.menu.height == 10
        # Should have default values for others
        assert config.windows.status.height == 1
        assert config.colors.highlight == "#6B4FBB"


class TestConfigValidation:
    """Test config value validation."""

    def test_invalid_window_height_raises_error(self, tmp_path):
        """Test that invalid window height raises validation error."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "windows": {
                "status": {"height": -1},  # Invalid: negative height
            }
        }
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ValueError, match="height must be non-negative"):
            Config.load(str(config_file))

    def test_invalid_color_raises_error(self, tmp_path):
        """Test that invalid color format raises validation error."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "colors": {
                "highlight": "invalid-color",  # Invalid format
            }
        }
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ValueError, match="Invalid color format"):
            Config.load(str(config_file))

    def test_invalid_yaml_raises_error(self, tmp_path):
        """Test that invalid YAML syntax raises error."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: syntax: [")

        with pytest.raises(yaml.YAMLError):
            Config.load(str(config_file))


class TestRuntimeSubstitution:
    """Test runtime variable substitution."""

    def test_app_name_substitution(self, tmp_path):
        """Test that {app_name} is substituted at runtime."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "history": {
                "file_location": "~/.{app_name}/history",
            }
        }
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(str(config_file), app_name="my_app")

        assert config.history.file_location == "~/.my_app/history"

    def test_no_substitution_when_no_placeholder(self, tmp_path):
        """Test that strings without placeholders are unchanged."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "history": {
                "file_location": "~/.fixed_path/history",
            }
        }
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(str(config_file), app_name="my_app")

        assert config.history.file_location == "~/.fixed_path/history"


class TestConfigAccessors:
    """Test config value accessors."""

    def test_nested_attribute_access(self, tmp_path):
        """Test accessing nested config values via attributes."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "windows": {
                "output": {
                    "scrollable": True,
                    "auto_scroll_when_at_bottom": True,
                    "history_limit": None,
                }
            }
        }
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(str(config_file))

        assert config.windows.output.scrollable is True
        assert config.windows.output.auto_scroll_when_at_bottom is True
        assert config.windows.output.history_limit is None

    def test_get_with_default(self, tmp_path):
        """Test getting value with default fallback."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "windows": {
                "menu": {"height": 5}
            }
        }
        config_file.write_text(yaml.dump(config_data))

        config = Config.load(str(config_file))

        # Should get value
        assert config.get("windows.menu.height", default=10) == 5
        # Should get default for missing value
        assert config.get("windows.menu.nonexistent", default=10) == 10


class TestDefaultConfig:
    """Test default config values match specification."""

    def test_default_window_dimensions(self):
        """Test default window dimensions."""
        config = Config.get_defaults()

        # Output
        assert config.windows.output.scrollable is True
        assert config.windows.output.auto_scroll_when_at_bottom is True
        assert config.windows.output.history_limit is None

        # Status
        assert config.windows.status.height == 1
        assert config.windows.status.visible is True

        # Input
        assert config.windows.input.initial_height == 1
        assert config.windows.input.max_height is None  # No limit
        assert config.windows.input.enable_multiline is True

        # Info (default height is 0 - hidden)
        assert config.windows.info.height == 0
        assert config.windows.info.visible is True

        # Menu
        assert config.windows.menu.height == 5
        assert config.windows.menu.can_push_down is True
        assert config.windows.menu.min_bottom_buffer == 1

    def test_default_colors(self):
        """Test default color values."""
        config = Config.get_defaults()

        assert config.colors.highlight == "#6B4FBB"
        assert config.colors.grey == "#808080"
        assert config.colors.error == "red"
        assert config.colors.success == "green"

    def test_default_ansi_colors(self):
        """Test default ANSI color codes."""
        config = Config.get_defaults()

        # Standard styles
        assert config.ansi_colors.bold == "\x1b[1m"
        assert config.ansi_colors.dim == "\x1b[2m"
        assert config.ansi_colors.italic == "\x1b[3m"
        assert config.ansi_colors.underline == "\x1b[4m"

        # Foreground colors
        assert config.ansi_colors.red == "\x1b[31m"
        assert config.ansi_colors.green == "\x1b[32m"
        assert config.ansi_colors.yellow == "\x1b[33m"
        assert config.ansi_colors.cyan == "\x1b[36m"

        # Combined styles
        assert config.ansi_colors.cyan_bold == "\x1b[36;1m"
        assert config.ansi_colors.green_bold == "\x1b[32;1m"
        assert config.ansi_colors.red_bold == "\x1b[31;1m"

        # Semantic colors
        assert config.ansi_colors.stdout == ""
        assert config.ansi_colors.stderr == "\x1b[31m"
        assert config.ansi_colors.reset == "\x1b[0m"

    def test_default_keybindings(self):
        """Test default keybinding values."""
        config = Config.get_defaults()

        assert config.keybindings.exit == "c-c"
        assert config.keybindings.clear_input == "escape"
        assert config.keybindings.newline == "c-j"
        assert config.keybindings.submit == "enter"

    def test_default_prompt_settings(self):
        """Test default prompt settings."""
        config = Config.get_defaults()

        assert config.prompt.character == "> "
        assert config.prompt.continuation == "  "

    def test_default_symbols(self):
        """Test default symbol values for command output formatting."""
        config = Config.get_defaults()

        # Command output formatting symbols
        assert config.symbols.command_success == "●"
        assert config.symbols.command_error == "●"
        assert config.symbols.command_with_args == "■"
        assert config.symbols.indent == "⎿"
        assert config.symbols.arrow == "→"

        # Status indicator symbols
        assert config.symbols.success == "✓"
        assert config.symbols.error == "✗"
        assert config.symbols.warning == "⚠"
        assert config.symbols.info == "ℹ"
        assert config.symbols.bullet == "•"

    def test_default_status_line(self):
        """Test default status line spinner and styling configuration."""
        config = Config.get_defaults()

        # Spinner frames
        assert len(config.status_line.spinner_frames) == 10
        assert config.status_line.spinner_frames[0] == "⠋"
        assert config.status_line.spinner_frames[-1] == "⠏"

        # Spinner timing
        assert config.status_line.spinner_interval == 100

        # Status styling
        assert config.status_line.processing_color == "yellow"
        assert config.status_line.processing_style == "bold"

    def test_default_ascii_art(self):
        """Test default ASCII art banner text configuration."""
        config = Config.get_defaults()

        assert config.appearance.ascii_art_text == "CLI REPL Kit"
        assert config.appearance.box_width == 140
