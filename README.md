# cli-repl-kit

A simple, reusable framework for building interactive command-line tools with both REPL and CLI modes.

## What is cli-repl-kit?

**cli-repl-kit** makes it easy to create professional command-line applications that work in two ways:

1. **REPL Mode** (Interactive): Users type commands one at a time, like a chat
2. **CLI Mode** (Traditional): Users run single commands directly from the terminal

**Think of it like this**: Your app is like a restaurant that offers both dine-in (REPL) and takeout (CLI)!

## Why Use cli-repl-kit?

✅ **No REPL code to write** - The framework handles the interactive loop for you
✅ **Automatic command discovery** - Just declare your commands, no manual registration
✅ **Tab completion** - Claude Code style `/` prefix completion built-in
✅ **Beautiful output** - Rich console styling with colors and themes
✅ **Dual-mode by default** - REPL and CLI modes work automatically
✅ **Plugin-based** - Add commands without modifying framework code

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/simonpfrank/cli-repl-kit.git@main

# Or for development (editable mode)
git clone https://github.com/simonpfrank/cli-repl-kit.git
cd cli-repl-kit
pip install -e .
```

## Quick Start

Here's a complete "Hello World" application in just 3 files:

### 1. Create project structure

```
my-cli-app/
├── pyproject.toml          # Project configuration
├── my_cli_app/
│   ├── __init__.py         # Empty file
│   ├── cli.py              # Entry point
│   └── commands.py         # Your commands
```

### 2. Configure `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-cli-app"
version = "0.1.0"
dependencies = [
    "cli-repl-kit @ git+https://github.com/simonpfrank/cli-repl-kit.git@main",
]

[project.scripts]
my-cli = "my_cli_app.cli:main"

[project.entry-points."repl.commands"]
my_commands = "my_cli_app.commands:MyCommandsPlugin"
```

### 3. Write `cli.py` (entry point)

```python
"""Entry point for your CLI/REPL."""
from cli_repl_kit import REPL

def main():
    """Start the CLI/REPL."""
    repl = REPL(app_name="My CLI App")
    repl.start()

if __name__ == "__main__":
    main()
```

### 4. Write `commands.py` (your commands)

```python
"""Commands for your application."""
import click
from cli_repl_kit import CommandPlugin, format_success, format_info

class MyCommandsPlugin(CommandPlugin):
    """My application commands."""

    @property
    def name(self):
        return "my_commands"

    def register(self, cli, context_factory):
        """Register commands with the REPL."""

        @click.command()
        @click.argument("name")
        def greet(name):
            """Greet someone by name."""
            print(format_success(f"Hello, {name}!"))

        @click.command()
        def info():
            """Show application info."""
            print(format_info("My CLI App v0.1.0"))

        cli.add_command(greet, name="greet")
        cli.add_command(info, name="info")
```

### 5. Install and run

```bash
# Install your app
pip install -e .

# Run in REPL mode (interactive)
my-cli
> /greet Alice
✓ Hello, Alice!
> /info
ℹ My CLI App v0.1.0
> /quit

# Run in CLI mode (direct commands)
my-cli greet Bob
✓ Hello, Bob!

my-cli info
ℹ My CLI App v0.1.0
```

That's it! You now have a working CLI/REPL app with tab completion and colored output.

## Core Concepts (Explained Simply)

### 1. CommandPlugin

A **CommandPlugin** is a class that groups related commands together. Think of it as a "command package".

**Why use plugins?**
- Keeps your commands organized
- Allows automatic command discovery
- Easy to add/remove command groups

**Example**: If you're building a file manager, you might have:
- `FileCommandsPlugin` - for copy, move, delete
- `SearchCommandsPlugin` - for find, grep
- `SystemCommandsPlugin` - for help, quit, exit

### 2. Entry Points

**Entry points** tell Python where to find your plugins. They're declared in `pyproject.toml`.

```toml
[project.entry-points."repl.commands"]
my_commands = "my_cli_app.commands:MyCommandsPlugin"
```

**Translation**: "Hey Python, there's a plugin called `my_commands` in the file `my_cli_app/commands.py`, and it's the class `MyCommandsPlugin`."

**Important**: After changing entry points, reinstall your package:
```bash
pip install -e .
```

### 3. Click Commands

**Click** is a Python library for building command-line interfaces. cli-repl-kit uses Click commands.

```python
@click.command()
@click.argument("name")  # Required argument
@click.option("--greeting", default="Hello")  # Optional flag
def greet(name, greeting):
    """Greet someone."""
    print(f"{greeting}, {name}!")
```

**Learn more**: https://click.palletsprojects.com/

### 4. Context Factory

A **context factory** is a function that returns shared data for your commands.

**Use case**: Database connections, configuration, shared state.

```python
def my_context_factory():
    return {
        "config": load_config(),
        "db": connect_database()
    }

