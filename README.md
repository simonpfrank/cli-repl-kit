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
✅ **Command validation** - Validate arguments before execution with flexible levels
✅ **Subcommand support** - Organize commands with clean arrow notation

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
import sys
from cli_repl_kit import REPL

def main():
    """Start the CLI/REPL.

    Supports both modes:
    - CLI mode: When called with arguments
    - REPL mode: When called without arguments (interactive)
    """
    repl = REPL(app_name="My CLI App")

    # If arguments provided, run in CLI mode
    if len(sys.argv) > 1:
        try:
            repl.cli(sys.argv[1:], standalone_mode=False)
        except SystemExit as e:
            sys.exit(e.code)
    else:
        # No arguments - enter REPL mode
        repl.start()

if __name__ == "__main__":
    main()
```

### 4. Write `commands.py` (your commands)

```python
"""Commands for your application."""
import click
from cli_repl_kit import CommandPlugin

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
            print(f"Hello, {name}!")

        @click.command()
        def info():
            """Show application info."""
            print("My CLI App v0.1.0")

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
● /greet
  ⎿ Alice
Hello, Alice!

> /info
● /info
My CLI App v0.1.0

> /quit

# Run in CLI mode (direct commands)
my-cli greet Bob
Hello, Bob!

my-cli info
My CLI App v0.1.0
```

That's it! You now have a working CLI/REPL app with tab completion and styled output.

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

## Key Features

### Tab Completion

cli-repl-kit provides automatic tab completion with `/` prefix (Claude Code style):

```
> /h<TAB>
/hello     Say hello with custom text
/help      Show available commands

> /config <TAB>
show  Show configuration
load  Load configuration file
save  Save configuration

> /config load --<TAB>
--file    Config file path
--force   Force reload
```

**No configuration needed** - works automatically for all Click commands!

### Command Validation

Validate command arguments before execution with three flexible levels:

#### Validation Levels

- **Required** (`"required"`) - Block invalid commands, show red ● bullet
- **Optional** (`"optional"`) - Warn but allow execution, show yellow ⚠ icon
- **None** (`"none"` or default) - No validation, normal execution

#### Example Implementation

```python
from cli_repl_kit import CommandPlugin, ValidationResult
import click

class MyCommandsPlugin(CommandPlugin):
    @property
    def name(self):
        return "my_commands"

    def register(self, cli, context_factory):
        @click.command()
        @click.argument("environment")
        def deploy(environment):
            """Deploy to an environment."""
            print(f"Deploying to {environment}...")

        @click.command()
        @click.argument("message", nargs=-1)
        def echo(message):
            """Echo a message."""
            print(" ".join(message))

        cli.add_command(deploy, name="deploy")
        cli.add_command(echo, name="echo")

    def get_validation_config(self):
        """Configure validation levels for commands."""
        return {
            "deploy": "required",  # Block invalid environments
            "echo": "optional",    # Warn about deprecation
        }

    def validate_command(self, cmd_name, cmd_args, parsed_args):
        """Validate command arguments."""
        if cmd_name == "deploy":
            # Required validation - block invalid environments
            allowed = ["dev", "staging", "prod"]
            env = cmd_args[0] if cmd_args else ""
            if env not in allowed:
                return ValidationResult(
                    status="invalid",
                    message=f"Environment must be one of: {', '.join(allowed)}"
                )
            return ValidationResult(status="valid")

        elif cmd_name == "echo":
            # Optional validation - warn about deprecation
            return ValidationResult(
                status="warning",
                message="The 'echo' command is deprecated, use 'print' instead"
            )

        return ValidationResult(status="valid")
```

#### Output Examples

**Required validation - blocked:**
```
> /deploy testing
● /deploy
  ⎿ testing
✗ Environment must be one of: dev, staging, prod
```
*(Command not executed, not in history)*

**Optional validation - warning:**
```
> /echo hello world
⚠ /echo
  ⎿ hello world
⚠ The 'echo' command is deprecated, use 'print' instead
hello world
```
*(Command executed, added to history)*

**Valid command:**
```
> /deploy staging
● /deploy
  ⎿ staging
Deploying to staging...
```

### Subcommands with Clean Formatting

Organize related commands into groups with automatic arrow notation:

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

**Output with automatic arrow formatting:**
```
> /config show
■ /config → show
Current config...

> /config load --file config.yaml
■ /config → load
  ⎿ --file config.yaml
Loading from config.yaml...
```

Subcommands are automatically detected and formatted with arrow icons (→) for clarity!

### Calling External Commands

Easily integrate command-line tools using subprocess:

```python
import click
import subprocess
from cli_repl_kit import CommandPlugin

