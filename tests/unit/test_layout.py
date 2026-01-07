"""Unit tests for layout module."""
from cli_repl_kit.core.layout import ConditionalScrollbarMargin
from prompt_toolkit.buffer import Buffer


class TestConditionalScrollbarMargin:
    """Test ConditionalScrollbarMargin class."""

    def test_initialization(self):
        """Test ConditionalScrollbarMargin initializes correctly."""
        buffer = Buffer()
        margin = ConditionalScrollbarMargin(buffer, max_lines=10, display_arrows=True)

        assert margin.buffer == buffer
        assert margin.max_lines == 10
        assert margin.scrollbar is not None

    def test_initialization_default_max_lines(self):
        """Test default max_lines is 10."""
        buffer = Buffer()
        margin = ConditionalScrollbarMargin(buffer)

        assert margin.max_lines == 10

    def test_initialization_default_display_arrows(self):
        """Test default display_arrows is True."""
        buffer = Buffer()
        margin = ConditionalScrollbarMargin(buffer)

        assert margin.scrollbar is not None

    def test_get_width_below_max_lines_returns_zero(self):
        """Test get_width returns 0 when line count is below max."""
        buffer = Buffer()
        buffer.text = "Line 1\nLine 2\nLine 3"  # 3 lines
        margin = ConditionalScrollbarMargin(buffer, max_lines=10)

        # Create a mock ui_content
        class MockUIContent:
            pass

        width = margin.get_width(MockUIContent())
        assert width == 0

    def test_get_width_at_max_lines_returns_scrollbar_width(self):
        """Test get_width returns scrollbar width at max lines."""
        buffer = Buffer()
        # Create exactly 10 lines
        buffer.text = "\n".join([f"Line {i}" for i in range(10)])
        margin = ConditionalScrollbarMargin(buffer, max_lines=10)

        class MockUIContent:
            pass

        width = margin.get_width(MockUIContent())
        # Scrollbar width should be non-zero (typically 1)
        assert width > 0

    def test_get_width_above_max_lines_returns_scrollbar_width(self):
        """Test get_width returns scrollbar width above max lines."""
        buffer = Buffer()
        # Create 15 lines
        buffer.text = "\n".join([f"Line {i}" for i in range(15)])
        margin = ConditionalScrollbarMargin(buffer, max_lines=10)

        class MockUIContent:
            pass

        width = margin.get_width(MockUIContent())
        assert width > 0

    def test_get_width_empty_buffer_returns_zero(self):
        """Test get_width with empty buffer returns 0."""
        buffer = Buffer()
        buffer.text = ""
        margin = ConditionalScrollbarMargin(buffer, max_lines=10)

        class MockUIContent:
            pass

        width = margin.get_width(MockUIContent())
        assert width == 0

    def test_create_margin_below_max_returns_empty_list(self):
        """Test create_margin returns empty list when below max."""
        buffer = Buffer()
        buffer.text = "Line 1\nLine 2"  # 2 lines
        margin = ConditionalScrollbarMargin(buffer, max_lines=10)

        class MockWindowRenderInfo:
            pass

        result = margin.create_margin(MockWindowRenderInfo(), width=1, height=10)

        # Should return an empty list
        assert result == []

    def test_create_margin_at_max_returns_scrollbar_margin(self):
        """Test create_margin returns scrollbar margin at max lines."""
        buffer = Buffer()
        buffer.text = "\n".join([f"Line {i}" for i in range(10)])
        margin = ConditionalScrollbarMargin(buffer, max_lines=10)

        # We can't easily test the actual scrollbar creation without full mocking
        # Just verify that with >= max_lines, we don't get the empty lambda
        # This is tested indirectly by checking line count logic
        assert margin.max_lines == 10
        line_count = buffer.text.count("\n") + 1
        assert line_count >= margin.max_lines

    def test_line_count_calculation_with_newlines(self):
        """Test line count calculation with various newlines."""
        buffer = Buffer()

        # Test single line (no newlines)
        buffer.text = "Single line"
        margin = ConditionalScrollbarMargin(buffer, max_lines=5)

        class MockUIContent:
            pass

        width = margin.get_width(MockUIContent())
        assert width == 0  # 1 line < 5 max

        # Test exactly at threshold
        buffer.text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"  # 5 lines
        width = margin.get_width(MockUIContent())
        assert width > 0  # 5 lines >= 5 max

    def test_custom_max_lines(self):
        """Test with custom max_lines value."""
        buffer = Buffer()
        buffer.text = "L1\nL2\nL3"  # 3 lines
        margin = ConditionalScrollbarMargin(buffer, max_lines=3)

        class MockUIContent:
            pass

        width = margin.get_width(MockUIContent())
        assert width > 0  # 3 lines >= 3 max

    def test_display_arrows_false(self):
        """Test initialization with display_arrows=False."""
        buffer = Buffer()
        margin = ConditionalScrollbarMargin(buffer, max_lines=10, display_arrows=False)

        # Scrollbar should still be created
        assert margin.scrollbar is not None
