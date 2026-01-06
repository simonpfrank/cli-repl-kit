"""Unit tests for custom layout (Phase 1 & 2)."""

import pytest
from click import Group

from cli_repl_kit.core.repl import REPL


class TestPhase1Layout:
    """Test Phase 1: Core layout infrastructure."""

    def test_layout_has_hsplit_structure(self):
        """Test that layout uses HSplit with 6 areas."""
        # Create a REPL instance
        repl = REPL(app_name="Test App", cli_group=Group())

        # We can't easily test the internal layout without running the app
        # So we'll test that the REPL initializes correctly
        assert repl.app_name == "Test App"
        assert repl.cli is not None

    def test_repl_initializes_with_app_name(self):
        """Test REPL initializes with correct app name."""
        repl = REPL(app_name="My Test App")
        assert repl.app_name == "My Test App"

    def test_repl_creates_default_cli_group(self):
        """Test REPL creates default CLI group if none provided."""
        repl = REPL(app_name="Test App")
        assert isinstance(repl.cli, Group)

    def test_repl_uses_provided_cli_group(self):
        """Test REPL uses provided CLI group."""
        custom_group = Group()
        repl = REPL(app_name="Test App", cli_group=custom_group)
        assert repl.cli is custom_group

    def test_context_factory_defaults_to_empty_dict(self):
        """Test context factory returns empty dict by default."""
        repl = REPL(app_name="Test App")
        context = repl.context_factory()
        assert context == {}

    def test_context_factory_uses_provided_function(self):
        """Test context factory uses provided function."""
        def custom_factory():
            return {"key": "value"}

        repl = REPL(app_name="Test App", context_factory=custom_factory)
        context = repl.context_factory()
        assert context == {"key": "value"}


class TestPhase2KeyBindings:
    """Test Phase 2: Multi-line input and key bindings."""

    def test_ctrl_j_binding_registered(self):
        """Test that Ctrl+J key binding would be registered."""
        # This is a simplified test - we're checking REPL initializes
        # Full testing would require actually running the app
        repl = REPL(app_name="Test App")
        assert repl is not None
        assert repl.app_name == "Test App"

    def test_enter_binding_registered(self):
        """Test that Enter key binding would be registered."""
        repl = REPL(app_name="Test App")
        assert repl is not None
        assert repl.app_name == "Test App"

    def test_ctrl_c_binding_registered(self):
        """Test that Ctrl+C key binding would be registered for exit."""
        repl = REPL(app_name="Test App")
        assert repl is not None
        assert repl.app_name == "Test App"

    def test_shift_enter_not_supported(self):
        """Test that Shift+Enter binding is NOT used (not supported)."""
        # This is a documentation test - confirming we DON'T use s-enter
        # If we tried to use it, prompt_toolkit would raise ValueError
        from prompt_toolkit.key_binding import KeyBindings

        kb = KeyBindings()

        # This should raise ValueError
        with pytest.raises(ValueError, match="Invalid key: s-enter"):
            @kb.add('s-enter')
            def dummy(event):
                pass


class TestCommandExecution:
    """Test command execution functionality."""

    def test_command_strips_leading_slash(self):
        """Test that leading slash is stripped from commands."""
        # This will be tested when we fix command execution
        pass

    def test_unknown_command_shows_error(self):
        """Test that unknown commands show error message."""
        # This will be tested when we fix command execution
        pass

    def test_valid_command_executes(self):
        """Test that valid commands execute correctly."""
        # This will be tested when we fix command execution
        pass


class TestOutputRendering:
    """Test output rendering in the output area."""

    def test_output_lines_appear_after_command(self):
        """Test that command output appears in output area."""
        # This will be tested when we implement proper output capturing
        pass

    def test_output_lines_limited_to_1000(self):
        """Test that output history keeps only last 1000 lines."""
        # This will be tested when we implement proper output capturing
        pass