class FileCommandsPlugin(CommandPlugin):
    @property
    def name(self):
        return "files"

    def register(self, cli, context_factory):
        @click.command()
        @click.argument("path", default=".")
        def list_files(path):
            """List files in a directory."""
            try:
                result = subprocess.run(
                    ["ls", "-la", path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"Error: {e.stderr}")

        cli.add_command(list_files, name="list_files")
```

**Output:**
```
> /list_files
■ /list_files
total 48
drwxr-xr-x  12 user  staff   384 Jan  6 10:30 .
drwxr-xr-x   8 user  staff   256 Jan  5 15:20 ..
-rw-r--r--   1 user  staff  1234 Jan  6 09:15 README.md
...
```

The REPL automatically captures and displays all output from external commands!

## Try the Live Demo

The repository includes a fully working demo app that showcases all framework features.

### Running the Demo

```bash
# Clone the repository
git clone https://github.com/simonpfrank/cli-repl-kit.git
cd cli-repl-kit

# Install in development mode
pip install -e .

# Interactive REPL mode
python -m example.cli

# CLI mode (direct commands)
python -m example.cli hello World
python -m example.cli list_files
python -m example.cli sub red "red text"
```

### Demo Features

The demo includes:
- **Command validation** - Try `/print` without arguments (required validation)
- **Subcommands** - Try `/sub red text` (automatic arrow formatting)
- **External commands** - Try `/list_files` (subprocess integration)
- **Tab completion** - Type `/` and press TAB
- **Agent mode** - Type text without `/` prefix for echo

### Example Session

```
$ python -m example.cli

Hello World Demo
Type /help for commands, /quit to exit

> /hello World
■ /hello
  ⎿ World
hello - World

> /sub red This text is red
■ /sub → red
  ⎿ This text is red
RED: This text is red

> /list_files example
■ /list_files
  ⎿ example
total 24
-rw-r--r--  1 user  staff   892 Jan  6 10:30 cli.py
-rw-r--r--  1 user  staff  2145 Jan  6 09:45 commands.py
...

> /print
● /print
✗ Text argument is required for print command

> /hello
⚠ /hello
⚠ Tip: Try '/hello World' with a name for a custom greeting!
hello - (no text provided)

> just some text without a slash
Echo: just some text without a slash

> /quit
Goodbye!
```

### Demo Code

The entire demo is just **3 small files** (~100 lines total):

1. **`example/cli.py`** - Entry point with dual-mode support
2. **`example/commands.py`** - All commands including validation
3. **`pyproject.toml`** - Package configuration with entry points

See [`example/`](example/) directory for the complete implementation!

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

# For REPL mode
repl.start(enable_agent_mode=False)

# For CLI mode (call from main with sys.argv)
repl.cli(sys.argv[1:], standalone_mode=False)
```

### CommandPlugin Class

```python
from cli_repl_kit import CommandPlugin, ValidationResult

class MyPlugin(CommandPlugin):
    @property
    def name(self) -> str:
        """Plugin name for identification."""
        return "my_plugin"

    def register(self, cli, context_factory):
        """Register commands with the CLI group."""
        # Add your Click commands here
        pass

    def get_validation_config(self) -> dict:
        """Optional: Return validation configuration.

        Returns dict mapping command names to levels:
        - "required": Validate and block if invalid
        - "optional": Validate and warn if invalid
        - "none": No validation (default)
        """
        return {}

    def validate_command(self, cmd_name, cmd_args, parsed_args):
        """Optional: Validate command arguments.

        Returns ValidationResult with:
        - status: "valid", "invalid", or "warning"
        - message: Optional message to display
        """
        return ValidationResult(status="valid")
```

### ValidationResult Class

```python
from cli_repl_kit import ValidationResult

result = ValidationResult(
    status="invalid",  # "valid", "invalid", or "warning"
    message="Error description"
)

result.is_valid()      # True if status is "valid" or "warning"
result.should_block()  # True if status is "invalid"
result.should_warn()   # True if status is "warning"
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

### Validation not working?

1. Make sure both `get_validation_config()` and `validate_command()` are implemented
2. Check that command name matches exactly (case-sensitive)
3. For subcommands, use dot notation: `"config.set"`

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Write tests first** (TDD methodology)
2. **Keep it simple** - This framework prioritizes clarity over complexity
3. **Document for beginners** - Assume users have basic Python knowledge
4. **Run tests** before submitting:
   ```bash
   python -m pytest -xvs
   ```

### Development Setup

```bash
git clone https://github.com/simonpfrank/cli-repl-kit.git
cd cli-repl-kit
pip install -e .
```

### Running Tests

```bash
# All tests (unit + integration)
python -m pytest -xvs

# Unit tests only
python -m pytest tests/unit/ -xvs

# Integration tests only
python -m pytest tests/integration/ -xvs

# With coverage
python -m pytest --cov=cli_repl_kit
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
