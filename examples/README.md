# cli-repl-kit Examples

Progressive examples showing how to build command-line applications with cli-repl-kit.

## Overview

These examples build on each other, introducing one new concept at a time:

1. **01_basic_hello.py** - Simplest possible app (single command)
2. **02_with_arguments.py** - Commands with arguments
3. **03_validation.py** - Automatic validation with Click types
4. **04_subcommands.py** - Organizing commands into groups
5. **05_advanced.py** - Context injection, subprocess, REPL API

## Running the Examples

Each example can be run in two modes:

### REPL Mode (Interactive)
```bash
python examples/01_basic_hello.py
```

This starts an interactive REPL where you can type commands:
```
> /hello
Hello, World!
> /quit
```

### CLI Mode (Direct Execution)
```bash
python examples/01_basic_hello.py hello
```

This executes the command directly and exits (traditional CLI behavior).

## Example Progression

### Example 01: Basic Hello
**Concepts:** REPL creation, simple command

The absolute minimum - create a REPL and register one command:
```python
repl = REPL(app_name="My App")

@repl.cli.command()
def hello():
    print("Hello, World!")

repl.start()
```

### Example 02: With Arguments
**Concepts:** Arguments, nargs, type conversion

Commands can accept arguments:
```python
@repl.cli.command()
@click.argument("name", nargs=-1, required=True)
def greet(name):
    full_name = " ".join(name)
    print(f"Hello, {full_name}!")
```

The `nargs=-1` means "accept multiple arguments" and `required=True` makes validation automatic.

### Example 03: Validation
**Concepts:** Click.Choice, automatic validation, error handling

cli-repl-kit automatically validates commands based on Click decorators:
```python
@repl.cli.command()
@click.argument("env", type=click.Choice(["dev", "test", "prod"]))
def deploy(env):
    print(f"Deploying to: {env}")
```

Try invalid input in REPL:
```
> /deploy staging
❌ Invalid value for 'env': 'staging' is not one of 'dev', 'test', 'prod'
```

### Example 04: Subcommands
**Concepts:** Click.Group, command organization, dot notation

Organize related commands into groups:
```python
@repl.cli.group()
def config():
    """Configuration commands."""
    pass

@config.command()
@click.argument("key")
def get(key):
    print(f"Config value for '{key}'")
```

In REPL, use dot notation:
```
> /config get theme
Config value for 'theme': dark
```

### Example 05: Advanced
**Concepts:** Context factory, dependency injection, subprocess, REPL API

#### Context Injection
Share state across commands:
```python
def create_context():
    return {"user": "alice", "session_id": "abc123"}

repl = REPL(app_name="App", context_factory=create_context)

@repl.cli.command()
@click.pass_context
def whoami(ctx):
    print(f"User: {ctx.obj['user']}")
```

#### Subprocess Execution
Execute shell commands safely:
```python
@repl.cli.command()
@click.argument("command", nargs=-1)
def shell(command):
    result = subprocess.run(list(command), capture_output=True, text=True)
    print(result.stdout)
```

#### REPL API
Control the REPL from commands:
```python
@repl.cli.command()
@click.argument("text", nargs=-1)
def status(text):
    message = " ".join(text)
    repl.set_status(message, style="yellow")
```

## What to Build Next

After working through these examples, you're ready to build your own applications. Common patterns:

### Database Management Tool
Use groups for different database operations (connect, query, migrate).

### File Processing Tool
Commands for reading, transforming, and writing files with validation.

### API Testing Tool
Commands for making HTTP requests with context for auth tokens.

### DevOps Dashboard
Commands for checking server status, deploying, viewing logs.

### Build Automation
Commands for building, testing, and deploying your application.

## Tips

1. **Start simple**: Begin with example 01 and add features incrementally
2. **Use validation**: Let Click handle argument validation (example 03)
3. **Organize with groups**: Use groups for related commands (example 04)
4. **Share state with context**: Use context factory for shared config (example 05)
5. **Leverage REPL API**: Use `set_status()` and `set_info()` for rich feedback

## Common Patterns

### Yes/No Confirmation
```python
@repl.cli.command()
@click.confirmation_option(prompt="Are you sure?")
def dangerous():
    print("Executing dangerous operation...")
```

### File Path Arguments
```python
@repl.cli.command()
@click.argument("file", type=click.Path(exists=True))
def process(file):
    print(f"Processing {file}")
```

### Optional Arguments with Defaults
```python
@repl.cli.command()
@click.option("--count", default=1, help="Number of times to repeat")
@click.argument("message")
def repeat(count, message):
    for _ in range(count):
        print(message)
```

## Troubleshooting

### Command not found
Make sure you're using `/` prefix in REPL mode:
```
> /hello    # ✓ Correct
> hello     # ✗ Wrong (treated as free text)
```

### Validation errors
Check your Click decorators match the arguments you're passing:
```python
# This requires exactly 2 arguments:
@click.argument("x")
@click.argument("y")

# This accepts 0 or more:
@click.argument("args", nargs=-1)
```

### Module not found
The examples use `sys.path.insert()` to import cli_repl_kit. If you've installed cli-repl-kit via pip, you can remove those lines.

## Next Steps

- Read the main [README.md](../README.md) for full documentation
- Explore the [plugin system](../docs/plugins.md) for extensibility
- Check [configuration options](../docs/configuration.md) for customization
- See [validation guide](../docs/validation.md) for advanced validation
