"""Unit tests for the CommandPlugin base class."""
import pytest
import click
from abc import ABC


def test_cannot_instantiate_command_plugin_directly():
    """Test that CommandPlugin cannot be instantiated directly (it's abstract)."""
    from cli_repl_kit.plugins.base import CommandPlugin

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        CommandPlugin()


def test_command_plugin_is_abstract_base_class():
    """Test that CommandPlugin is an ABC."""
    from cli_repl_kit.plugins.base import CommandPlugin

    assert issubclass(CommandPlugin, ABC)


def test_subclass_must_implement_register():
    """Test that subclasses must implement the register() method."""
    from cli_repl_kit.plugins.base import CommandPlugin

    # Create subclass without register()
    class IncompletePlugin(CommandPlugin):
        @property
        def name(self):
            return "incomplete"

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompletePlugin()


def test_subclass_must_implement_name_property():
    """Test that subclasses must implement the name property."""
    from cli_repl_kit.plugins.base import CommandPlugin

    # Create subclass without name property
    class IncompletePlugin(CommandPlugin):
        def register(self, cli, context_factory):
            pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompletePlugin()


def test_complete_subclass_can_be_instantiated():
    """Test that a complete subclass can be instantiated."""
    from cli_repl_kit.plugins.base import CommandPlugin

    class CompletePlugin(CommandPlugin):
        @property
        def name(self):
            return "complete"

        def register(self, cli, context_factory):
            pass

    # Should not raise
    plugin = CompletePlugin()
    assert plugin.name == "complete"


def test_register_method_signature():
    """Test that register() method has correct signature."""
    from cli_repl_kit.plugins.base import CommandPlugin
    import inspect

    class TestPlugin(CommandPlugin):
        @property
        def name(self):
            return "test"

        def register(self, cli, context_factory):
            pass

    plugin = TestPlugin()
    sig = inspect.signature(plugin.register)
    params = list(sig.parameters.keys())

    # Should have cli and context_factory parameters
    assert "cli" in params
    assert "context_factory" in params


def test_register_can_add_commands_to_cli_group():
    """Test that register() can add commands to a Click group."""
    from cli_repl_kit.plugins.base import CommandPlugin

    class TestPlugin(CommandPlugin):
        @property
        def name(self):
            return "test"

        def register(self, cli, context_factory):
            @click.command()
            def hello():
                """Say hello."""
                pass

            cli.add_command(hello, name="hello")

    # Create a Click group
    cli_group = click.Group()
    plugin = TestPlugin()

    # Register commands
    plugin.register(cli_group, lambda: {})

    # Verify command was added
    assert "hello" in cli_group.commands
    assert cli_group.commands["hello"].help == "Say hello."


def test_multiple_plugins_can_register_to_same_cli():
    """Test that multiple plugins can register commands to the same CLI group."""
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

    cli_group = click.Group()

    Plugin1().register(cli_group, lambda: {})
    Plugin2().register(cli_group, lambda: {})

    # Both commands should be registered
    assert "cmd1" in cli_group.commands
    assert "cmd2" in cli_group.commands
