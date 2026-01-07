"""Unit tests for output capture module."""
from cli_repl_kit.core.output_capture import OutputCapture
from cli_repl_kit.core.config import Config
from pathlib import Path
import cli_repl_kit


class TestOutputCapture:
    """Test OutputCapture class."""

    def setup_method(self):
        """Load config for tests."""
        default_config = Path(cli_repl_kit.__file__).parent / "config.yaml"
        self.config = Config.load(str(default_config), app_name="test")
        self.captured_output = []

        def capture_callback(formatted_text):
            """Store captured output for testing."""
            self.captured_output.append(formatted_text)

        self.callback = capture_callback

    def test_initialization_stdout(self):
        """Test OutputCapture initialization for stdout."""
        capture = OutputCapture("stdout", self.callback, self.config)
        assert capture.stream_type == "stdout"
        assert capture.output_callback == self.callback
        assert capture.config == self.config

    def test_initialization_stderr(self):
        """Test OutputCapture initialization for stderr."""
        capture = OutputCapture("stderr", self.callback, self.config)
        assert capture.stream_type == "stderr"
        assert capture.output_callback == self.callback
        assert capture.config == self.config

    def test_write_stdout_plain_text(self):
        """Test writing to stdout capture."""
        capture = OutputCapture("stdout", self.callback, self.config)
        capture.write("Hello World")

        # Should have captured output with no style
        assert len(self.captured_output) == 1
        assert self.captured_output[0] == [("", "Hello World")]

    def test_write_stderr_styled_text(self):
        """Test writing to stderr capture with error style."""
        capture = OutputCapture("stderr", self.callback, self.config)
        capture.write("Error message")

        # Should have captured output with error color
        assert len(self.captured_output) == 1
        assert len(self.captured_output[0]) == 1
        style, text = self.captured_output[0][0]
        assert text == "Error message"
        assert style == self.config.colors.error

    def test_write_ignores_empty_string(self):
        """Test that empty strings are ignored."""
        capture = OutputCapture("stdout", self.callback, self.config)
        capture.write("")

        # Should not have captured anything
        assert len(self.captured_output) == 0

    def test_write_ignores_single_newline(self):
        """Test that single newlines are ignored."""
        capture = OutputCapture("stdout", self.callback, self.config)
        capture.write("\n")

        # Should not have captured anything
        assert len(self.captured_output) == 0

    def test_write_multiple_times_stdout(self):
        """Test writing multiple times to stdout."""
        capture = OutputCapture("stdout", self.callback, self.config)
        capture.write("Line 1")
        capture.write("Line 2")
        capture.write("Line 3")

        # Should have captured all three
        assert len(self.captured_output) == 3
        assert self.captured_output[0] == [("", "Line 1")]
        assert self.captured_output[1] == [("", "Line 2")]
        assert self.captured_output[2] == [("", "Line 3")]

    def test_write_multiple_times_stderr(self):
        """Test writing multiple times to stderr."""
        capture = OutputCapture("stderr", self.callback, self.config)
        capture.write("Error 1")
        capture.write("Error 2")

        # Should have captured both with error style
        assert len(self.captured_output) == 2
        assert self.captured_output[0][0][1] == "Error 1"
        assert self.captured_output[1][0][1] == "Error 2"

    def test_flush_is_noop(self):
        """Test that flush is a no-op."""
        capture = OutputCapture("stdout", self.callback, self.config)
        # Should not raise any errors
        capture.flush()
        capture.flush()
        assert True  # If we got here, flush worked

    def test_inherits_from_string_io(self):
        """Test that OutputCapture inherits from io.StringIO."""
        import io

        capture = OutputCapture("stdout", self.callback, self.config)
        assert isinstance(capture, io.StringIO)

    def test_write_with_text_containing_newline(self):
        """Test writing text that contains newlines."""
        capture = OutputCapture("stdout", self.callback, self.config)
        capture.write("Hello\nWorld")

        # Should capture the text with newline
        assert len(self.captured_output) == 1
        assert self.captured_output[0] == [("", "Hello\nWorld")]

    def test_multiple_captures_independent(self):
        """Test that multiple OutputCapture instances are independent."""
        captured_1 = []
        captured_2 = []

        def callback_1(text):
            captured_1.append(text)

        def callback_2(text):
            captured_2.append(text)

        capture1 = OutputCapture("stdout", callback_1, self.config)
        capture2 = OutputCapture("stderr", callback_2, self.config)

        capture1.write("stdout text")
        capture2.write("stderr text")

        # Each should have captured independently
        assert len(captured_1) == 1
        assert len(captured_2) == 1
        assert captured_1[0] == [("", "stdout text")]
        assert captured_2[0][0][1] == "stderr text"

    def test_callback_receives_formatted_text_list(self):
        """Test that callback receives FormattedText structure."""
        capture = OutputCapture("stdout", self.callback, self.config)
        capture.write("Test")

        # Callback should receive list of (style, text) tuples
        assert isinstance(self.captured_output[0], list)
        assert isinstance(self.captured_output[0][0], tuple)
        assert len(self.captured_output[0][0]) == 2

    def test_stderr_uses_config_error_color(self):
        """Test that stderr uses error color from config."""
        capture = OutputCapture("stderr", self.callback, self.config)
        capture.write("Error")

        style, text = self.captured_output[0][0]
        # Should use the error color from config
        assert style == self.config.colors.error
        assert hasattr(self.config.colors, "error")
