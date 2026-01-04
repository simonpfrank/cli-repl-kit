# Reusable REPL Architecture Plan - cli-repl-kit

## Final Decisions

✅ **Plugin System**: Entry Points (pyproject.toml) for automatic command discovery
✅ **Agent Mode**: Framework feature (available to all projects)
✅ **Styling**: Customizable per project (with sensible defaults)
✅ **Package Name**: `cli-repl-kit`
✅ **File Naming**: `cli.py` for entry point, `repl_commands.py` for command plugins

> **Note**: Throughout this document, references to `repl-framework` should be read as `cli-repl-kit`, and `main.py` should be read as `cli.py`. These will be corrected during implementation.

## Implementation Summary

### Repository: cli-repl-kit
**GitHub**: `https://github.com/simonpfrank/cli-repl-kit`

**Structure**:
```
cli-repl-kit/
├── pyproject.toml
├── docs/
│   └── IMPLEMENTATION_PLAN.md    # This plan document
├── README.md                      # Beginner-friendly guide
├── src/
│   └── cli_repl_kit/
│       ├── __init__.py
│       ├── core/
│       │   ├── repl.py           # Core REPL engine
│       │   ├── completion.py     # Slash command completion
│       │   └── context.py        # Context management
│       ├── plugins/
│       │   └── base.py           # CommandPlugin base class
│       └── ui/
│           └── styles.py         # Rich styling (customizable)
└── tests/
```

### Using in Projects

**Minimal project structure**:
```
my-project/
├── pyproject.toml                 # Declare cli-repl-kit dependency + entry points
├── my_project/
│   ├── cli.py                     # Entry point (creates REPL instance)
│   ├── repl_commands.py           # Command plugins for REPL
│   └── commands/                  # (Optional) Command implementations
│       └── my_commands.py
└── README.md
```

**Key files**:

1. **`pyproject.toml`**:
```toml
[project]
dependencies = [
    "cli-repl-kit @ git+https://github.com/simonpfrank/cli-repl-kit.git@main",
]

[project.scripts]
my-cli = "my_project.cli:main"

[project.entry-points."repl.commands"]
my_commands = "my_project.repl_commands:MyCommandsPlugin"
```

2. **`my_project/cli.py`**:
```python
from cli_repl_kit import REPL

def main():
    repl = REPL(app_name="My Project")
    repl.start()
```

3. **`my_project/repl_commands.py`**:
```python
from cli_repl_kit.plugins.base import CommandPlugin
import click

class MyCommandsPlugin(CommandPlugin):
    name = "my_commands"

    def register(self, cli, context_factory):
        @click.command()
        def hello():
            """Say hello!"""
            print("Hello!")

        cli.add_command(hello, name="hello")
```

### Key Features

**Framework provides**:
- ✅ REPL loop with history (`~/.{app}/history`)
- ✅ Slash command completion (`/` prefix)
- ✅ Rich console output (customizable colors/themes)
- ✅ Dual-mode: Interactive REPL + CLI commands
- ✅ Plugin discovery via entry points
- ✅ Context injection for shared state
- ✅ Agent mode (free text input toggle) - framework feature

**Projects provide**:
- Commands (as Click commands/groups)
- Context factory (optional, for dependency injection)
- Custom styling (optional, overrides framework defaults)

### Implementation Tasks

**FIRST: Commit current simple-agent changes**
- Commit docs (Progress_Tracker.md, repl_framework_plan.md, etc.)
- Commit any code changes
- Push to GitHub

**THEN: Build cli-repl-kit using TDD**

1. Create `cli-repl-kit` repository structure
2. **TDD**: Write tests for plugin base class, then implement
3. **TDD**: Write tests for REPL core, then extract code from simple-agent
4. **TDD**: Write tests for completion, then extract from simple-agent
5. **TDD**: Write tests for styling, then extract from simple-agent
6. Write beginner-friendly README (clear for less-skilled Python devs)
7. Copy this plan to `cli-repl-kit/docs/IMPLEMENTATION_PLAN.md`
8. **TDD**: Refactor `simple-agent` to use framework (write tests first)
9. Test both REPL and CLI modes in simple-agent
10. Commit and push both repos

**TDD Approach**:
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Write failing tests first, then implement to pass

---

# Reusable REPL Architecture Plan

## Current Situation

The simple-agent project has a sophisticated Click-based REPL with:
- **491 lines** in `app.py` (main entry point)
- **17 command files** (4011 total lines) in `simple_agent/commands/`
- **Custom completion** via `SlashCommandCompleter` (188 lines)
- **Manual command registration** - all commands added in `app.py`
- **Context-based dependency injection** via Click's `ctx.obj`
- **Rich console** output with custom styling
- **No plugin system** - requires modifying `app.py` to add commands

## Requirements

1. **Separate Repository**: REPL maintained independently from projects
2. **Multi-Project Reuse**: Include REPL in different projects (including simple-agent)
3. **Easy Customization**: Different commands per project without modifying core REPL

---

## Suggested Architecture: Plugin-Based REPL Package

### Repository Management Strategy

**Recommended: PyPI Package + Git Repository**