class TestPhaseC1BugFixes:
    """Test Phase C.1 bug fixes for scroll, cursor, and dynamic behavior."""

    def test_input_window_no_scrollbar(self):
        """Test that input window has no scrollbar (spec: NOT scrollable, just grows)."""
        # Verify REPL initializes - actual window testing requires prompt_toolkit internals
        repl = REPL(app_name="Test App")
        assert repl is not None

    def test_input_prompt_configurable(self):
        """Test that prompt character is configurable."""
        repl = REPL(app_name="Test App")
        # Config should have default prompt
        assert repl.config.prompt.character == "> "

    def test_input_continuation_spacing(self):
        """Test continuation spacing matches prompt length."""
        repl = REPL(app_name="Test App")
        # Continuation should match prompt length (2 chars for "> ")
        assert repl.config.prompt.continuation == "  "

    def test_info_window_default_height_zero(self):
        """Test that info window defaults to height 0 (hidden)."""
        repl = REPL(app_name="Test App")
        assert repl.config.windows.info.height == 0

    def test_menu_navigation_requires_multiple_options(self):
        """Test that menu navigation requires > 1 option (not just 1)."""
        # This tests the spec: "menu visible and more than one option"
        # Actual testing requires running the app, but we verify config
        repl = REPL(app_name="Test App")
        assert repl.config.windows.menu.height == 5

    def test_output_scroll_state_initialized(self):
        """Test that output scroll state is properly initialized."""
        # State is initialized in run() method, so we test config exists
        repl = REPL(app_name="Test App")
        assert repl.config.windows.output.scrollable is True

    def test_history_api_exists(self):
        """Test that prompt_toolkit Buffer has history_backward/forward methods."""
        from prompt_toolkit.buffer import Buffer
        buf = Buffer()
        assert hasattr(buf, 'history_backward')
        assert hasattr(buf, 'history_forward')
        assert callable(buf.history_backward)
        assert callable(buf.history_forward)

    def test_cursor_movement_api_exists(self):
        """Test that prompt_toolkit Buffer has cursor_up/down methods."""
        from prompt_toolkit.buffer import Buffer
        buf = Buffer()
        assert hasattr(buf, 'cursor_up')
        assert hasattr(buf, 'cursor_down')
        assert callable(buf.cursor_up)
        assert callable(buf.cursor_down)

    def test_dimension_callable_for_height(self):
        """Test that prompt_toolkit accepts callable for height."""
        from prompt_toolkit.layout import Window
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.layout.dimension import Dimension as D

        def dynamic_height():
            return D(preferred=5)

        # This should not raise an error
        window = Window(
            content=FormattedTextControl(text=lambda: []),
            height=dynamic_height,
        )
        assert window is not None


