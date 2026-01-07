"""Unit tests for formatting module."""
from cli_repl_kit.core.formatting import ANSILexer, formatted_text_to_ansi_string
from cli_repl_kit.core.config import Config
from pathlib import Path
from prompt_toolkit.document import Document
import cli_repl_kit


class TestFormattedTextToANSIString:
    """Test formatted_text_to_ansi_string() function."""

    def setup_method(self):
        """Load config for tests."""
        default_config = Path(cli_repl_kit.__file__).parent / "config.yaml"
        self.config = Config.load(str(default_config), app_name="test")

    def test_empty_list_returns_empty_string(self):
        """Test empty FormattedText returns empty string."""
        result = formatted_text_to_ansi_string([], self.config)
        assert result == ""

    def test_plain_text_no_style(self):
        """Test plain text with empty style."""
        formatted_text = [("", "Hello")]
        result = formatted_text_to_ansi_string(formatted_text, self.config)
        assert result == "Hello"

    def test_single_color_red(self):
        """Test text with red color."""
        formatted_text = [("red", "Error")]
        result = formatted_text_to_ansi_string(formatted_text, self.config)
        # Should have ANSI codes wrapped around text
        assert "Error" in result
        assert result.startswith("\x1b[")  # ANSI escape code
        assert result.endswith("\x1b[0m")  # Reset code

    def test_bold_style(self):
        """Test text with bold style."""
        formatted_text = [("bold", "Important")]
        result = formatted_text_to_ansi_string(formatted_text, self.config)
        assert "Important" in result
        assert "\x1b[" in result

    def test_combined_style_cyan_bold(self):
        """Test combined style like 'cyan bold'."""
        formatted_text = [("cyan bold", "Header")]
        result = formatted_text_to_ansi_string(formatted_text, self.config)
        assert "Header" in result
        assert "\x1b[" in result

    def test_multiple_fragments(self):
        """Test multiple styled fragments."""
        formatted_text = [
            ("red", "Error: "),
            ("", "Something went wrong"),
            ("yellow", " (warning)"),
        ]
        result = formatted_text_to_ansi_string(formatted_text, self.config)
        assert "Error: " in result
        assert "Something went wrong" in result
        assert "(warning)" in result

    def test_unknown_style_returns_plain_text(self):
        """Test unknown style falls back to plain text."""
        formatted_text = [("unknown_style_xyz", "Text")]
        result = formatted_text_to_ansi_string(formatted_text, self.config)
        assert result == "Text"

    def test_none_style_treated_as_empty(self):
        """Test None style is treated as empty."""
        formatted_text = [(None, "Text")]
        result = formatted_text_to_ansi_string(formatted_text, self.config)
        assert result == "Text"

    def test_green_color(self):
        """Test green color formatting."""
        formatted_text = [("green", "Success")]
        result = formatted_text_to_ansi_string(formatted_text, self.config)
        assert "Success" in result
        assert "\x1b[" in result


class TestANSILexer:
    """Test ANSILexer class."""

    def test_lexer_initialization(self):
        """Test ANSILexer can be instantiated."""
        lexer = ANSILexer()
        assert lexer is not None

    def test_lex_plain_text(self):
        """Test lexing plain text without ANSI codes."""
        lexer = ANSILexer()
        doc = Document("Hello World")
        get_line = lexer.lex_document(doc)

        # Get line 0
        result = get_line(0)
        assert isinstance(result, list)
        assert len(result) > 0
        # Should have text content
        text_parts = [part[1] for part in result]
        assert "Hello World" in "".join(text_parts)

    def test_lex_with_ansi_codes(self):
        """Test lexing text with ANSI escape codes."""
        lexer = ANSILexer()
        # Red text with ANSI codes
        text_with_ansi = "\x1b[31mError\x1b[0m"
        doc = Document(text_with_ansi)
        get_line = lexer.lex_document(doc)

        result = get_line(0)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_lex_multiline_document(self):
        """Test lexing multiline document."""
        lexer = ANSILexer()
        doc = Document("Line 1\nLine 2\nLine 3")
        get_line = lexer.lex_document(doc)

        # Get each line
        line0 = get_line(0)
        line1 = get_line(1)
        line2 = get_line(2)

        assert len(line0) > 0
        assert len(line1) > 0
        assert len(line2) > 0

    def test_lex_empty_line(self):
        """Test lexing empty line."""
        lexer = ANSILexer()
        doc = Document("")
        get_line = lexer.lex_document(doc)

        result = get_line(0)
        assert isinstance(result, list)

    def test_lex_out_of_bounds_line(self):
        """Test lexing line number beyond document length."""
        lexer = ANSILexer()
        doc = Document("Single line")
        get_line = lexer.lex_document(doc)

        # Request line 10 when only 1 line exists
        result = get_line(10)
        assert result == []

    def test_lex_returns_formatted_text(self):
        """Test lex_document returns FormattedText structure."""
        lexer = ANSILexer()
        doc = Document("Test")
        get_line = lexer.lex_document(doc)

        result = get_line(0)
        # Should be list of tuples (style, text)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], tuple)

    def test_lex_colored_output(self):
        """Test lexing colored output preserves styling."""
        lexer = ANSILexer()
        # Cyan bold text
        text = "\x1b[36;1mHeader\x1b[0m"
        doc = Document(text)
        get_line = lexer.lex_document(doc)

        result = get_line(0)
        assert isinstance(result, list)
        # Should parse ANSI codes into styled fragments
        assert len(result) > 0
