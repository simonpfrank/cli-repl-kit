# cli-repl-kit

**Warning** This was produced in hurry with some Vibe Coding sins along the way and therefore functionally it is not bad, but right now it is a nightmare for maintainability and coding standards, it is undergoing refactoring.

(Still under development and has outstanding defects, and critical code structure issues, being AI developed. Refactor underway)

A simple, reusable framework for building interactive command-line tools with both REPL and CLI modes.

## What is cli-repl-kit?

**cli-repl-kit** makes it easy to create command-line applications that work in two ways:

1. **REPL Mode** (Interactive): Users type commands one at a time, like a chat, with options for mulit line text and slash commands or just commands
2. **CLI Mode** (Traditional): Users run single commands directly from the terminal


## Why Use cli-repl-kit?

✅ **No REPL code to write** - The framework handles the interactive loop for you
✅ **Automatic command discovery** - Just declare your commands, no manual registration
✅ **Tab completion** - Claude Code style `/` prefix completion built-in
✅ **Beautiful output** - Rich console styling with colors and themes using `Rich`
✅ **Dual-mode by default** - REPL and CLI modes work automatically
✅ **Plugin-based** - Add commands without modifying framework code
✅ **Automatic validation** - Validation based on Click decorators, no manual methods needed
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

## How It Works

Understanding how cli-repl-kit works under the hood helps you build better applications and debug issues effectively.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User Input                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────▼─────────────┐
          │   CLI vs REPL Decision    │
          │  (sys.argv > 1?)          │
          └─────┬──────────────┬──────┘
                │              │
       ┌────────▼─────┐   ┌───▼──────────────┐
       │   CLI Mode    │   │   REPL Mode      │
       │  (Click CLI)  │   │ (prompt_toolkit) │
       └────────┬─────┘   └───┬──────────────┘
                │              │
                │         ┌────▼────────────────────┐
                │         │  ValidationManager      │
                │         │  (introspect commands)  │
                │         └─────────┬───────────────┘
                │                   │
         ┌──────▼───────────────────▼──────┐
         │      Command Execution           │
         │   (Click Command Tree)           │
         └──────────────┬───────────────────┘
                        │
                 ┌──────▼──────┐
                 │   Output     │
                 │ (stdout/err) │
                 └──────────────┘
```

### 1. Plugin Discovery

**When you start a cli-repl-kit application:**

```python
repl = REPL(app_name="My App", plugin_group="repl.commands")
```

**What happens:**

1. **Entry Point Scanning**: The framework uses Python's `importlib.metadata.entry_points()` to discover all plugins registered under the specified group

   ```toml
   # pyproject.toml
   [project.entry-points."repl.commands"]
   my_commands = "my_app.commands:MyCommandsPlugin"
   ```

2. **Plugin Loading**: Each discovered plugin class is instantiated and its `register()` method is called

3. **Command Registration**: Plugins register Click commands with the main CLI group

**Flow:**
```
pyproject.toml → entry_points() → Plugin.register() → Click CLI tree
```

### 2. Click Command Tree

cli-repl-kit builds on Click's command structure:

```python
cli (Group)
├── hello (Command)
├── deploy (Command)
└── config (Group)
    ├── get (Command)
    └── set (Command)
```

**Key Points:**
- Top-level is always a Click `Group`
- Commands can be added directly or nested in subgroups
- In REPL mode, commands use `/` prefix: `/hello`, `/config get`
- In CLI mode, no prefix needed: `my-cli hello`, `my-cli config get`

### 3. Validation Introspection

**Automatic validation is one of cli-repl-kit's killer features:**

```python
@click.command()
@click.argument("env", type=click.Choice(["dev", "staging", "prod"]))
def deploy(env):
    """Deploy to environment."""
    pass