repl = REPL(
    app_name="My App",
    context_factory=my_context_factory
)
```

**Access context in commands**:
```python
@click.command()
@click.pass_context
def show_config(ctx):
    """Show configuration."""
    config = ctx.obj["config"]
    print(config)
```

## Step-by-Step Guide: Adding cli-repl-kit to Your Project

### Step 1: Add dependency

```toml
# pyproject.toml
[project]
dependencies = [
    "cli-repl-kit @ git+https://github.com/simonpfrank/cli-repl-kit.git@main",
]
```

### Step 2: Create entry point

```python
# my_project/cli.py
from cli_repl_kit import REPL

def main():
    repl = REPL(app_name="My Project")
    repl.start()
```

### Step 3: Declare script in pyproject.toml

```toml
[project.scripts]
my-cli = "my_project.cli:main"
```

### Step 4: Create command plugin

```python
# my_project/commands.py
import click
from cli_repl_kit import CommandPlugin

class MyCommandsPlugin(CommandPlugin):
    @property
    def name(self):
        return "my_commands"

    def register(self, cli, context_factory):
        @click.command()
        def hello():
            """Say hello."""
            print("Hello!")

        cli.add_command(hello, name="hello")
```

### Step 5: Register plugin in pyproject.toml

```toml
[project.entry-points."repl.commands"]
my_commands = "my_project.commands:MyCommandsPlugin"
```

### Step 6: Install and test

```bash
pip install -e .
my-cli        # REPL mode
my-cli hello  # CLI mode
```

## Features in Detail

### Tab Completion

cli-repl-kit provides automatic tab completion with `/` prefix (Claude Code style):

```
> /h<TAB>
/help     Show available commands
/history  Show command history

> /config <TAB>
show  Show configuration
load  Load configuration file
save  Save configuration

> /config load --<TAB>
--file    Config file path
--force   Force reload
```

**No configuration needed** - works automatically for all Click commands!

### Styling and Formatting

cli-repl-kit includes Rich console styling for beautiful terminal output:

```python
from cli_repl_kit import (
    format_success,  # Green checkmark
    format_error,    # Red cross
    format_warning,  # Yellow warning
    format_info      # Blue info
)

print(format_success("Operation completed!"))
# ✓ Operation completed!

print(format_error("Something went wrong"))
# ✗ Error: Something went wrong

print(format_warning("Please be careful"))
# ⚠ Warning: Please be careful

print(format_info("Here's some information"))
# ℹ Here's some information
```

**Custom themes**:
```python
from cli_repl_kit import APP_THEME
from rich.console import Console

console = Console(theme=APP_THEME)
console.print("[success]Success![/success]")  # Green
console.print("[error]Error![/error]")        # Red
console.print("[warning]Warning![/warning]")  # Yellow
```

### Subcommands and Groups

Organize related commands into groups:

```python
import click
from cli_repl_kit import CommandPlugin

class ConfigCommandsPlugin(CommandPlugin):
    @property
    def name(self):
        return "config"

    def register(self, cli, context_factory):
        @click.group()
        def config():
            """Configuration commands."""
            pass

        @config.command()
        def show():
            """Show configuration."""
            print("Current config...")

        @config.command()
        @click.option("--file", help="Config file path")
        def load(file):
            """Load configuration."""
            print(f"Loading from {file}...")

        cli.add_command(config, name="config")
```

**Usage**:
```
> /config show
Current config...

> /config load --file config.yaml
Loading from config.yaml...
```

## Examples

### Example 1: Calculator App

```python
# calculator/commands.py
import click
from cli_repl_kit import CommandPlugin, format_success

class CalculatorPlugin(CommandPlugin):
    @property
    def name(self):
        return "calculator"

    def register(self, cli, context_factory):
        @click.command()
        @click.argument("a", type=float)
        @click.argument("b", type=float)
        def add(a, b):
            """Add two numbers."""
            result = a + b
            print(format_success(f"{a} + {b} = {result}"))

        @click.command()
        @click.argument("a", type=float)
        @click.argument("b", type=float)
        def multiply(a, b):
            """Multiply two numbers."""
            result = a * b
            print(format_success(f"{a} × {b} = {result}"))

        cli.add_command(add, name="add")
        cli.add_command(multiply, name="multiply")
```

### Example 2: File Manager App

```python
# filemanager/commands.py
import click
import os
from cli_repl_kit import CommandPlugin, format_success, format_error

class FileCommandsPlugin(CommandPlugin):
    @property
    def name(self):
        return "files"

    def register(self, cli, context_factory):
        @click.command()
        def list_files():
            """List files in current directory."""
            files = os.listdir(".")
            for f in files:
                print(f"  • {f}")

        @click.command()
        @click.argument("filename")
        def read(filename):
            """Read a file."""
            try:
                with open(filename, "r") as f:
                    print(f.read())
            except FileNotFoundError:
                print(format_error(f"File '{filename}' not found"))

        cli.add_command(list_files, name="ls")
        cli.add_command(read, name="read")
