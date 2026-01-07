"""Unit tests for menu height behavior in layout."""
import pytest
from prompt_toolkit.layout import Dimension as D

from cli_repl_kit.core.layout import LayoutBuilder
from cli_repl_kit.core.state import REPLState
from cli_repl_kit.core.config import Config


class TestMenuHeight:
    """Test menu window always occupies configured height."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create test config with known menu height."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
windows:
  menu:
    height: 5
""")
        return Config.load(str(config_file))

    @pytest.fixture
    def state(self):
        """Create fresh REPL state."""
        return REPLState()

    @pytest.fixture
    def cli(self):
        """Create mock CLI group."""
        import click
        return click.Group()

    @pytest.fixture
    def layout_builder(self, config, state, cli):
        """Create layout builder for testing."""
        return LayoutBuilder(config, state, cli)

    def test_menu_height_with_no_completions(self, layout_builder):
        """GIVEN menu has no completions
        WHEN menu height is calculated
        THEN height should still be the configured value (not 0)
        """
        # No completions, menu not active
        layout_builder.state.slash_command_active = False
        layout_builder.state.completions = []
        layout_builder.state.menu_keep_visible = False

        height = layout_builder._get_menu_height()

        # Should use configured height, not collapse to 0
        assert isinstance(height, D)
        assert height.preferred == layout_builder.config.windows.menu.height
        assert height.preferred == 5

    def test_menu_height_with_completions(self, layout_builder):
        """GIVEN menu has completions
        WHEN menu height is calculated
        THEN height should be the configured value
        """
        layout_builder.state.slash_command_active = True
        layout_builder.state.completions = ["cmd1", "cmd2", "cmd3"]

        height = layout_builder._get_menu_height()

        assert isinstance(height, D)
        assert height.preferred == layout_builder.config.windows.menu.height
        assert height.preferred == 5

    def test_menu_height_kept_visible(self, layout_builder):
        """GIVEN menu_keep_visible is True
        WHEN menu height is calculated
        THEN height should be the configured value
        """
        layout_builder.state.menu_keep_visible = True
        layout_builder.state.completions = []

        height = layout_builder._get_menu_height()

        assert isinstance(height, D)
        assert height.preferred == layout_builder.config.windows.menu.height
        assert height.preferred == 5

    def test_menu_height_consistency(self, layout_builder):
        """GIVEN different menu states
        WHEN menu height is calculated
        THEN height should always be the same configured value
        """
        config_height = layout_builder.config.windows.menu.height

        # Test various states
        states = [
            {"slash_command_active": False, "completions": [], "menu_keep_visible": False},
            {"slash_command_active": True, "completions": ["a"], "menu_keep_visible": False},
            {"slash_command_active": False, "completions": [], "menu_keep_visible": True},
            {"slash_command_active": True, "completions": ["a", "b"], "menu_keep_visible": True},
        ]

        for state_values in states:
            layout_builder.state.slash_command_active = state_values["slash_command_active"]
            layout_builder.state.completions = state_values["completions"]
            layout_builder.state.menu_keep_visible = state_values["menu_keep_visible"]

            height = layout_builder._get_menu_height()
            assert height.preferred == config_height, (
                f"Height should be {config_height} for state: {state_values}"
            )