#### Structure:
```
repl-framework/              # Separate git repo
├── pyproject.toml          # Package definition
├── src/
│   └── repl_framework/
│       ├── __init__.py
│       ├── core/
│       │   ├── repl.py         # Core REPL engine
│       │   ├── completion.py   # Completer base classes
│       │   └── context.py      # Context management
│       └── plugins/
│           └── base.py         # Plugin interface
└── tests/

simple-agent/               # Your project
├── pyproject.toml         # Lists repl-framework as dependency
├── simple_agent/
│   ├── commands/          # Project-specific commands
│   │   ├── agent_commands.py
│   │   ├── tool_commands.py
│   │   └── __init__.py
│   └── plugins.py         # Command registration
└── config.yaml
```

#### Installation Options:

**Option A: Published PyPI Package** (Best for stability)
```toml
# simple-agent/pyproject.toml
[project]
dependencies = [
    "repl-framework>=1.0.0",
]
```
- **Pros**: Version pinning, semantic versioning, easy updates
- **Cons**: Requires publishing to PyPI or private index

**Option B: Git Dependency** (Best for rapid development)
```toml
# simple-agent/pyproject.toml
[project]
dependencies = [
    "repl-framework @ git+https://github.com/you/repl-framework.git@main",
]
```
- **Pros**: Direct from GitHub, no publishing needed, can pin to commit/tag/branch
- **Cons**: Slower installs, requires git access

**Option C: Editable Local Install** (Best for simultaneous development)
```bash
# Clone both repos side-by-side
git clone https://github.com/you/repl-framework.git
git clone https://github.com/you/simple-agent.git

# Install repl-framework in editable mode
cd repl-framework && pip install -e .
cd ../simple-agent && pip install -e .
```
- **Pros**: Test REPL changes immediately across projects
- **Cons**: Manual setup, not portable

**Recommendation**: Start with Option C during development, transition to Option A for production.

---

### Command Customization Strategy

**Recommended: Entry Points Plugin System**

#### How It Works:

1. **Core REPL** (in `repl-framework`) discovers commands via Python entry points
2. **Projects** register commands in their `pyproject.toml`
3. **No code changes** needed to add/remove commands from projects

#### Implementation:

**Step 1: Define Plugin Interface** (`repl-framework/src/repl_framework/plugins/base.py`)
```python
from abc import ABC, abstractmethod
import click

class CommandPlugin(ABC):
    """Base class for REPL command plugins."""

    @abstractmethod
    def register(self, cli: click.Group, context_factory) -> None:
        """Register commands with the CLI group.

        Args:
            cli: Click group to register commands with
            context_factory: Function that returns context dict/object
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name for identification."""
        pass
```

**Step 2: Core REPL Auto-Discovery** (`repl-framework/src/repl_framework/core/repl.py`)
```python
from importlib.metadata import entry_points
import click
from typing import Callable, Dict, Any

class REPL:
    def __init__(self,
                 app_name: str,
                 context_factory: Callable[[], Dict[str, Any]],
                 plugin_group: str = "repl.commands"):
        self.app_name = app_name
        self.context_factory = context_factory
        self.plugin_group = plugin_group
        self.cli = click.Group()

        # Auto-discover and register plugins
        self._load_plugins()

    def _load_plugins(self):
        """Load all registered command plugins."""
        discovered = entry_points(group=self.plugin_group)

        for ep in discovered:
            plugin_class = ep.load()
            plugin = plugin_class()
            plugin.register(self.cli, self.context_factory)
            print(f"Loaded plugin: {plugin.name}")

    def start(self):
        """Start the REPL."""
        # Your existing start_repl() logic here
        pass
```

**Step 3: Project Registers Commands** (`simple-agent/pyproject.toml`)
```toml
[project.entry-points."repl.commands"]
system = "simple_agent.plugins:SystemCommandsPlugin"
agent = "simple_agent.plugins:AgentCommandsPlugin"
tool = "simple_agent.plugins:ToolCommandsPlugin"
llm = "simple_agent.plugins:LLMCommandsPlugin"
```

**Step 4: Project Implements Plugins** (`simple-agent/simple_agent/plugins.py`)
```python
from repl_framework.plugins.base import CommandPlugin
from .commands.system_commands import help_command, quit_command
from .commands.agent_commands import agent
from .commands.tool_commands import tool
from .commands.llm import llm_command

class SystemCommandsPlugin(CommandPlugin):
    name = "system"

    def register(self, cli, context_factory):
        cli.add_command(help_command, name="help")
        cli.add_command(quit_command, name="quit")
        # ... other system commands

class AgentCommandsPlugin(CommandPlugin):
    name = "agent"

    def register(self, cli, context_factory):
        cli.add_command(agent, name="agent")

class ToolCommandsPlugin(CommandPlugin):
    name = "tool"

    def register(self, cli, context_factory):
        cli.add_command(tool, name="tool")
```

**Step 5: Simple Project Entry Point** (`simple-agent/simple_agent/app.py`)
```python
from repl_framework import REPL
from .core.app_context import create_context

def main():
    # Context factory for dependency injection
    def context_factory():
        return create_context()  # Returns your current ctx.obj dict

    # Create REPL with auto-discovered commands
    repl = REPL(
        app_name="Simple Agent",
        context_factory=context_factory,
        plugin_group="repl.commands"
    )

    repl.start()

if __name__ == "__main__":
    main()
```

#### Benefits:

✅ **Zero core REPL changes** when adding/removing commands
✅ **Declaration in pyproject.toml** - clear command inventory
✅ **Per-project customization** - enable only needed commands
✅ **Third-party plugins** - others can extend your REPL
✅ **Version compatibility** - plugins can declare version requirements

---

## Alternative Approaches

### Alternative 1: Configuration-Based Loading

Instead of entry points, use YAML config:

```yaml
# simple-agent/config.yaml
repl:
  commands:
    - module: simple_agent.commands.system_commands
      commands: [help, quit, exit]
    - module: simple_agent.commands.agent_commands
      commands: [agent]
```

**Pros**: No entry points, runtime configuration
**Cons**: String-based imports (less type-safe), no version management

### Alternative 2: Git Submodule

Keep REPL as submodule in each project:

```bash
cd simple-agent
git submodule add https://github.com/you/repl-framework.git src/repl
```

**Pros**: Same codebase across projects, easy to update
**Cons**: Git complexity, not a true package, harder to version

### Alternative 3: Mono-repo with Workspace

Single repo with multiple projects:

```
workspace/
├── packages/
│   ├── repl-framework/
│   ├── simple-agent/
│   └── other-project/
└── pyproject.toml  # Workspace definition
```

**Pros**: Single repo, easy cross-project changes
**Cons**: Harder CI/CD, all projects bundled

---

## Recommended Approach

**Phase 1: Extract Core REPL**
1. Create `repl-framework` repository
2. Extract from `simple-agent`:
   - `app.py` → `repl_framework/core/repl.py` (core REPL logic)
   - `ui/completion.py` → `repl_framework/core/completion.py`
   - `ui/styles.py` → `repl_framework/ui/styles.py`
3. Add plugin interface (`repl_framework/plugins/base.py`)
4. Add entry point discovery to core REPL

**Phase 2: Refactor simple-agent**
1. Add `repl-framework` as dependency (editable install initially)
2. Create `simple_agent/plugins.py` with command plugins
3. Register plugins in `pyproject.toml` entry points
4. Simplify `app.py` to just call `REPL().start()`

**Phase 3: Test & Polish**
1. Test REPL in simple-agent
2. Create sample "hello-world" project using the REPL
3. Document plugin creation guide

**Phase 4: Publish (Optional)**
1. Add versioning to `repl-framework`
2. Publish to PyPI or private index
3. Update projects to use published version

---

## Files to Create/Modify

### New Repository: `repl-framework`
- `src/repl_framework/core/repl.py` - Core REPL engine with plugin discovery
- `src/repl_framework/core/completion.py` - Moved from simple-agent
- `src/repl_framework/core/context.py` - Context management utilities
- `src/repl_framework/plugins/base.py` - Plugin base class
- `src/repl_framework/ui/styles.py` - Moved from simple-agent
- `pyproject.toml` - Package definition
- `README.md` - Usage documentation

### Modified: `simple-agent`
- `simple_agent/plugins.py` - NEW: Plugin implementations
- `simple_agent/app.py` - SIMPLIFIED: Just calls REPL().start()
- `pyproject.toml` - Add repl-framework dependency + entry points
- `simple_agent/ui/completion.py` - REMOVED (moved to framework)
- `simple_agent/ui/styles.py` - REMOVED (moved to framework)

---

## Example: Adding Commands to New Project

```python
# my-new-project/my_project/plugins.py
from repl_framework.plugins.base import CommandPlugin
import click

class MyCommandsPlugin(CommandPlugin):
    name = "my_commands"

    def register(self, cli, context_factory):
        @click.command()
        def hello():
            """Say hello!"""
            print("Hello from my project!")

        cli.add_command(hello, name="hello")

# my-new-project/pyproject.toml
[project]
dependencies = ["repl-framework>=1.0.0"]

[project.entry-points."repl.commands"]
my_commands = "my_project.plugins:MyCommandsPlugin"

# my-new-project/my_project/main.py
from repl_framework import REPL

def main():
    repl = REPL(app_name="My Project", context_factory=dict)
    repl.start()
```

**Result**: Instant REPL with `/hello` command, no REPL code to maintain!

---

## User Requirements (Clarified)

Based on your feedback:

### Repository Management
**Preference**: Git dependency with bidirectional updates
- Start new projects by cloning/referencing the REPL repo
- Push improvements back to the REPL repo from any project
- **Recommendation**: Git dependency + fork workflow

### Plugin System
**Preference**: Between Entry Points and Config YAML (needs clarification)
- See detailed comparison below

### Use Cases
- **Primary**: Reuse across multiple projects
- **Secondary**: Learning/experimentation with plugin architectures

### Essential Features to Preserve
✅ Slash command completion (`/` prefix, Claude Code style)
✅ Rich console output (colors, tables, formatting)
✅ Context injection (shared state via Click context)
✅ Agent mode with optional free text input
✅ **CRITICAL**: Dual-mode support (REPL + CLI)

### New Requirement: Dual-Mode Support

**REPL Mode** (Interactive):
```bash
$ simple-agent
Welcome to Simple Agent!
> /agent create myagent --provider openai
> /agent run myagent "analyze this data"
```

**CLI Mode** (Traditional command-line):
```bash
$ simple-agent agent create myagent --provider openai
$ simple-agent agent run myagent "analyze this data"
```

**Good News**: Your current Click-based architecture already supports this! Click commands work in both modes automatically. The REPL is just an interactive wrapper around the same CLI commands. We must preserve this in the framework.

---

## Plugin System Comparison: Entry Points vs Config YAML

### Option 1: Entry Points (pyproject.toml)

**How it works**:
```toml
# Project's pyproject.toml
[project.entry-points."repl.commands"]
agent = "simple_agent.plugins:AgentCommandsPlugin"
tool = "simple_agent.plugins:ToolCommandsPlugin"
```