```

**What happens:**

1. **Introspection**: `ValidationManager.introspect_commands()` walks the Click command tree

2. **Rule Extraction**: For each command, it extracts:
   - Required arguments
   - Optional arguments
   - Choice constraints
   - Required options

3. **Validation**: Before executing a command, the framework validates input:
   ```python
   result, level = validate_command("deploy", ["invalid"])
   # result.status = "invalid"
   # result.message = "Invalid choice: invalid. Choose from: dev, staging, prod"
   ```

4. **Blocking**: Invalid commands are blocked in REPL mode (CLI mode delegates to Click)

**Flow:**
```
Click Decorators → Introspection → Validation Rules → Pre-execution Check
```

### 4. REPL Event Loop

**When you run in REPL mode, here's the lifecycle:**

```python
repl.start()
```

**Initialization:**
1. Load configuration from `config.yaml` (or defaults)
2. Discover and register plugins
3. Build validation rules
4. Create UI layout (status, input, output, menu)
5. Set up key bindings

**Main Loop:**
```
┌─────────────────────────────────────────┐
│ 1. Display Prompt                        │
│    > / (cursor)                          │
└──────────┬──────────────────────────────┘
           │
┌──────────▼──────────────────────────────┐
│ 2. User Types                            │
│    > /dep                                │
│    - Key bindings handle each key        │
│    - Completer shows suggestions         │
└──────────┬──────────────────────────────┘
           │
┌──────────▼──────────────────────────────┐
│ 3. User Presses Enter                    │
│    - Validate command                    │
│    - If valid: execute                   │
│    - If invalid: show error, don't exec  │
└──────────┬──────────────────────────────┘
           │
┌──────────▼──────────────────────────────┐
│ 4. Execute Command                       │
│    - Capture stdout/stderr               │
│    - Append to output buffer             │
│    - Add to history                      │
└──────────┬──────────────────────────────┘
           │
           └──────► Back to step 1
```

**Components:**

- **LayoutBuilder**: Constructs the UI (output window, input window, status line, info line, menu)
- **KeyBindingManager**: Handles keyboard events (Tab, Enter, Arrow keys, Escape)
- **CommandExecutor**: Formats and executes commands, captures output
- **OutputCapture**: Redirects stdout/stderr to output buffer
- **REPLState**: Tracks current state (completions, selections, multiline mode)

### 5. CLI vs REPL Mode

**Automatic mode switching:**

```python
def main():
    repl = REPL(app_name="My App")

    if len(sys.argv) > 1:
        # CLI mode: my-cli hello World
        repl.cli(sys.argv[1:])
    else:
        # REPL mode: my-cli
        repl.start()
```

**Mode Comparison:**

| Feature | CLI Mode | REPL Mode |
|---------|----------|-----------|
| Execution | One command, then exit | Continuous loop |
| Validation | Click handles it | Pre-validated + Click |
| Output | Direct to terminal | Captured in buffer |
| History | Shell history | Built-in history |
| Completion | Shell completion | Built-in menu |
| Prefix | No prefix | `/` prefix |

### 6. Output Capture

**In REPL mode, all output is captured:**

```python
@click.command()
def hello():
    print("Hello, World!")  # ← Captured
    sys.stderr.write("Error!")  # ← Also captured
```

**How it works:**

1. `OutputCapture` class inherits from `io.StringIO`
2. Before command execution: `sys.stdout = OutputCapture("stdout", ...)`
3. During execution: All `print()` calls write to `OutputCapture`
4. `OutputCapture.write()` sends text to output buffer
5. After execution: `sys.stdout` is restored

**This allows:**
- Clean output display in REPL
- Color preservation
- Error highlighting
- Scrollback history

### 7. Configuration Loading

**Configuration is loaded in this order:**

1. **Default config**: Built-in defaults in `Config` class
2. **Package config**: `cli_repl_kit/config.yaml` (framework defaults)
3. **User config**: Specified via `config_path` parameter
4. **Merging**: User config overrides package config, which overrides defaults

```python
repl = REPL(
    app_name="My App",
    config_path="/path/to/custom/config.yaml"  # Optional
)
```

**Config structure:**

```yaml
appearance:
  ascii_art_text: "My App"
  box_width: 100
