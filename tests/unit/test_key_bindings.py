"""Unit tests for KeyBindingManager module."""
from unittest.mock import Mock, MagicMock
from cli_repl_kit.core.key_bindings import KeyBindingManager
from cli_repl_kit.core.state import REPLState
from cli_repl_kit.core.config import Config
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
import click
import pytest


class TestKeyBindingManager:
    """Test KeyBindingManager class."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create a test config."""
        config_file = tmp_path / "config.yaml"
        return Config.load(str(config_file))

    @pytest.fixture
    def manager(self, config):
        """Create a KeyBindingManager for testing."""
        state = REPLState()
        input_buffer = Buffer()
        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()

        def mock_execute(text):
            pass

        return KeyBindingManager(
            config=config,
            state=state,
            input_buffer=input_buffer,
            output_buffer=output_buffer,
            cli=cli,
            layout_builder=layout_builder,
            execute_callback=mock_execute
        )

    def test_initialization(self, config):
        """Test KeyBindingManager initializes correctly."""
        state = REPLState()
        input_buffer = Buffer()
        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config=config,
            state=state,
            input_buffer=input_buffer,
            output_buffer=output_buffer,
            cli=cli,
            layout_builder=layout_builder,
            execute_callback=execute_callback
        )

        assert manager.config == config
        assert manager.state == state
        assert manager.input_buffer == input_buffer
        assert manager.output_buffer == output_buffer
        assert manager.cli == cli
        assert manager.layout_builder == layout_builder
        assert manager.execute_callback == execute_callback

    def test_create_bindings_returns_keybindings(self, manager):
        """Test create_bindings() returns KeyBindings object."""
        bindings = manager.create_bindings()

        assert isinstance(bindings, KeyBindings)

    def test_handle_up_with_menu_active(self, config):
        """Test up arrow navigates menu when active."""
        state = REPLState()
        state.slash_command_active = True
        state.completions = ["cmd1", "cmd2", "cmd3"]
        state.selected_idx = 2

        input_buffer = Buffer()
        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        # Simulate up arrow
        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_up(event)

        # Should decrement selected_idx
        assert state.selected_idx == 1

    def test_handle_down_with_menu_active(self, config):
        """Test down arrow navigates menu when active."""
        state = REPLState()
        state.slash_command_active = True
        state.completions = ["cmd1", "cmd2", "cmd3"]
        state.selected_idx = 0

        input_buffer = Buffer()
        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_down(event)

        # Should increment selected_idx
        assert state.selected_idx == 1

    def test_handle_escape_clears_input(self, config):
        """Test escape clears input buffer."""
        state = REPLState()
        input_buffer = Buffer()
        input_buffer.text = "some text"
        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_escape(event)

        assert input_buffer.text == ""
        assert not state.placeholder_active
        assert not state.menu_keep_visible

    def test_handle_ctrl_j_inserts_newline(self, config):
        """Test ctrl-j inserts newline."""
        state = REPLState()
        input_buffer = Buffer()
        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_ctrl_j(event)

        assert "\n" in input_buffer.text

    def test_handle_tab_with_slash_command(self, config):
        """Test tab completion with slash command."""
        from prompt_toolkit.completion import Completion

        state = REPLState()
        state.slash_command_active = True
        # Use proper Completion objects
        state.completions = [
            Completion("hello", start_position=-1),
            Completion("help", start_position=-1)
        ]
        state.selected_idx = 0

        input_buffer = Buffer()
        input_buffer.text = "/h"
        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        layout_builder.get_argument_placeholder_text.return_value = None
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_tab(event)

        # Should autocomplete to selected command
        assert "hello" in input_buffer.text

    def test_handle_enter_submits_command(self, config):
        """Test enter key submits command."""
        state = REPLState()
        input_buffer = Buffer()
        input_buffer.text = "/hello World"
        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_enter(event)

        # Should call execute_callback
        execute_callback.assert_called_once()

    def test_handle_space_with_slash_command(self, config):
        """Test space bar with slash command."""
        state = REPLState()
        state.slash_command_active = True
        state.completions = ["hello"]
        state.selected_idx = 0

        input_buffer = Buffer()
        input_buffer.text = "/hello"
        output_buffer = Buffer()

        # Create a mock command with no params
        cmd = click.Command("hello", callback=lambda: None)
        cli = click.Group()
        cli.add_command(cmd)

        layout_builder = Mock()
        layout_builder.get_argument_placeholder_text.return_value = None
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_space(event)

        # Should insert space
        assert " " in input_buffer.text

    def test_handle_up_multiline_input(self, config):
        """Test up arrow with multi-line input moves cursor up."""
        state = REPLState()
        state.is_multiline = True
        state.slash_command_active = False

        input_buffer = Buffer()
        input_buffer.text = "line1\nline2\nline3"
        input_buffer.cursor_position = len("line1\nline2\n")  # Start of line3

        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_up(event)

        # cursor_up should have been called on the buffer
        event.app.invalidate.assert_called()

    def test_handle_up_history_navigation(self, config):
        """Test up arrow at start navigates history."""
        state = REPLState()
        state.slash_command_active = False
        state.is_multiline = False

        input_buffer = Buffer()
        input_buffer.cursor_position = 0  # At start

        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_up(event)

        # Should call invalidate
        event.app.invalidate.assert_called()

    def test_handle_up_move_to_start(self, config):
        """Test up arrow not at start moves cursor to start."""
        state = REPLState()
        state.slash_command_active = False
        state.is_multiline = False

        input_buffer = Buffer()
        input_buffer.text = "hello"
        input_buffer.cursor_position = 3  # Not at start

        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_up(event)

        # Should move to start
        assert input_buffer.cursor_position == 0

    def test_handle_down_multiline_input(self, config):
        """Test down arrow with multi-line input moves cursor down."""
        state = REPLState()
        state.is_multiline = True
        state.slash_command_active = False

        input_buffer = Buffer()
        input_buffer.text = "line1\nline2\nline3"

        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_down(event)

        # cursor_down should trigger invalidate
        event.app.invalidate.assert_called()

    def test_handle_down_history_forward(self, config):
        """Test down arrow at start navigates history forward."""
        state = REPLState()
        state.slash_command_active = False
        state.is_multiline = False

        input_buffer = Buffer()
        input_buffer.cursor_position = 0

        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_down(event)

        event.app.invalidate.assert_called()

    def test_handle_down_move_to_start(self, config):
        """Test down arrow not at start moves cursor to start."""
        state = REPLState()
        state.slash_command_active = False
        state.is_multiline = False

        input_buffer = Buffer()
        input_buffer.text = "hello"
        input_buffer.cursor_position = 3

        output_buffer = Buffer()
        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_down(event)

        assert input_buffer.cursor_position == 0

    def test_handle_pageup(self, config):
        """Test page up scrolls output buffer."""
        state = REPLState()
        input_buffer = Buffer()
        output_buffer = Buffer()
        output_buffer.text = "line1\nline2\nline3\nline4\nline5"

        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_pageup(event)

        event.app.invalidate.assert_called()

    def test_handle_pagedown(self, config):
        """Test page down scrolls output buffer."""
        state = REPLState()
        input_buffer = Buffer()
        output_buffer = Buffer()
        output_buffer.text = "line1\nline2\nline3\nline4\nline5"

        cli = click.Group()
        layout_builder = Mock()
        execute_callback = Mock()

        manager = KeyBindingManager(
            config, state, input_buffer, output_buffer, cli,
            layout_builder, execute_callback
        )

        event = Mock()
        event.current_buffer = input_buffer
        event.app = Mock()

        manager._handle_pagedown(event)

        event.app.invalidate.assert_called()