**Pros**:
- ✅ **Standard Python packaging** - uses established Python entry points mechanism
- ✅ **Automatic discovery** - REPL finds plugins without configuration
- ✅ **Type-safe** - imports actual Python classes, not strings
- ✅ **Version management** - plugins can specify compatible REPL versions
- ✅ **Third-party support** - others can publish plugins as separate packages
- ✅ **No runtime parsing** - discovered at import time
- ✅ **IDE support** - autocomplete and navigation work

**Cons**:
- ⚠️ Requires understanding entry points concept (mild learning curve)
- ⚠️ Need to reinstall package after changing entry points: `pip install -e .`
- ⚠️ Slightly more setup (but only once)

**Example**: Adding new commands requires:
1. Create plugin class in code
2. Add entry point to pyproject.toml
3. Run `pip install -e .`
4. REPL auto-discovers on next run

### Option 2: Config YAML (config.yaml)

**How it works**:
```yaml
# Project's config.yaml
repl:
  commands:
    - module: simple_agent.commands.agent_commands
      commands: [agent]
    - module: simple_agent.commands.tool_commands
      commands: [tool]
```

**Pros**:
- ✅ **Simple to understand** - just list modules and commands
- ✅ **No reinstall needed** - edit YAML and restart REPL
- ✅ **Runtime configuration** - can enable/disable commands without code changes
- ✅ **Lower barrier** - no entry points concept to learn

**Cons**:
- ⚠️ **String-based imports** - typos only caught at runtime
- ⚠️ **No version management** - can't specify REPL version compatibility
- ⚠️ **No IDE support** - autocomplete/navigation don't work for strings
- ⚠️ **Brittle** - module refactoring breaks config
- ⚠️ **No third-party plugins** - can't publish plugins as separate packages
- ⚠️ **Runtime parsing overhead** - config parsed every startup

**Example**: Adding new commands requires:
1. Create command in code
2. Add to YAML config
3. Restart REPL

### Recommendation: Entry Points (Option 1)

**Why**: For your goals (reuse + learning), entry points are better:

1. **Learning value**: Entry points are a standard Python pattern used by many frameworks (pytest, Flask, etc.). Understanding them is valuable.

2. **Scalability**: As you add more projects, entry points make it clear which commands each project has. Just look at `pyproject.toml`.

3. **Maintainability**: Refactoring code won't break anything - imports are real Python references.

4. **Future-proofing**: If you want to share plugins between projects or with others, entry points enable this.

The "need to reinstall" con is minimal - during development, you have `pip install -e .` anyway, and entry points only change when adding new command modules (rare).

**Alternative**: You could support both! Entry points as primary, YAML as optional override. But this adds complexity.

---

## Repository Strategy: Git Dependency with Fork Workflow

### Setup

**Create REPL Repository**:
```bash
# Create new repo on GitHub
https://github.com/simonpfrank/repl-framework

# Initialize locally
git clone https://github.com/simonpfrank/repl-framework.git
cd repl-framework
# ... create package structure ...
git add .
git commit -m "Initial REPL framework"
git push origin main
```

**Use in Projects**:
```toml
# simple-agent/pyproject.toml
[project]
dependencies = [
    "repl-framework @ git+https://github.com/simonpfrank/repl-framework.git@main",
]
```

### Bidirectional Updates Workflow

**Scenario 1: Improve REPL from simple-agent**

```bash
# Clone REPL alongside project (first time only)
cd ~/Documents/dev/python
git clone https://github.com/simonpfrank/repl-framework.git

# Install REPL in editable mode
cd simple-agent
pip uninstall repl-framework  # Remove git version
pip install -e ../repl-framework  # Use local editable version

# Make improvements to REPL
cd ../repl-framework
# ... edit code ...

# Test in simple-agent
cd ../simple-agent
simple-agent  # Uses local editable REPL

# Push improvements to REPL repo
cd ../repl-framework
git add .
git commit -m "Improve completion algorithm"
git push origin main

# Switch back to git dependency (optional)
cd ../simple-agent
pip uninstall repl-framework
pip install "repl-framework @ git+https://github.com/simonpfrank/repl-framework.git@main"
```

**Scenario 2: Use improved REPL in other projects**

```bash
# In any project, just update dependency
cd my-other-project
pip install --upgrade "repl-framework @ git+https://github.com/simonpfrank/repl-framework.git@main"
```

### Benefits

✅ **Single source of truth** - One REPL repo, many projects use it
✅ **Easy updates** - `pip install --upgrade` pulls latest
✅ **Version pinning** - Can pin to specific commit/tag if needed
✅ **Bidirectional** - Develop in editable mode, push back to repo
✅ **No publishing overhead** - No PyPI needed

### Alternative: Git Submodules

If you prefer keeping REPL code inside each project:

```bash
# Add REPL as submodule
cd simple-agent
git submodule add https://github.com/simonpfrank/repl-framework.git src/repl

# Update from REPL repo
git submodule update --remote

# Push changes back to REPL repo
cd src/repl
git add .
git commit -m "Improvements"
git push origin main
```

**Pros**: REPL code visible in project, easier to see what version
**Cons**: Git submodule complexity, manual update steps, messier project structure

**Recommendation**: Stick with pip install from git - cleaner and more Pythonic.

---

## Recommended Implementation Plan

### Summary

**Repository Strategy**: Git dependency with editable local development
**Plugin System**: Entry points (pyproject.toml) for automatic command discovery
**Architecture**: Extract core REPL to separate repo, keep commands in projects