colors:
  divider: "cyan"
  prompt: "green"
  error: "red"
ansi_colors:
  red: "\033[31m"
  green: "\033[32m"
```

### 8. Context Injection

**Share state across commands using context factory:**

```python
def create_context():
    return {
        "user": "alice",
        "session_id": "abc123"
    }

repl = REPL(
    app_name="My App",
    context_factory=create_context
)

@repl.cli.command()
@click.pass_context
def whoami(ctx):
    user = ctx.obj["user"]  # Access shared context
    print(f"Current user: {user}")
```

**Context lifecycle:**
1. Context factory called once at startup
2. Context object stored in Click's `ctx.obj`
3. All commands can access via `@click.pass_context`
4. Modifications persist across commands (mutable dict)

### Performance Characteristics

Based on our performance benchmarks:

- **Startup time**: ~4ms (well under 500ms target)
- **Memory usage**: ~0.24MB (well under 50MB target)
- **Validation overhead**: ~0.015ms per command
- **Completion generation**: ~0.018ms per request
- **Config loading**: ~0.35ms

These benchmarks ensure the framework stays fast and responsive even for large command sets.

## Core Concepts

### 1. CommandPlugin

A **CommandPlugin** is a class that groups related commands together. Think of it as a "command package".

**Why use plugins?**
- Keeps your commands organized
- Allows automatic command discovery
- Easy to add/remove command groups
- YAML was considered but plugin appears to be more integrated

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

## Using Multiple Plugins

### Can Multiple Plugins Work Together?

**Yes!** cli-repl-kit is designed to support multiple plugins working together in the same application. All plugins are automatically discovered, loaded, and their commands are merged into a single CLI/REPL interface.

### How Multiple Plugins Work

When your app starts, the REPL:
1. **Discovers** all plugins from the `"repl.commands"` entry point group
2. **Instantiates** each plugin class
3. **Registers** all commands from all plugins into the same Click CLI
4. **Shares** the same context factory across all plugins

All commands from all plugins appear together in tab completion and `/help` output.

### Configuring Multiple Plugins

To use multiple plugins, simply add multiple entries to the `"repl.commands"` entry point in `pyproject.toml`:

```toml
[project.entry-points."repl.commands"]
file_commands = "my_app.plugins.files:FileCommandsPlugin"
git_commands = "my_app.plugins.git:GitCommandsPlugin"
config_commands = "my_app.plugins.config:ConfigCommandsPlugin"
```

**Important**: After changing entry points, you MUST reinstall your package:
```bash
pip install -e .
```

### Complete Example: Multi-Plugin App

Here's a complete example of an app with three plugins:

**Project structure:**
```
my-app/
├── pyproject.toml
├── my_app/
│   ├── __init__.py
│   ├── cli.py                # Entry point
│   └── plugins/
│       ├── __init__.py
│       ├── files.py          # File operations plugin
│       ├── git.py            # Git operations plugin
│       └── system.py         # System commands plugin
```

**`pyproject.toml`:**
```toml
[project]
name = "my-app"
version = "0.1.0"
dependencies = ["cli-repl-kit"]

[project.scripts]
my-app = "my_app.cli:main"

[project.entry-points."repl.commands"]
files = "my_app.plugins.files:FileCommandsPlugin"
git = "my_app.plugins.git:GitCommandsPlugin"
system = "my_app.plugins.system:SystemCommandsPlugin"
```

**`my_app/plugins/files.py`:**
```python
import click
from cli_repl_kit import CommandPlugin

class FileCommandsPlugin(CommandPlugin):
    @property
    def name(self):
        return "files"

    def register(self, cli, context_factory):
        @click.command()
        @click.argument("path")
        def copy(path):
            """Copy a file."""
            print(f"Copying {path}...")

        @click.command()
        @click.argument("path")
        def delete(path):
            """Delete a file."""
            print(f"Deleting {path}...")

        cli.add_command(copy, name="copy")
        cli.add_command(delete, name="delete")
```

**`my_app/plugins/git.py`:**
```python
import click
from cli_repl_kit import CommandPlugin

