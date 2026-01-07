# Hello World Demo

A simple demo application showcasing cli-repl-kit features.

## Features

This demo includes:

1. **`/quit`** - Exit the application
2. **`/hello <text>`** - Prints "hello - <text>"
3. **`/sub red <text>`** - Prints text in red color
4. **`/sub blue <text>`** - Prints text in blue color
5. **Agent mode** - Type text without `/` and it echoes back

## Installation

From the `example` directory:

```bash
# Make sure cli-repl-kit is installed
cd ..
pip install -e .

# Install the demo app
cd example
pip install -e .
```

## Usage

### REPL Mode (Interactive)

```bash
hello-world
```

Example session:
```
Hello World Demo
Type /help for commands, /quit to exit

> /hello world
hello - world

> /sub red this is red text
this is red text

> /sub blue this is blue text
this is blue text

> just typing some text
Echo: just typing some text

> /quit
Goodbye!
```

### CLI Mode (Direct Commands)

```bash
# Run commands directly
hello-world hello "from the command line"
hello-world sub red "red text"
hello-world sub blue "blue text"
```

## Tab Completion

The REPL supports tab completion with the `/` prefix:

```
> /h<TAB>
/hello    Say hello with custom text

> /sub <TAB>
red   Print text in red
blue  Print text in blue
```

## File Structure

```
example/
├── pyproject.toml          # Project configuration
├── __init__.py             # Package init
├── cli.py                  # Entry point
├── commands.py             # Command implementations
├── run.sh                  # Convenience script
└── README.md               # This file
```

## How It Works

1. **cli.py** creates a REPL instance and enables agent mode
2. **commands.py** defines commands as a CommandPlugin
3. **pyproject.toml** registers the plugin via entry points
4. cli-repl-kit discovers and loads the commands automatically

This demonstrates the plugin-based architecture where commands are automatically discovered without any manual registration!
