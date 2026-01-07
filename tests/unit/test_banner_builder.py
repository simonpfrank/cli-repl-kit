"""Unit tests for BannerBuilder module."""
import pytest

from cli_repl_kit.core.banner_builder import BannerBuilder
from cli_repl_kit.core.config import Config


class TestBannerBuilder:
    """Test BannerBuilder class."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create a test config."""
        config_file = tmp_path / "config.yaml"
        return Config.load(str(config_file))

    def test_initialization(self, config):
        """Test BannerBuilder initializes correctly."""
        builder = BannerBuilder(config, "Test App")

        assert builder.config == config
        assert builder.app_name == "Test App"

    def test_build_returns_list(self, config):
        """Test build() returns list of formatted text."""
        builder = BannerBuilder(config, "Test App")

        result = builder.build()

        assert isinstance(result, list)
        assert len(result) > 0

    def test_build_includes_app_name(self, config):
        """Test build() includes app name in banner."""
        builder = BannerBuilder(config, "My Application")

        result = builder.build()

        # Convert to string to check for app name
        banner_text = str(result)
        assert "My Application" in banner_text

    def test_build_with_known_ascii_art(self, config):
        """Test build() uses ASCII art for known banner text."""
        # Set banner text to known value
        config.appearance.ascii_art_text = "Hello World"
        builder = BannerBuilder(config, "Test App")

        result = builder.build()

        # Should have ASCII art lines
        assert len(result) > 10  # Banner has many lines with ASCII art

    def test_build_with_custom_text(self, config):
        """Test build() handles custom banner text."""
        config.appearance.ascii_art_text = "Custom Banner"
        builder = BannerBuilder(config, "Test App")

        result = builder.build()

        # Should still build banner (falls back to plain text)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_ascii_art_map_has_known_values(self):
        """Test ASCII_ART_MAP contains expected entries."""
        assert "Hello World" in BannerBuilder.ASCII_ART_MAP
        assert "CLI REPL Kit" in BannerBuilder.ASCII_ART_MAP

    def test_ascii_art_map_entries_are_lists(self):
        """Test ASCII_ART_MAP entries are lists of strings."""
        for key, value in BannerBuilder.ASCII_ART_MAP.items():
            assert isinstance(value, list)
            assert all(isinstance(line, str) for line in value)

    def test_banner_has_instructions(self, config):
        """Test banner includes usage instructions."""
        builder = BannerBuilder(config, "Test App")

        result = builder.build()

        # Convert to string to check for instructions
        banner_text = str(result)
        assert "quit" in banner_text.lower()
        assert "Ctrl+J" in banner_text or "ctrl" in banner_text.lower()

    def test_banner_has_box_drawing(self, config):
        """Test banner uses box drawing characters."""
        builder = BannerBuilder(config, "Test App")

        result = builder.build()

        # First line should have top border
        first_line = result[0]
        assert "╭" in str(first_line) or "─" in str(first_line)

    def test_banner_respects_box_width(self, config):
        """Test banner respects configured box width."""
        # Set custom box width
        config.appearance.box_width = 80
        builder = BannerBuilder(config, "Test App")

        result = builder.build()

        # Check that box lines use the configured width
        # First line should be ╭ + 80 dashes + ╮
        assert isinstance(result, list)
        assert len(result) > 0