class GitCommandsPlugin(CommandPlugin):
    @property
    def name(self):
        return "git"

    def register(self, cli, context_factory):
        @click.group()
        def git():
            """Git operations."""
            pass

        @git.command()
        def status():
            """Show git status."""
            print("Git status...")

        @git.command()
        @click.argument("message")
        def commit(message):
            """Commit changes."""
            print(f"Committing: {message}")

        cli.add_command(git, name="git")
```

**`my_app/plugins/system.py`:**
```python
import click
from cli_repl_kit import CommandPlugin

class SystemCommandsPlugin(CommandPlugin):
    @property
    def name(self):
        return "system"

    def register(self, cli, context_factory):
        @click.command()
        def quit():
            """Exit the application."""
            print("Goodbye!")
            raise SystemExit(0)

        @click.command()
        def version():
            """Show version."""
            print("My App v0.1.0")

        cli.add_command(quit, name="quit")
        cli.add_command(version, name="version")
```

**`my_app/cli.py`:**
```python
import sys
from cli_repl_kit import REPL

def main():
    """Start the app."""
    repl = REPL(app_name="My App")

    if len(sys.argv) > 1:
        repl.cli(sys.argv[1:], standalone_mode=False)
    else:
        repl.start()

if __name__ == "__main__":
    main()
```

**Using the multi-plugin app:**
```
$ my-app
My App
Type /help for commands, /quit to exit

> /<TAB>
/copy      Copy a file
/delete    Delete a file
/git       Git operations
/quit      Exit the application
/version   Show version
/help      Show available commands

> /copy file.txt
■ /copy
  ⎿ file.txt
Copying file.txt...

> /git status
■ /git → status
Git status...

> /version
● /version
My App v0.1.0

> /quit
● /quit
Goodbye!
```

### Sharing Context Between Plugins

All plugins receive the same `context_factory` function, so they can access shared data:

```python
# In cli.py
def my_context():
    return {
        "config": load_config(),
        "db": connect_database(),
        "session": create_session()
    }

repl = REPL(app_name="My App", context_factory=my_context)
```

```python
# In ANY plugin
@click.command()
@click.pass_context
def some_command(ctx):
    """Access shared context."""
    config = ctx.obj["config"]      # Same config object
    db = ctx.obj["db"]              # Same database connection
    session = ctx.obj["session"]    # Same session object
```

### Command Name Collisions

**What happens if two plugins try to register the same command name?**

Click will raise an error during registration, and your app won't start. You'll see:
```
UsageError: The command 'status' already exists.
```

**How to avoid collisions:**

1. **Use unique command names** - Prefix with plugin name:
   ```python
   cli.add_command(show_status, name="git_status")  # Instead of "status"
   cli.add_command(show_info, name="file_info")     # Instead of "info"
   ```

2. **Use subcommand groups** (recommended):
   ```python
   # Instead of top-level "status" command from multiple plugins
   # Use groups: /git status, /network status, /system status
   @click.group()
   def git():
       pass

   @git.command()
   def status():
       pass

   cli.add_command(git, name="git")
   ```

### When to Use Multiple Plugins vs. One Plugin

**Use multiple plugins when:**
- Commands naturally group into separate concerns (files, git, network, etc.)
- Different team members own different command sets
- You want to enable/disable command groups independently
- Commands have different dependencies (one plugin needs database, another doesn't)

**Use a single plugin when:**
- All commands are closely related
- Your app is small (< 10 commands)
- Commands share significant implementation code
- You want simpler project structure

**Example**: The demo app uses **one plugin** because all commands are simple examples for the same purpose. A production app with file operations, git integration, and system monitoring would use **three plugins**.

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

### Status and Info Line Formatting

The built-in `/status` and `/info` commands support ANSI escape codes from the config for colored text:

**Using ANSI colors from config:**
```bash
# In REPL mode
> /status ${ansi.red}Error occurred${ansi.reset}
> /info ${ansi.cyan}Tip: ${ansi.reset}Use /help for commands