```

### Example 3: App with Context (Database Connection)

```python
# myapp/cli.py
from cli_repl_kit import REPL
from myapp.database import connect_db

def context_factory():
    """Create context with database connection."""
    return {
        "db": connect_db(),
        "user": "admin"
    }

def main():
    repl = REPL(
        app_name="My Database App",
        context_factory=context_factory
    )
    repl.start()

# myapp/commands.py
import click
from cli_repl_kit import CommandPlugin

class DatabaseCommandsPlugin(CommandPlugin):
    @property
    def name(self):
        return "database"

    def register(self, cli, context_factory):
        @click.command()
        @click.pass_context
        def users(ctx):
            """List all users."""
            db = ctx.obj["db"]
            users = db.query("SELECT * FROM users")
            for user in users:
                print(f"  • {user['name']}")

        cli.add_command(users, name="users")
```

## API Reference

### REPL Class

```python
from cli_repl_kit import REPL

repl = REPL(
    app_name="My App",              # Required: App name for prompts/history
    context_factory=None,            # Optional: Function returning context dict
    cli_group=None,                  # Optional: Existing Click group
    plugin_group="repl.commands"     # Optional: Entry point group name
)

repl.start()  # Start REPL or execute CLI command
```

### CommandPlugin Class

```python
from cli_repl_kit import CommandPlugin

class MyPlugin(CommandPlugin):
    @property
    def name(self) -> str:
        """Plugin name for identification."""
        return "my_plugin"

    def register(self, cli, context_factory):
        """Register commands with the CLI group."""
        # Add your commands here
        pass
```

### SlashCommandCompleter

```python
from cli_repl_kit import SlashCommandCompleter

completer = SlashCommandCompleter(
    commands={"help": "Show help", "quit": "Exit"},  # Command dict
    cli_group=None  # Optional: Click group for subcommand completion
)
```

### Styling Functions

```python
from cli_repl_kit import (
    format_success,   # Green ✓ with message
    format_error,     # Red ✗ with "Error:" label
    format_warning,   # Yellow ⚠ with "Warning:" label
    format_info,      # Blue ℹ with message
    APP_THEME,        # Rich Theme object
    SYMBOLS           # Dict of Unicode symbols
)
```

## Troubleshooting

### Commands not showing up?

1. Check your entry point is correct in `pyproject.toml`:
   ```toml
   [project.entry-points."repl.commands"]
   my_commands = "my_app.commands:MyCommandsPlugin"
   ```

2. Reinstall your package:
   ```bash
   pip install -e .
   ```

3. Verify the plugin class exists:
   ```python
   # In my_app/commands.py
   class MyCommandsPlugin(CommandPlugin):  # Must match entry point!
       ...
   ```

### Tab completion not working?

Tab completion works automatically in REPL mode. Make sure you're using the `/` prefix:
```
> /h<TAB>    # ✓ Works
> h<TAB>     # ✗ Won't show completions
```

### ImportError: No module named 'cli_repl_kit'?

Make sure cli-repl-kit is installed:
```bash
pip install git+https://github.com/simonpfrank/cli-repl-kit.git@main
```

### Context not available in commands?

Use `@click.pass_context` decorator:
```python
@click.command()
@click.pass_context
def my_command(ctx):
    config = ctx.obj["config"]  # Access context
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Write tests first** (TDD methodology)
2. **Keep it simple** - This framework prioritizes clarity over complexity
3. **Document for beginners** - Assume users have basic Python knowledge
4. **Run tests** before submitting:
   ```bash
   PYTHONPATH=src python -m pytest tests/unit/ -v
   ```

### Development Setup

```bash
git clone https://github.com/simonpfrank/cli-repl-kit.git
cd cli-repl-kit
pip install -e .
```

### Running Tests

```bash
# All tests
PYTHONPATH=src python -m pytest tests/unit/ -v

# Specific test file
PYTHONPATH=src python -m pytest tests/unit/test_completion.py -v

# With coverage
PYTHONPATH=src python -m pytest tests/unit/ --cov=src/cli_repl_kit
```

## License

MIT License - See LICENSE file for details

## Credits

Built with:
- [Click](https://click.palletsprojects.com/) - Command-line interface framework
- [Rich](https://rich.readthedocs.io/) - Terminal styling and formatting
- [prompt-toolkit](https://python-prompt-toolkit.readthedocs.io/) - Interactive prompt building

## Support

- 📝 **Issues**: https://github.com/simonpfrank/cli-repl-kit/issues
- 📖 **Documentation**: See [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
- 💬 **Discussions**: https://github.com/simonpfrank/cli-repl-kit/discussions

---

**Made with ❤️ for Python developers who want to build great CLIs without the boilerplate**
