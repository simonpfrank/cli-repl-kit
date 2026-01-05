"""Unit tests for the REPL core class."""
import pytest
import click
from unittest.mock import Mock, patch, MagicMock


def test_repl_initialization_with_app_name():
    """Test that REPL can be initialized with an app name."""
    from cli_repl_kit.core.repl import REPL

    repl = REPL(app_name="Test App")
    assert repl.app_name == "Test App"


def test_repl_initialization_with_context_factory():
    """Test that REPL accepts a context factory."""
    from cli_repl_kit.core.repl import REPL

    context_factory = lambda: {"test": "context"}
    repl = REPL(app_name="Test App", context_factory=context_factory)
    assert repl.context_factory() == {"test": "context"}


def test_repl_creates_default_cli_group():
    """Test that REPL creates a default Click group if none provided."""
    from cli_repl_kit.core.repl import REPL

    repl = REPL(app_name="Test App")
    assert isinstance(repl.cli, click.Group)


def test_repl_accepts_existing_cli_group():
    """Test that REPL can accept an existing Click group."""
    from cli_repl_kit.core.repl import REPL

    @click.group()
    def my_cli():
        """My CLI."""
        pass

    repl = REPL(app_name="Test App", cli_group=my_cli)
    assert repl.cli is my_cli


def test_repl_has_default_plugin_group():
    """Test that REPL has a default plugin group name."""
    from cli_repl_kit.core.repl import REPL

    repl = REPL(app_name="Test App")
    assert repl.plugin_group == "repl.commands"


def test_repl_accepts_custom_plugin_group():
    """Test that REPL accepts a custom plugin group name."""
    from cli_repl_kit.core.repl import REPL

    repl = REPL(app_name="Test App", plugin_group="custom.commands")
    assert repl.plugin_group == "custom.commands"


@patch('cli_repl_kit.core.repl.entry_points')
def test_repl_discovers_plugins_from_entry_points(mock_entry_points):
    """Test that REPL discovers plugins via entry points."""
    from cli_repl_kit.core.repl import REPL
    from cli_repl_kit.plugins.base import CommandPlugin

    # Create a mock plugin
    class MockPlugin(CommandPlugin):
        @property
        def name(self):
            return "mock"

        def register(self, cli, context_factory):
            @click.command()
            def test_cmd():
                pass
            cli.add_command(test_cmd, name="test")

    # Mock entry point
    mock_ep = Mock()
    mock_ep.load.return_value = MockPlugin
    mock_entry_points.return_value = [mock_ep]

    repl = REPL(app_name="Test App")

    # Verify entry_points was called with correct group
    mock_entry_points.assert_called_once_with(group="repl.commands")

    # Verify plugin was loaded
    mock_ep.load.assert_called_once()

    # Verify command was registered
    assert "test" in repl.cli.commands


@patch('cli_repl_kit.core.repl.entry_points')
def test_repl_loads_multiple_plugins(mock_entry_points):
    """Test that REPL can load multiple plugins."""
    from cli_repl_kit.core.repl import REPL
    from cli_repl_kit.plugins.base import CommandPlugin

    class Plugin1(CommandPlugin):
        @property
        def name(self):
            return "plugin1"

        def register(self, cli, context_factory):
            @click.command()
            def cmd1():
                pass
            cli.add_command(cmd1, name="cmd1")

    class Plugin2(CommandPlugin):
        @property
        def name(self):
            return "plugin2"

        def register(self, cli, context_factory):
            @click.command()
            def cmd2():
                pass
            cli.add_command(cmd2, name="cmd2")

    # Mock entry points
    mock_ep1 = Mock()
    mock_ep1.load.return_value = Plugin1
    mock_ep2 = Mock()
    mock_ep2.load.return_value = Plugin2
    mock_entry_points.return_value = [mock_ep1, mock_ep2]

    repl = REPL(app_name="Test App")

    # Both commands should be registered
    assert "cmd1" in repl.cli.commands
    assert "cmd2" in repl.cli.commands


@patch('cli_repl_kit.core.repl.entry_points')
def test_repl_passes_context_factory_to_plugins(mock_entry_points):
    """Test that REPL passes context factory to plugins during registration."""
    from cli_repl_kit.core.repl import REPL
    from cli_repl_kit.plugins.base import CommandPlugin

    context_factory_called = []

    class TestPlugin(CommandPlugin):
        @property
        def name(self):
            return "test"

        def register(self, cli, context_factory):
            # Store that context_factory was passed
            context_factory_called.append(context_factory)

    mock_ep = Mock()
    mock_ep.load.return_value = TestPlugin
    mock_entry_points.return_value = [mock_ep]

    context_factory = lambda: {"test": "data"}
    repl = REPL(app_name="Test App", context_factory=context_factory)

    # Verify context factory was passed to plugin
    assert len(context_factory_called) == 1
    assert context_factory_called[0]() == {"test": "data"}


@patch('cli_repl_kit.core.repl.entry_points')
def test_repl_handles_no_plugins_gracefully(mock_entry_points):
    """Test that REPL handles the case where no plugins are found."""
    from cli_repl_kit.core.repl import REPL

    mock_entry_points.return_value = []

    # Should not raise
    repl = REPL(app_name="Test App")
    assert isinstance(repl.cli, click.Group)
    # Should have 4 built-in commands (print, error, status, info) even with no plugins
    assert len(repl.cli.commands) == 4
    assert "print" in repl.cli.commands
    assert "error" in repl.cli.commands
    assert "status" in repl.cli.commands
    assert "info" in repl.cli.commands


def test_repl_has_start_method():
    """Test that REPL has a start() method."""
    from cli_repl_kit.core.repl import REPL

    repl = REPL(app_name="Test App")
    assert hasattr(repl, "start")
    assert callable(repl.start)


@patch('cli_repl_kit.core.repl.entry_points')
def test_repl_default_context_factory_returns_empty_dict(mock_entry_points):
    """Test that REPL has a default context factory that returns empty dict."""
    from cli_repl_kit.core.repl import REPL

    mock_entry_points.return_value = []

    repl = REPL(app_name="Test App")
    assert repl.context_factory() == {}


@patch('cli_repl_kit.core.repl.entry_points')
def test_repl_stores_configuration(mock_entry_points):
    """Test that REPL stores configuration parameters."""
    from cli_repl_kit.core.repl import REPL

    mock_entry_points.return_value = []

    repl = REPL(
        app_name="My App",
        plugin_group="my.plugins",
        context_factory=lambda: {"config": "value"}
    )

    assert repl.app_name == "My App"
    assert repl.plugin_group == "my.plugins"
    assert repl.context_factory() == {"config": "value"}