# The ${ansi.COLOR} patterns are replaced with actual ANSI codes
```

**Available ANSI codes** (from `config.ansi_colors`):

**Text styles:**
- `${ansi.bold}` - Bold text
- `${ansi.dim}` - Dim text
- `${ansi.italic}` - Italic text
- `${ansi.underline}` - Underlined text

**Foreground colors:**
- `${ansi.black}`, `${ansi.red}`, `${ansi.green}`, `${ansi.yellow}`
- `${ansi.blue}`, `${ansi.magenta}`, `${ansi.cyan}`, `${ansi.white}`

**Special:**
- `${ansi.reset}` - Reset all formatting (important!)

**Example usage:**
```bash
> /status ${ansi.yellow}Processing...${ansi.reset}
> /status ${ansi.green}${ansi.bold}Success!${ansi.reset}
> /info ${ansi.dim}Press Ctrl+C to cancel${ansi.reset}
```

**Note:** For command output (print statements), use the Rich Console as shown in the "Styling Command Output" section below.

### Automatic Validation

Validation is now completely automatic based on Click decorators. No manual validation methods needed!

#### How It Works

Validation is automatically inferred from your Click command definitions:

- **Required arguments** (`required=True`) → Blocks if missing
- **Choice types** (`click.Choice([...])`) → Blocks if invalid
- **Optional arguments** (with `default` or `nargs=-1`) → No validation (allows empty)

#### Example Implementation

```python
from cli_repl_kit import CommandPlugin
import click

class MyCommandsPlugin(CommandPlugin):
    @property
    def name(self):
        return "my_commands"

    def register(self, cli, context_factory):
        @click.command()
        @click.argument("environment", type=click.Choice(["dev", "staging", "prod"]))
        def deploy(environment):
            """Deploy to an environment (automatically validated!)."""
            if environment == "prod":
                click.echo("WARNING: Deploying to PRODUCTION!")
            print(f"Deploying to {environment}...")

        @click.command()
        @click.argument("text", nargs=-1, required=True)
        def hello(text):
            """Say hello (automatically validated!)."""
            print(f"Hello, {' '.join(text)}!")

        @click.command()
        @click.argument("path", nargs=-1)  # No required=True means optional
        def list_files(path):
            """List files (no validation - optional path)."""
            target = " ".join(path) if path else "."
            print(f"Listing files in {target}")

        cli.add_command(deploy, name="deploy")
        cli.add_command(hello, name="hello")
        cli.add_command(list_files, name="list_files")
```

#### Output Examples

**Required validation - blocked:**
```
> /hello
✗ Missing required argument: text
```
*(Command not executed, not in history)*

**Choice validation - blocked:**
```
> /deploy testing
✗ Invalid value: 'testing' is not one of 'dev', 'staging', 'prod'
```
*(Command not executed, not in history)*

**Valid commands:**
```
> /deploy staging
● /deploy
  ⎿ staging
Deploying to staging...

> /hello World
● /hello
  ⎿ World
Hello, World!

> /list_files
Listing files in .
```

#### Validation Levels

Validation level is automatically determined:

- **Required** - Commands with `required=True` args or `click.Choice` types
- **Optional** - Commands with optional arguments (have defaults)
- **None** - Commands with no parameters

No manual `get_validation_config()` or `validate_command()` methods needed!

### Mouse Selection in Output Area

You can now select and copy text from the output area using your mouse.

#### How to Use

1. Press **Ctrl+O** to toggle focus to the output area
2. Click and drag to select text with your mouse
3. Copy selected text with **Ctrl+C** or **Ctrl+Shift+C**
4. Press **Ctrl+O** again (or click the input area) to return focus

This is especially useful for copying command output, error messages, or long text blocks.

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

### Styling Command Output

Add colors, formatting, and styled output to your commands using Rich:

```python
import click
from cli_repl_kit import CommandPlugin
from rich.console import Console
from rich.table import Table