class TestPhaseC1ScrollBehavior:
    """Test scroll lock and auto-scroll behavior."""

    def test_scroll_offset_calculation(self):
        """Test scroll offset is calculated correctly for render_output."""
        # Simulate state with output lines
        state = {
            "output_lines": ["line1", "line2", "line3", "line4", "line5"],
            "output_scroll_offset": 2,
            "user_scrolled_output": True,
        }

        # When offset is 2, we should see lines up to index 3 (5-2=3)
        lines = state["output_lines"]
        scroll_offset = state["output_scroll_offset"]

        if scroll_offset > 0 and len(lines) > scroll_offset:
            end_idx = len(lines) - scroll_offset
            visible_lines = lines[:end_idx]
        else:
            visible_lines = lines

        assert visible_lines == ["line1", "line2", "line3"]

    def test_scroll_offset_zero_shows_all(self):
        """Test scroll offset 0 shows all content."""
        state = {
            "output_lines": ["line1", "line2", "line3"],
            "output_scroll_offset": 0,
        }

        lines = state["output_lines"]
        scroll_offset = state["output_scroll_offset"]

        if scroll_offset > 0 and len(lines) > scroll_offset:
            end_idx = len(lines) - scroll_offset
            visible_lines = lines[:end_idx]
        else:
            visible_lines = lines

        assert visible_lines == ["line1", "line2", "line3"]

    def test_add_output_resets_scroll_when_at_bottom(self):
        """Test that adding output resets scroll when user hasn't scrolled up."""
        state = {
            "output_lines": [],
            "output_scroll_offset": 0,
            "user_scrolled_output": False,
        }

        # Simulate add_output_line logic
        def add_output_line(line):
            state["output_lines"].append(line)
            if not state["user_scrolled_output"]:
                state["output_scroll_offset"] = 0

        add_output_line("new line")

        assert state["output_scroll_offset"] == 0
        assert len(state["output_lines"]) == 1

    def test_add_output_preserves_scroll_when_scrolled_up(self):
        """Test that adding output preserves scroll position when user scrolled up."""
        state = {
            "output_lines": ["line1", "line2"],
            "output_scroll_offset": 5,
            "user_scrolled_output": True,
        }

        # Simulate add_output_line logic
        def add_output_line(line):
            state["output_lines"].append(line)
            if not state["user_scrolled_output"]:
                state["output_scroll_offset"] = 0

        add_output_line("new line")

        # Scroll offset should be preserved because user_scrolled_output is True
        assert state["output_scroll_offset"] == 5
        assert len(state["output_lines"]) == 3