### Implementation Phases

#### Phase 1: Create REPL Framework Repository

**New repo**: `repl-framework`

**Files to create**:
1. `src/repl_framework/__init__.py` - Package init, export main classes
2. `src/repl_framework/core/repl.py` - Core REPL class with plugin discovery
3. `src/repl_framework/core/completion.py` - SlashCommandCompleter (from simple-agent)
4. `src/repl_framework/core/context.py` - Context management utilities
5. `src/repl_framework/plugins/base.py` - CommandPlugin base class
6. `src/repl_framework/ui/styles.py` - Rich styling (from simple-agent)
7. `pyproject.toml` - Package definition with dependencies
8. `README.md` - Documentation and examples

**Code to extract from simple-agent**:
- `simple_agent/app.py` lines 243-462 (`start_repl()` function) → `repl_framework/core/repl.py`
- `simple_agent/ui/completion.py` (entire file) → `repl_framework/core/completion.py`
- `simple_agent/ui/styles.py` (entire file) → `repl_framework/ui/styles.py`

**Dependencies** (in `repl_framework/pyproject.toml`):
```toml
dependencies = [
    "click>=8.0",
    "click-repl>=0.3",
    "prompt-toolkit>=3.0",
    "rich>=13.0",
]
```

**Key design principles**:
- Core REPL must NOT depend on simple-agent specifics
- Plugin discovery via entry points (standard Python pattern)
- Context factory pattern for dependency injection
- Support both REPL mode and CLI mode (Click's natural behavior)
- Preserve all essential features (slash completion, rich output, context injection, agent mode)

#### Phase 2: Implement Plugin System

**In `repl_framework/plugins/base.py`**:
```python
from abc import ABC, abstractmethod
import click
from typing import Callable, Dict, Any

class CommandPlugin(ABC):
    """Base class for REPL command plugins."""

    @abstractmethod
    def register(self, cli: click.Group, context_factory: Callable[[], Dict[str, Any]]) -> None:
        """Register commands with the CLI group."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name for identification."""
        pass
```

**In `repl_framework/core/repl.py`**:
- Add plugin discovery using `importlib.metadata.entry_points()`
- Load plugins from entry point group `repl.commands`
- Call `plugin.register(cli, context_factory)` for each discovered plugin
- Preserve dual-mode support (REPL interactive + CLI command-line)

**Critical**: The REPL class must:
1. Accept a Click group OR create one
2. Load plugins and register their commands
3. Support both `repl.start()` (interactive) and direct CLI invocation
4. Pass context factory to plugins for dependency injection

#### Phase 3: Refactor simple-agent to Use Framework

**Files to create**:
1. `simple_agent/plugins.py` - Plugin implementations for all command groups

**Files to modify**:
1. `simple_agent/app.py` - Simplify to use `REPL` class
2. `simple_agent/pyproject.toml` - Add repl-framework dependency + entry points

**Files to delete**:
1. `simple_agent/ui/completion.py` - Moved to framework
2. `simple_agent/ui/styles.py` - Moved to framework

**New `simple_agent/plugins.py`** (example structure):
```python
from repl_framework.plugins.base import CommandPlugin
from .commands.system_commands import help_command, quit_command, exit_command, refresh
from .commands.config_commands import config
from .commands.agent_commands import agent
from .commands.tool_commands import tool
# ... import all command groups

class SystemCommandsPlugin(CommandPlugin):
    name = "system"

    def register(self, cli, context_factory):
        cli.add_command(help_command, name="help")
        cli.add_command(quit_command, name="quit")
        cli.add_command(exit_command, name="exit")
        cli.add_command(refresh, name="refresh")

class ConfigCommandsPlugin(CommandPlugin):
    name = "config"

    def register(self, cli, context_factory):
        cli.add_command(config, name="config")

class AgentCommandsPlugin(CommandPlugin):
    name = "agent"

    def register(self, cli, context_factory):
        cli.add_command(agent, name="agent")

# ... similar for all 17 command groups
```

**Updated `simple_agent/pyproject.toml`**:
```toml
[project]
name = "simple-agent"
dependencies = [
    "repl-framework @ git+https://github.com/simonpfrank/repl-framework.git@main",
    # ... other dependencies
]

[project.entry-points."repl.commands"]
system = "simple_agent.plugins:SystemCommandsPlugin"
config = "simple_agent.plugins:ConfigCommandsPlugin"
agent = "simple_agent.plugins:AgentCommandsPlugin"
tool = "simple_agent.plugins:ToolCommandsPlugin"
collection = "simple_agent.plugins:CollectionCommandsPlugin"
flow = "simple_agent.plugins:FlowCommandsPlugin"
embed = "simple_agent.plugins:EmbedCommandsPlugin"
process = "simple_agent.plugins:ProcessCommandsPlugin"
llm = "simple_agent.plugins:LLMCommandsPlugin"
# ... all 17+ command groups
```

**Simplified `simple_agent/app.py`**:
```python
import click
from repl_framework import REPL
from .core.app_context import create_context  # Your existing context factory

@click.group()
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging")
@click.option("--config-file", "-c", default=None, help="Config file path")
@click.pass_context
def cli(ctx, debug, config_file):
    """Simple Agent CLI/REPL"""
    ctx.obj = create_context(debug=debug, config_file=config_file)

def main():
    # Create REPL with plugin auto-discovery
    repl = REPL(
        cli_group=cli,  # Pass existing Click group
        app_name="Simple Agent",
        plugin_group="repl.commands",  # Where to find plugins
    )

    # Start in appropriate mode
    repl.start()  # Detects if CLI args provided or should enter REPL

if __name__ == "__main__":
    main()
```

**Key changes**:
- `app.py` reduces from ~491 lines to ~30 lines
- All REPL logic moved to framework
- Commands still in `simple_agent/commands/` (no changes)
- Plugin registration in `plugins.py` + `pyproject.toml`

#### Phase 4: Test and Validate

**Test checklist**:
1. ✅ REPL mode works: `simple-agent` enters interactive mode
2. ✅ CLI mode works: `simple-agent agent list` runs command directly
3. ✅ Slash completion works in REPL: `/agent<TAB>` shows completions
4. ✅ Rich output preserved: Tables, colors, formatting still work
5. ✅ Context injection works: Commands receive `ctx.obj` with managers
6. ✅ Agent mode works: Free text input when in agent chat mode
7. ✅ All 17+ command groups load correctly
8. ✅ Config loading preserved: YAML config still read on startup
9. ✅ History preserved: `~/.simple-agent/history` still works
10. ✅ Error handling preserved: User-friendly error messages

**Integration test**:
```bash
# Test REPL mode
$ simple-agent
Welcome to Simple Agent!
> /agent create test --provider openai
✓ Agent 'test' created
> /agent list
┌──────┬──────────┐
│ Name │ Provider │
├──────┼──────────┤
│ test │ openai   │
└──────┴──────────┘
> /quit

# Test CLI mode
$ simple-agent agent list
┌──────┬──────────┐
│ Name │ Provider │
├──────┼──────────┤
│ test │ openai   │
└──────┴──────────┘
```

#### Phase 5: Documentation

**In `repl-framework/README.md`**:
- Installation instructions
- Quick start example
- Plugin creation guide
- API reference
- Contributing guidelines

**In `simple-agent/README.md`**:
- Update to mention REPL framework
- Remove detailed REPL implementation notes

### Critical Files Summary

**New Repository: `repl-framework`**

| File | Purpose | Lines (est.) |
|------|---------|--------------|
| `src/repl_framework/core/repl.py` | Core REPL engine with plugin discovery | ~250 |
| `src/repl_framework/core/completion.py` | SlashCommandCompleter (from simple-agent) | ~188 |
| `src/repl_framework/core/context.py` | Context management utilities | ~50 |
| `src/repl_framework/plugins/base.py` | Plugin base class | ~30 |
| `src/repl_framework/ui/styles.py` | Rich styling (from simple-agent) | ~50 |
| `pyproject.toml` | Package definition | ~30 |
| `README.md` | Documentation | ~200 |

**Modified in `simple-agent`**

| File | Change | Lines (before → after) |
|------|--------|------------------------|
| `simple_agent/app.py` | Simplified to use REPL class | 491 → ~30 |
| `simple_agent/pyproject.toml` | Add repl-framework dep + entry points | +20 lines |
| `simple_agent/plugins.py` | NEW: Plugin implementations | +200 |
| `simple_agent/ui/completion.py` | DELETED (moved to framework) | -188 |
| `simple_agent/ui/styles.py` | DELETED (moved to framework) | -50 |
| `simple_agent/commands/*.py` | NO CHANGES | 0 |

**Net change in simple-agent**: ~470 lines removed, ~220 lines added = **250 lines saved**

### Development Workflow

**Initial setup** (one time):
```bash
# Create REPL framework repo
cd ~/Documents/dev/python
git clone https://github.com/simonpfrank/repl-framework.git
cd repl-framework
# ... implement framework ...
git push origin main

# Use in simple-agent (editable mode for development)
cd ../simple-agent
pip install -e ../repl-framework
pip install -e .
```

**Daily workflow**:
```bash
# Work on simple-agent, using local REPL
cd ~/Documents/dev/python/simple-agent
simple-agent  # Uses local editable repl-framework

# If you improve REPL:
cd ../repl-framework
# ... make changes ...
git commit -m "Improve X"
git push origin main

# If you want to update other projects:
cd ../other-project
pip install --upgrade --force-reinstall repl-framework
```

**Starting new projects**:
```bash
# New project
cd ~/Documents/dev/python
mkdir my-new-cli && cd my-new-cli

# Add REPL framework
cat > pyproject.toml <<EOF
[project]
name = "my-new-cli"
dependencies = [
    "repl-framework @ git+https://github.com/simonpfrank/repl-framework.git@main",
]

[project.entry-points."repl.commands"]
my_commands = "my_new_cli.plugins:MyCommandsPlugin"
EOF

# Implement minimal plugin
mkdir -p my_new_cli
cat > my_new_cli/plugins.py <<EOF
from repl_framework.plugins.base import CommandPlugin
import click

class MyCommandsPlugin(CommandPlugin):
    name = "my_commands"

    def register(self, cli, context_factory):
        @click.command()
        def hello():
            """Say hello!"""
            print("Hello from my CLI!")

        cli.add_command(hello, name="hello")
EOF

# Install and run
pip install -e .
my-new-cli
> /hello
Hello from my CLI!
```

---

## Answers to User Questions

### Question 1: What does a new project need? What's the folder structure?

**Minimal structure for a new project using the REPL framework**:

```
my-new-project/
├── pyproject.toml                  # Package definition + REPL dependency + entry points
├── my_new_project/                 # Your package directory
│   ├── __init__.py                 # Package init
│   ├── main.py                     # Main entry point (creates REPL instance)
│   ├── repl_commands.py            # REPL command plugin definitions
│   └── commands/                   # (Optional) Separate command modules
│       ├── __init__.py
│       ├── my_commands.py
│       └── other_commands.py
└── README.md
```

**What each file contains**:

**`pyproject.toml`** - Declares dependency and registers plugins:
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-new-project"
version = "0.1.0"
dependencies = [
    "repl-framework @ git+https://github.com/simonpfrank/repl-framework.git@main",
]

[project.scripts]
my-cli = "my_new_project.main:main"

[project.entry-points."repl.commands"]
my_commands = "my_new_project.repl_commands:MyCommandsPlugin"
```

**`my_new_project/main.py`** - Creates and starts the REPL:
```python
from repl_framework import REPL

def main():
    """Entry point for the CLI/REPL."""
    # Simple context factory (can be more complex if needed)
    def context_factory():
        return {
            "app_name": "My Project",
            "config": {},  # Your config here
        }

    # Create REPL with auto-discovered commands
    repl = REPL(
        app_name="My Project",
        context_factory=context_factory,
        plugin_group="repl.commands",
    )

    # Start in appropriate mode (REPL or CLI)
    repl.start()

if __name__ == "__main__":
    main()
```

**`my_new_project/repl_commands.py`** - Plugin definitions:
```python
from repl_framework.plugins.base import CommandPlugin
import click

class MyCommandsPlugin(CommandPlugin):
    """My project's commands for the REPL."""

    name = "my_commands"

    def register(self, cli, context_factory):
        """Register commands with the REPL."""

        @click.command()
        @click.argument("name")
        def greet(name):
            """Greet someone."""
            print(f"Hello, {name}!")

        @click.command()
        def status():
            """Show project status."""
            print("Everything is working!")

        cli.add_command(greet, name="greet")
        cli.add_command(status, name="status")
```

**Result**: After `pip install -e .`, you can run:
- REPL mode: `my-cli` then `/greet Alice`
- CLI mode: `my-cli greet Alice`

**That's it!** Only 3 files needed: `pyproject.toml`, `main.py`, and `repl_commands.py`

---

### Question 2: Will each project require its own command line handling?

**Short answer**: No! The REPL framework handles all command-line interaction for you.

**What the framework provides**:
- ✅ Command parsing (via Click)
- ✅ REPL loop (via click-repl)
- ✅ Tab completion (slash-based)
- ✅ History management
- ✅ Help system
- ✅ Dual-mode support (REPL + CLI)

**What your project provides**:
- Just the **commands** (as Click commands/groups)
- Just the **context factory** (returns dict/object for dependency injection)

**Example - No custom CLI handling needed**:

```python
# my_new_project/main.py - COMPLETE FILE
from repl_framework import REPL

def main():
    repl = REPL(
        app_name="My Project",
        context_factory=dict,  # Simple dict context
    )
    repl.start()  # Framework handles everything!
```

**However**, you **can** add custom CLI handling if needed:

```python
# my_new_project/main.py - WITH custom CLI options
import click
from repl_framework import REPL

@click.group()
@click.option("--config", "-c", default="config.yaml", help="Config file")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, config, verbose):
    """My Project CLI/REPL."""
    ctx.obj = {
        "config_file": config,
        "verbose": verbose,
    }