class StyledCommandsPlugin(CommandPlugin):
    @property
    def name(self):
        return "styled"

    def register(self, cli, context_factory):
        console = Console()

        @click.command()
        @click.argument("status", type=click.Choice(["success", "error", "warning"]))
        def status(status):
            """Show a styled status message."""
            if status == "success":
                console.print("✓ [green]Operation completed successfully![/green]")
            elif status == "error":
                console.print("✗ [red]Error: Operation failed![/red]")
            else:
                console.print("⚠ [yellow]Warning: Proceed with caution[/yellow]")

        @click.command()
        def table():
            """Show a styled table."""
            table = Table(title="User Data")
            table.add_column("Name", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Score", justify="right", style="yellow")

            table.add_row("Alice", "Active", "95")
            table.add_row("Bob", "Inactive", "78")
            table.add_row("Charlie", "Active", "89")

            console.print(table)

        @click.command()
        @click.argument("text")
        def highlight(text):
            """Print text with various styles."""
            console.print(f"[bold]Bold:[/bold] {text}")
            console.print(f"[italic]Italic:[/italic] {text}")
            console.print(f"[underline]Underlined:[/underline] {text}")
            console.print(f"[red]Red:[/red] {text}")
            console.print(f"[green]Green:[/green] {text}")
            console.print(f"[blue]Blue:[/blue] {text}")

        cli.add_command(status, name="status")
        cli.add_command(table, name="table")
        cli.add_command(highlight, name="highlight")
```

**Output examples:**
```
> /status success
● /status
  ⎿ success
✓ Operation completed successfully!    [in green]

> /table
● /table
╭────────────────────────────────╮
│         User Data              │
├─────────┬──────────┬───────────┤
│ Name    │ Status   │ Score     │
├─────────┼──────────┼───────────┤
│ Alice   │ Active   │        95 │
│ Bob     │ Inactive │        78 │
│ Charlie │ Active   │        89 │
╰─────────┴──────────┴───────────╯

> /highlight test
● /highlight
  ⎿ test
Bold: test
Italic: test
Underlined: test
Red: test        [each line in its respective color/style]
Green: test
Blue: test
```

**Available Rich features:**
- **Colors**: `[red]`, `[green]`, `[blue]`, `[yellow]`, `[cyan]`, `[magenta]`
- **Styles**: `[bold]`, `[italic]`, `[underline]`, `[dim]`, `[strike]`
- **Tables**: Create formatted tables with borders and colors
- **Progress bars**: Show progress for long operations
- **Syntax highlighting**: Display code with syntax coloring
- **Panels**: Create bordered boxes around content

See the [Rich documentation](https://rich.readthedocs.io/) for more styling options!

## Try the Live Demo

The repository includes a simple working demo app that showcases most framework features.

### Running the Demo

```bash
# Clone the repository
git clone https://github.com/simonpfrank/cli-repl-kit.git
cd cli-repl-kit

# Install in development mode
pip install -e .

# Interactive REPL mode
python -m demo.cli

# CLI mode (direct commands)
python -m demo.cli hello World
python -m demo.cli list_files
python -m demo.cli sub red "red text"
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
$ python -m demo.cli

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

> /list_files demo
■ /list_files
  ⎿ demo
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

1. **`demo/cli.py`** - Entry point with dual-mode support
2. **`demo/commands.py`** - All commands including validation
3. **`pyproject.toml`** - Package configuration with entry points

See [`demo/`](demo/) directory for the complete implementation!

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
from cli_repl_kit import CommandPlugin
import click

class MyPlugin(CommandPlugin):
    @property
    def name(self) -> str:
        """Plugin name for identification."""
        return "my_plugin"

    def register(self, cli, context_factory):
        """Register commands with the CLI group.

        Validation is automatic based on Click decorators:
        - Use required=True for required arguments
        - Use click.Choice([...]) for enum validation
        - Use default=value for optional arguments
        """
        @click.command()
        @click.argument("name", type=click.Choice(["dev", "prod"]))
        def deploy(name):
            """Example with automatic validation."""
            print(f"Deploying to {name}")

        cli.add_command(deploy, name="deploy")
```

### ValidationResult Class (Internal Use)

The `ValidationResult` class is used internally by the framework. You typically don't need to use it directly since validation is automatic.

```python
from cli_repl_kit.plugins.base import ValidationResult

result = ValidationResult(
    status="invalid",  # "valid", "invalid", or "warning"
    message="Error description"
)

result.is_valid()      # True if status is "valid" or "warning"
result.should_block()  # True if status is "invalid"
result.should_warn()   # True if status is "warning"
```

## Performance

cli-repl-kit is designed to be fast and lightweight, suitable for production tools and developer workflows.

### Benchmarks

Based on automated performance tests on macOS (Apple Silicon):

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Startup Time** | < 500ms | ~4ms | ✅ 125x faster |
| **Memory Usage** | < 50MB | ~0.24MB | ✅ 200x less |
| **Validation Overhead** | < 10ms | ~0.015ms | ✅ 600x faster |
| **Completion Generation** | < 50ms | ~0.018ms | ✅ 2700x faster |
| **Config Loading** | < 100ms | ~0.35ms | ✅ 285x faster |

### Performance Tips

1. **Large Command Sets**: The framework scales well to hundreds of commands
   - Validation introspection happens once at startup
   - Completion lookup is O(1) with dict-based caching

2. **Subprocess Commands**: Use timeouts to prevent hanging
   ```python
   subprocess.run(cmd, timeout=10)  # Timeout after 10 seconds
   ```

3. **Memory**: Framework overhead is minimal (~0.24MB)
   - Add monitoring if your commands load large datasets
   - Use lazy loading for heavy resources

4. **I/O Bound Commands**: Use async patterns if needed
   ```python
   import asyncio

   @click.command()
   def fetch():
       async def _fetch():
           # Async I/O operations
           pass
       asyncio.run(_fetch())
   ```

### Running Performance Tests

```bash
pytest tests/performance/ -v -s
```

This will output detailed timing information for all performance benchmarks.

## Security

cli-repl-kit prioritizes security for building production-ready CLI tools.

### Security Features

✅ **Safe Subprocess Execution**
- All framework and example code uses `subprocess.run()` with `shell=False`
- No shell injection possible by default

✅ **Path Traversal Prevention**
- Example commands validate paths are within allowed directories
- Use `pathlib.Path.resolve()` for safe path handling

✅ **Input Validation**
- Click's type validation automatically enforced
- Invalid commands blocked before execution in REPL mode

✅ **No Network Exposure**
- Framework is local-only, single-user design
- No authentication/authorization needed

### Security Best Practices

**1. Validate All User Inputs**

```python
from pathlib import Path

@click.command()
@click.argument("path")
def read_file(path):
    """Read a file (secure version)."""
    # Validate path
    target = Path(path).resolve()
    allowed_dir = Path.cwd().resolve()

    # Prevent path traversal
    if not str(target).startswith(str(allowed_dir)):
        print(f"Error: Access denied to {path}")
        return

    # Safe to read
    with open(target) as f:
        print(f.read())
```

**2. Whitelist Commands**

```python
ALLOWED_COMMANDS = ["git", "npm", "python"]

@click.command()
@click.argument("command", nargs=-1)
def shell(command):
    """Execute whitelisted commands only."""
    if command[0] not in ALLOWED_COMMANDS:
        print(f"Error: Command not allowed: {command[0]}")
        return

    subprocess.run(command, timeout=10)
```

**3. Use Timeouts**

```python
subprocess.run(cmd, timeout=10)  # Prevent hanging
```

**4. Handle Secrets Securely**

```python
import os

# Get from environment, never hardcode
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    print("Error: API_KEY environment variable not set")
    return
```

### Security Audit

Last audited: **2026-01-07**

**Verified:**
- ✅ No `shell=True` in subprocess calls
- ✅ Path traversal prevention in examples
- ✅ Input validation via Click types
- ✅ No hardcoded secrets
- ✅ Safe cross-platform command handling

**See:** `docs/SECURITY.md` for full security documentation.

## Platform Compatibility

cli-repl-kit works on all major platforms with platform-specific optimizations.

### Supported Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| **macOS** | ✅ Fully Supported | All features work, tested on Apple Silicon |
| **Linux** | ✅ Fully Supported | Tested on Ubuntu, Debian, RHEL |
| **Windows** | ✅ Supported | Requires Windows Terminal for best experience |

### Platform-Specific Features

**macOS/Linux:**
- Full ANSI color support
- Native terminal integration
- Clipboard support

**Windows:**
- ANSI colors via Windows Terminal
- ConPTY support on Windows 10+
- Legacy console mode for older versions

### Cross-Platform Command Handling

When writing commands that execute system utilities, use platform detection:

```python
import sys
import subprocess

@click.command()
@click.argument("path", default=".")
def list_files(path):
    """List files (cross-platform)."""
    # Platform-specific command
    if sys.platform == "win32":
        cmd = ["dir", "/W", path]
    else:
        cmd = ["ls", "-la", path]

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
```

### Path Handling

Always use `pathlib.Path` for cross-platform path handling:

```python
from pathlib import Path

# Good - works on all platforms
config_path = Path.home() / ".config" / "myapp" / "config.yaml"

# Bad - breaks on Windows
config_path = os.path.expanduser("~/.config/myapp/config.yaml")
```

### Testing on Windows

**Requirements:**
- Windows 10 or later (for best terminal support)
- Windows Terminal (recommended) or PowerShell 7+
- Python 3.8+

**Known Issues:**
- Legacy `cmd.exe` has limited ANSI support
  - **Solution**: Use Windows Terminal or PowerShell 7+
- Some Unicode characters may not display correctly
  - **Solution**: Use a font with good Unicode coverage (e.g., Cascadia Code)

### CI/CD Testing

cli-repl-kit includes CI/CD workflows (see `.github/workflows/`) that test on:
- Ubuntu Latest (Linux)
- macOS Latest (macOS)
- Windows Latest (Windows)

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

### Validation not working as expected?

Validation is now automatic based on Click decorators:

1. Use `required=True` for required arguments - missing args will be blocked
2. Use `click.Choice([...])` for enum validation - invalid choices will be blocked
3. Check that your Click decorators are correctly applied
4. For subcommands, validation applies to each subcommand individually

### Why Ctrl+J instead of Shift+Enter for multiline?

Shift+Enter is not reliably supported across different terminals in prompt_toolkit. The key binding requires terminal-specific escape sequences that vary between terminal emulators (iTerm, Terminal.app, gnome-terminal, etc.). Ctrl+J works consistently across all terminals and is the standard prompt_toolkit approach for multiline input.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Write tests first** (TDD methodology) - Define expected behavior with tests before implementing
2. **Keep it simple** - This framework prioritizes clarity over complexity
3. **Document for beginners** - Assume users have basic Python knowledge
4. **Follow code quality standards**:
   - Run `ruff check . --fix` to fix linting issues
   - Ensure all tests pass with `python -m pytest -xvs`
   - Add tests for new features

### How to Submit Changes

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/cli-repl-kit.git
   cd cli-repl-kit
   ```

3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

4. **Install in development mode**:
   ```bash
   pip install -e .
   ```

5. **Make your changes** following TDD:
   - Write tests first
   - Implement the feature
   - Run tests to verify
   - Fix any linting issues with `ruff check . --fix`

6. **Run all tests** to ensure nothing broke:
   ```bash
   python -m pytest -xvs
   ```

7. **Commit your changes** with a descriptive message:
   ```bash
   git add .
   git commit -m "feat: Add new feature description"
   # or
   git commit -m "fix: Fix bug description"
   ```

8. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

9. **Create a Pull Request**:
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Describe your changes and why they're needed
   - Link any related issues

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

### Code Quality Checks

```bash
# Run linting and auto-fix issues
ruff check . --fix

# Check for remaining issues
ruff check .
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