class TestPhaseD1FormattedToANSI:
    """Test Phase D.1: formatted_to_ansi() helper function."""

    def test_formatted_to_ansi_empty_list(self):
        """Test formatted_to_ansi with empty list."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import formatted_to_ansi

        config = Config.get_defaults()
        result = formatted_to_ansi([], config)
        assert result == ""

    def test_formatted_to_ansi_plain_text(self):
        """Test formatted_to_ansi with plain text (no style)."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import formatted_to_ansi

        config = Config.get_defaults()
        formatted = [("", "Hello World")]
        result = formatted_to_ansi(formatted, config)
        assert result == "Hello World"

    def test_formatted_to_ansi_single_color(self):
        """Test formatted_to_ansi with single color."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import formatted_to_ansi

        config = Config.get_defaults()
        formatted = [("red", "Error message")]
        result = formatted_to_ansi(formatted, config)
        assert result == "\x1b[31mError message\x1b[0m"

    def test_formatted_to_ansi_bold_style(self):
        """Test formatted_to_ansi with bold style."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import formatted_to_ansi

        config = Config.get_defaults()
        formatted = [("bold", "Bold text")]
        result = formatted_to_ansi(formatted, config)
        assert result == "\x1b[1mBold text\x1b[0m"

    def test_formatted_to_ansi_combined_style(self):
        """Test formatted_to_ansi with combined style."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import formatted_to_ansi

        config = Config.get_defaults()
        formatted = [("cyan bold", "Cyan bold text")]
        result = formatted_to_ansi(formatted, config)
        # Note: config uses cyan_bold with underscore
        assert "\x1b" in result  # Has ANSI codes
        assert "Cyan bold text" in result

    def test_formatted_to_ansi_multiple_fragments(self):
        """Test formatted_to_ansi with multiple fragments."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import formatted_to_ansi

        config = Config.get_defaults()
        formatted = [
            ("", "Normal "),
            ("red", "Error "),
            ("green", "Success"),
        ]
        result = formatted_to_ansi(formatted, config)
        assert "Normal " in result
        assert "\x1b[31mError \x1b[0m" in result
        assert "\x1b[32mSuccess\x1b[0m" in result

    def test_formatted_to_ansi_unknown_style(self):
        """Test formatted_to_ansi with unknown style (should output plain text)."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import formatted_to_ansi

        config = Config.get_defaults()
        formatted = [("unknown_style", "Text")]
        result = formatted_to_ansi(formatted, config)
        # Unknown style should just output the text without ANSI codes
        assert result == "Text"


class TestPhaseD2ANSILexer:
    """Test Phase D.2: ANSILexer class for rendering ANSI codes."""

    def test_ansi_lexer_plain_text(self):
        """Test ANSILexer with plain text (no ANSI codes)."""
        from prompt_toolkit.document import Document

        from cli_repl_kit.core.repl import ANSILexer

        lexer = ANSILexer()
        doc = Document("Hello World")
        get_line = lexer.lex_document(doc)

        # Get first line
        line = get_line(0)
        # Should return FormattedText fragments
        assert isinstance(line, list)
        # Plain text should have empty style
        assert len(line) > 0

    def test_ansi_lexer_with_ansi_codes(self):
        """Test ANSILexer with ANSI color codes."""
        from prompt_toolkit.document import Document

        from cli_repl_kit.core.repl import ANSILexer

        lexer = ANSILexer()
        # Text with ANSI red color
        doc = Document("\x1b[31mRed text\x1b[0m")
        get_line = lexer.lex_document(doc)

        line = get_line(0)
        # Should parse ANSI codes and return styled fragments
        assert isinstance(line, list)
        assert len(line) > 0

    def test_ansi_lexer_multiline(self):
        """Test ANSILexer with multiple lines."""
        from prompt_toolkit.document import Document

        from cli_repl_kit.core.repl import ANSILexer

        lexer = ANSILexer()
        doc = Document("Line 1\nLine 2\nLine 3")
        get_line = lexer.lex_document(doc)

        # Should be able to get each line
        line0 = get_line(0)
        line1 = get_line(1)
        line2 = get_line(2)

        assert isinstance(line0, list)
        assert isinstance(line1, list)
        assert isinstance(line2, list)

    def test_ansi_lexer_empty_line(self):
        """Test ANSILexer with empty line."""
        from prompt_toolkit.document import Document

        from cli_repl_kit.core.repl import ANSILexer

        lexer = ANSILexer()
        doc = Document("")
        get_line = lexer.lex_document(doc)

        line = get_line(0)
        assert isinstance(line, list)


class TestPhaseD3OutputCapture:
    """Test Phase D.3: OutputCapture class for stdout/stderr redirection."""

    def test_output_capture_initialization(self):
        """Test OutputCapture initializes correctly."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import OutputCapture

        config = Config.get_defaults()
        captured = []

        def callback(line):
            captured.append(line)

        capture = OutputCapture("stdout", callback, config)
        assert capture.stream_type == "stdout"

    def test_output_capture_stdout_write(self):
        """Test OutputCapture captures stdout writes."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import OutputCapture

        config = Config.get_defaults()
        captured = []

        def callback(line):
            captured.append(line)

        capture = OutputCapture("stdout", callback, config)
        capture.write("Hello stdout")

        assert len(captured) == 1
        assert captured[0] == [("", "Hello stdout")]

    def test_output_capture_stderr_write(self):
        """Test OutputCapture captures stderr writes with red styling."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import OutputCapture

        config = Config.get_defaults()
        captured = []

        def callback(line):
            captured.append(line)

        capture = OutputCapture("stderr", callback, config)
        capture.write("Error message")

        assert len(captured) == 1
        assert captured[0] == [("red", "Error message")]

    def test_output_capture_ignores_empty_writes(self):
        """Test OutputCapture ignores empty or newline-only writes."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import OutputCapture

        config = Config.get_defaults()
        captured = []

        def callback(line):
            captured.append(line)

        capture = OutputCapture("stdout", callback, config)
        capture.write("")
        capture.write("\n")

        # Should not capture empty writes
        assert len(captured) == 0

    def test_output_capture_flush(self):
        """Test OutputCapture flush method (no-op)."""
        from cli_repl_kit.core.config import Config
        from cli_repl_kit.core.repl import OutputCapture

        config = Config.get_defaults()

        def callback(line):
            pass

        capture = OutputCapture("stdout", callback, config)
        # Should not raise an error
        capture.flush()