def main():
    repl = REPL(
        cli_group=cli,  # Pass your Click group
        app_name="My Project",
    )
    repl.start()
```

**When to add custom CLI handling**:
- ✅ Global CLI options (like `--config`, `--debug`)
- ✅ Pre-REPL setup (load config, initialize database)
- ✅ Complex context creation

**When NOT to add it**:
- ❌ Just to have a REPL with commands
- ❌ Simple projects without global options

---

### Question 3: Interface naming - `main.py` vs `repl_commands.py`?

**Great observation!** You're right that naming matters for clarity.

**Current plan has TWO interfaces between framework and project**:

1. **`main.py`** - Main entry point that **creates the REPL instance**
2. **`repl_commands.py`** (was `plugins.py`) - Plugin classes that **register commands with REPL**

**Your concern**: The name `plugins.py` suggests "project has plugins", but really it's "commands for the REPL".

**Better naming options**:

| File name | Meaning | Pros | Cons |
|-----------|---------|------|------|
| `plugins.py` | Generic plugins | Used in examples, familiar term | Ambiguous - plugins for what? |
| `repl_commands.py` | Commands for REPL | Clear purpose, explicit | Slightly longer |
| `repl_plugins.py` | Plugins for REPL | Explicit + keeps "plugin" term | Still uses "plugin" |
| `commands.py` | Commands module | Short, clear | Conflicts with `commands/` folder |
| `cli_commands.py` | CLI commands | Clear for both REPL/CLI | "CLI" less accurate for REPL mode |

**Recommendation: `repl_commands.py`**

**Why**:
- ✅ Clear that these are "commands for the REPL"
- ✅ Doesn't conflict with existing `commands/` folder
- ✅ Accurately describes the file's purpose
- ✅ Distinguishes from project's own plugin system (if any)

**Updated structure**:

```
simple-agent/
├── simple_agent/
│   ├── main.py                 # Creates REPL instance, main entry point
│   ├── repl_commands.py        # Command plugins for REPL framework
│   ├── commands/               # Individual command implementations
│   │   ├── agent_commands.py
│   │   ├── tool_commands.py
│   │   └── ...
│   └── core/
│       └── app_context.py      # Context factory
```

**Updated `pyproject.toml`**:
```toml
[project.entry-points."repl.commands"]
system = "simple_agent.repl_commands:SystemCommandsPlugin"
agent = "simple_agent.repl_commands:AgentCommandsPlugin"
tool = "simple_agent.repl_commands:ToolCommandsPlugin"
# ... etc
```

**Summary of interfaces**:

| File | Role | Responsibility |
|------|------|----------------|
| `main.py` | **Main entry point** | Creates REPL instance, defines context factory, starts REPL |
| `repl_commands.py` | **Command registration** | Defines plugin classes that register Click commands with REPL |
| `commands/*.py` | **Command implementation** | Individual Click command/group definitions (unchanged) |
| `pyproject.toml` | **Entry point declaration** | Tells REPL framework which plugins to load |

**The interface is both**:
- `main.py` creates the REPL (one-time setup)
- `repl_commands.py` provides commands to the REPL (auto-discovered via entry points)

---

## Updated Implementation Plan

With clarified naming and structure, here's the updated plan:

### Phase 3 (Updated): Refactor simple-agent to Use Framework

**Files to create**:
1. `simple_agent/repl_commands.py` - Command plugin implementations (~200 lines)
2. `simple_agent/main.py` - New main entry point that creates REPL instance (~30 lines)

**Files to modify**:
1. `simple_agent/pyproject.toml` - Add repl-framework dependency + entry points, update scripts entry point (+20 lines)

**Files to delete/remove**:
1. `simple_agent/app.py` - Old CLI implementation, replaced by main.py (-491 lines)
2. `simple_agent/ui/completion.py` - Moved to framework (-188 lines)
3. `simple_agent/ui/styles.py` - Moved to framework (-50 lines)

**New `simple_agent/repl_commands.py`**:
```python
"""Command plugins for the REPL framework."""
from repl_framework.plugins.base import CommandPlugin
from .commands.system_commands import help_command, quit_command, exit_command, refresh
from .commands.config_commands import config
from .commands.agent_commands import agent
from .commands.tool_commands import tool
# ... import all command groups

class SystemCommandsPlugin(CommandPlugin):
    """System commands (help, quit, exit, refresh)."""
    name = "system"

    def register(self, cli, context_factory):
        cli.add_command(help_command, name="help")
        cli.add_command(quit_command, name="quit")
        cli.add_command(exit_command, name="exit")
        cli.add_command(refresh, name="refresh")

class ConfigCommandsPlugin(CommandPlugin):
    """Configuration management commands."""
    name = "config"

    def register(self, cli, context_factory):
        cli.add_command(config, name="config")

class AgentCommandsPlugin(CommandPlugin):
    """Agent management commands."""
    name = "agent"

    def register(self, cli, context_factory):
        cli.add_command(agent, name="agent")

# ... similar for all 17 command groups
```

**Updated `simple_agent/pyproject.toml`**:
```toml
[project]
name = "simple-agent"
dependencies = [
    "repl-framework @ git+https://github.com/simonpfrank/repl-framework.git@main",
    # ... other dependencies
]

[project.entry-points."repl.commands"]
system = "simple_agent.repl_commands:SystemCommandsPlugin"
config = "simple_agent.repl_commands:ConfigCommandsPlugin"
agent = "simple_agent.repl_commands:AgentCommandsPlugin"
tool = "simple_agent.repl_commands:ToolCommandsPlugin"
collection = "simple_agent.repl_commands:CollectionCommandsPlugin"
flow = "simple_agent.repl_commands:FlowCommandsPlugin"
embed = "simple_agent.repl_commands:EmbedCommandsPlugin"
process = "simple_agent.repl_commands:ProcessCommandsPlugin"
llm = "simple_agent.repl_commands:LLMCommandsPlugin"
# ... all 17+ command groups
```

**New `simple_agent/main.py`**:
```python
"""Main entry point for Simple Agent CLI/REPL."""
import click
from repl_framework import REPL
from .core.app_context import create_context

@click.group()
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging")
@click.option("--config-file", "-c", default=None, help="Config file path")
@click.pass_context
def cli(ctx, debug, config_file):
    """Simple Agent CLI/REPL."""
    ctx.obj = create_context(debug=debug, config_file=config_file)

def main():
    """Start the Simple Agent REPL or execute CLI command."""
    repl = REPL(
        cli_group=cli,
        app_name="Simple Agent",
        plugin_group="repl.commands",
    )
    repl.start()

if __name__ == "__main__":
    main()
```

**Updated `simple_agent/pyproject.toml`** (scripts section):
```toml
[project.scripts]
simple-agent = "simple_agent.main:main"  # Changed from app:main
```

---

### Questions Before Implementation

Before we proceed with implementation, please confirm:

1. **Entry Points**: Are you comfortable with the entry points approach after seeing the pros/cons? Or would you prefer starting with Config YAML for simplicity?

2. **Agent Mode**: How should agent mode (free text input) be handled? Should this be a framework feature or simple-agent specific?

3. **Styling**: Should the Rich theme/styles be customizable per project, or shared from framework?

4. **Package name**: Is `repl-framework` a good name, or would you prefer something else (e.g., `click-repl-framework`, `cli-repl-kit`, `interactive-cli`)?

5. **File naming**: Do you prefer `repl_commands.py` over `plugins.py` for the command registration file?

---
