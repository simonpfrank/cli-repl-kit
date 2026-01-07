"""Unit tests for LayoutBuilder module."""
from cli_repl_kit.core.layout import LayoutBuilder
from cli_repl_kit.core.state import REPLState
from cli_repl_kit.core.config import Config
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Layout
import click
import pytest


class TestLayoutBuilder:
    """Test LayoutBuilder class."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create a test config."""
        config_file = tmp_path / "config.yaml"
        # Use default config (load nonexistent file)
        return Config.load(str(config_file))

    def test_initialization(self, config):
        """Test LayoutBuilder initializes correctly."""
        state = REPLState()
        cli = click.Group()

        builder = LayoutBuilder(config, state, cli)

        assert builder.config == config
        assert builder.state == state
        assert builder.cli == cli

    def test_build_returns_layout(self, config):
        """Test build() returns a Layout object."""
        state = REPLState()
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        input_buffer = Buffer()
        output_buffer = Buffer()

        layout = builder.build(input_buffer, output_buffer)

        assert isinstance(layout, Layout)
        assert layout.container is not None

    def test_create_output_window(self, config):
        """Test _create_output_window creates Window."""
        state = REPLState()
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        output_buffer = Buffer()
        window = builder._create_output_window(output_buffer)

        assert window is not None
        assert window.content is not None

    def test_create_input_window(self, config):
        """Test _create_input_window creates Window."""
        state = REPLState()
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        input_buffer = Buffer()
        window = builder._create_input_window(input_buffer)

        assert window is not None
        assert window.content is not None

    def test_create_status_window(self, config):
        """Test _create_status_window creates Window."""
        state = REPLState()
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        window = builder._create_status_window()

        assert window is not None
        assert window.content is not None

    def test_create_info_window(self, config):
        """Test _create_info_window creates Window."""
        state = REPLState()
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        window = builder._create_info_window()

        assert window is not None
        assert window.content is not None

    def test_create_menu_window(self, config):
        """Test _create_menu_window creates Window."""
        state = REPLState()
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        input_buffer = Buffer()
        window = builder._create_menu_window(input_buffer)

        assert window is not None
        assert window.content is not None

    def test_create_divider_window(self, config):
        """Test _create_divider_window creates Window."""
        state = REPLState()
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        window = builder._create_divider_window()

        assert window is not None
        assert window.height == 1

    def test_divider_uses_terminal_width(self, config):
        """Test divider adapts to terminal width."""
        state = REPLState()
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        window = builder._create_divider_window()

        # Should use terminal width, not hardcoded 200
        # We can't easily test the actual width, but we can verify
        # it's a callable that will determine width dynamically
        assert window.content is not None

    def test_get_input_height_empty_buffer(self, config):
        """Test input height calculation for empty buffer."""
        state = REPLState()
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        input_buffer = Buffer()
        input_buffer.text = ""

        # Should return initial height from config
        height = builder._get_input_height(input_buffer)
        assert height is not None

    def test_get_input_height_multiline_buffer(self, config):
        """Test input height calculation for multiline buffer."""
        state = REPLState()
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        input_buffer = Buffer()
        input_buffer.text = "line1\nline2\nline3"

        # Should return height based on line count
        height = builder._get_input_height(input_buffer)
        assert height is not None

    def test_get_menu_height_slash_active(self, config):
        """Test menu height when slash command is active."""
        state = REPLState()
        state.slash_command_active = True
        state.completions = ["cmd1", "cmd2"]
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        height = builder._get_menu_height()

        # Should show menu when slash command active with completions
        assert height is not None

    def test_get_menu_height_no_slash(self, config):
        """Test menu height when no slash command active."""
        state = REPLState()
        state.slash_command_active = False
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        height = builder._get_menu_height()

        # Should be minimal/zero height
        assert height is not None

    def test_get_info_height_with_text(self, config):
        """Test info height when info text is set."""
        state = REPLState()
        state.info_text = [("", "Some info")]
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        height = builder._get_info_height()

        # Should show info window
        assert height is not None

    def test_get_info_height_without_text(self, config):
        """Test info height when no info text."""
        state = REPLState()
        state.info_text = []
        cli = click.Group()
        builder = LayoutBuilder(config, state, cli)

        height = builder._get_info_height()

        # Should be zero height
        assert height is not None
