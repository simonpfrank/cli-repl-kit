# cli-repl-kit Architecture

**Created:** 2026-01-07
**Status:** Proposed - Awaiting Approval
**Target:** Refactor 1,576-line monolith into 6 maintainable modules

---

## Table of Contents
1. [Current Architecture (Monolith)](#current-architecture-monolith)
2. [Target Architecture (Modular)](#target-architecture-modular)
3. [Module Breakdown](#module-breakdown)
4. [Class Diagrams](#class-diagrams)
5. [Data Flow](#data-flow)
6. [Plugin Lifecycle](#plugin-lifecycle)
7. [Migration Strategy](#migration-strategy)

---

## Current Architecture (Monolith)

### File Structure (As-Is)
```
cli_repl_kit/
├── core/
│   ├── __init__.py
│   ├── repl.py                    # 🔴 1,576 lines - MONOLITH
│   ├── config.py                  # 200 lines ✅
│   ├── completion.py              # 150 lines ✅
│   └── validation.py              # 100 lines ✅
├── plugins/
│   ├── __init__.py
│   ├── base.py                    # 95 lines ✅
│   └── validation.py              # 50 lines ✅
└── __init__.py
```

### Problems with Current `repl.py`

**Violations:**
- ❌ 1,576 lines (3.2x over 500-line limit)
- ❌ `_start_repl()` method: ~1,100 lines (22x over 50-line limit)
- ❌ 20+ nested closures in one method
- ❌ Mutable dict for state management
- ❌ Single Responsibility violated: 15 different responsibilities

**Responsibilities crammed into `repl.py`:**
1. Plugin discovery and loading
2. Validation rule extraction
3. Command validation
4. CLI mode execution
5. REPL mode execution
6. Output buffer management
7. stdout/stderr capture
8. UI layout construction
9. Key binding setup
10. Completion handling
11. History management
12. Config loading
13. ASCII art rendering
14. Status line management
15. Info line management

---

## Target Architecture (Modular)

### File Structure (To-Be)

```
cli_repl_kit/
├── core/
│   ├── __init__.py
│   ├── repl.py                    # 300 lines - Orchestration only
│   ├── state.py                   # 150 lines - State management (NEW)
│   ├── layout.py                  # 400 lines - UI layout (NEW)
│   ├── output_capture.py          # 150 lines - Output handling (NEW)
│   ├── key_bindings.py            # 400 lines - Keyboard handlers (NEW)
│   ├── formatting.py              # 200 lines - ANSI formatting (NEW)
│   ├── config.py                  # 200 lines - Config (existing)
│   ├── completion.py              # 150 lines - Completion (existing)
│   └── validation.py              # 100 lines - Validation (existing)
├── plugins/
│   ├── __init__.py
│   ├── base.py                    # 95 lines - Plugin base (existing)
│   └── validation.py              # 50 lines - Validation rules (existing)
└── __init__.py
```

### Size Constraints Met

| Module | Current | Target | Status |
|--------|---------|--------|--------|
| repl.py | 1,576 | 300 | 🔴 Needs refactoring |
| state.py | 0 | 150 | ⚪ New module |
| layout.py | 0 | 400 | ⚪ New module |
| output_capture.py | 0 | 150 | ⚪ New module |
| key_bindings.py | 0 | 400 | ⚪ New module |
| formatting.py | 0 | 200 | ⚪ New module |

**All modules ≤ 500 lines ✅**

---

## Module Breakdown

### 1. `repl.py` - Core Orchestration (300 lines)

**Responsibility:** Coordinate components, not implement them

**Public API:**
```python
class REPL:
    """Main REPL orchestrator."""

    def __init__(
        self,
        app_name: str,
        context_factory: Optional[Callable] = None,
        cli_group: Optional[click.Group] = None,
        plugin_group: str = "repl.commands",
        config_path: Optional[str] = None
    ):
        """Initialize REPL with config and plugins."""

    def start(self, prompt_text: str = "> ", enable_agent_mode: bool = False) -> None:
        """Start REPL or execute CLI command."""

    def _load_plugins(self) -> None:
        """Discover and load plugins from entry points."""

    def _extract_validation_rule(self, cmd: click.Command, cmd_path: str) -> ValidationRule:
        """Extract validation rule from Click command."""

    def _start_repl(self, prompt_text: str, enable_agent_mode: bool) -> None:
        """Start interactive REPL session (orchestrates components)."""
```

**Responsibilities:**
- Plugin discovery (entry points)
- Validation rule extraction
- CLI vs REPL mode switching
- Component orchestration (delegates to other modules)

**Does NOT:**
- Build layouts (LayoutBuilder does this)
- Handle keyboard events (KeyBindingManager does this)
- Manage state (REPLState does this)
- Capture output (OutputCapture does this)

---

### 2. `state.py` - State Management (150 lines)

**Responsibility:** Typed, documented state object to replace mutable dict

**Public API:**
```python
@dataclass
class REPLState:
    """Tracks the state of a REPL session.

    Replaces mutable dict pattern with typed, testable state.
    """
    completions: List[str] = field(default_factory=list)
    selected_idx: int = 0
    placeholder_active: bool = False
    placeholder_start: int = 0
    status_text: List[FormattedText] = field(default_factory=list)
    info_text: List[FormattedText] = field(default_factory=list)
    slash_command_active: bool = False
    is_multiline: bool = False
    menu_keep_visible: bool = False

    def reset_completions(self) -> None:
        """Clear completion state."""

    def set_status(self, text: List[FormattedText]) -> None:
        """Set status line content."""

    def clear_status(self) -> None:
        """Clear status line."""

    def set_info(self, text: List[FormattedText]) -> None:
        """Set info line content."""

    def clear_info(self) -> None:
        """Clear info line."""
```

**Benefits:**
- Type hints for IDE support
- Clear documentation
- Testable independently
- No side effects from closure mutations

---

### 3. `formatting.py` - ANSI Formatting (200 lines)

**Responsibility:** Convert between FormattedText and ANSI strings

**Public API:**
```python
def formatted_text_to_ansi_string(
    formatted_text: List[Tuple[str, str]],
    config: Config
) -> str:
    """Convert FormattedText to ANSI escape codes.

    Args:
        formatted_text: List of (style, text) tuples
        config: Config object with ansi_colors

    Returns:
        String with ANSI escape codes embedded
    """

class ANSILexer(Lexer):
    """Lexer that interprets ANSI escape codes.

    Converts ANSI-escaped text into FormattedText for
    prompt_toolkit rendering.
    """

    def lex_document(self, document: Document) -> Callable:
        """Return function that returns styled fragments for a line."""
```

**Extracted from:**
- Lines 28-68 of current repl.py
- Lines 71-100 of current repl.py

---

### 4. `output_capture.py` - Output Handling (150 lines)

**Responsibility:** Capture stdout/stderr and redirect to output buffer

**Public API:**
```python
class OutputCapture(io.StringIO):
    """Capture stdout/stderr and redirect to output buffer.

    Intercepts writes and sends them to REPL output with styling.
    """

    def __init__(
        self,
        stream_type: str,
        output_callback: Callable[[List[Tuple[str, str]]], None],
        config: Config
    ):
        """Initialize capture.

        Args:
            stream_type: "stdout" or "stderr"
            output_callback: Function to call with FormattedText
            config: Config for styling

        Raises:
            ValueError: If stream_type not "stdout" or "stderr"
        """

    def write(self, text: str) -> int:
        """Capture text and send to output.

        Returns:
            Number of bytes written
        """

    def flush(self) -> None:
        """Flush buffer."""

class OutputManager:
    """Manages output buffer and appending text."""

    def __init__(self, output_buffer: Buffer, config: Config):
        """Initialize output manager."""

    def append_line(self, line: Union[str, List[Tuple[str, str]]]) -> None:
        """Add a line to output buffer with auto-scroll."""

    def clear(self) -> None:
        """Clear output buffer."""
```

**Extracted from:**
- Lines 103-138 of current repl.py (OutputCapture)
- Lines 657-679 of current repl.py (append_to_output_buffer logic)

---

### 5. `layout.py` - UI Layout Construction (400 lines)

**Responsibility:** Build prompt_toolkit Layout with all windows

**Public API:**
```python
class LayoutBuilder:
    """Builds prompt_toolkit Layout for REPL.

    Separates layout construction from REPL orchestration.
    Makes UI components testable and reusable.
    """

    def __init__(self, config: Config, state: REPLState):
        """Initialize layout builder."""

    def build(
        self,
        input_buffer: Buffer,
        output_buffer: Buffer,
        completer: Completer,
        history: FileHistory
    ) -> Layout:
        """Build complete REPL layout.

        Returns:
            Layout with output, status, input, info, menu windows
        """

    def _create_output_window(self, buffer: Buffer) -> Window:
        """Create output display window with ANSI support."""

    def _create_status_window(self) -> Window:
        """Create status line window."""

    def _create_input_window(
        self,
        buffer: Buffer,
        completer: Completer,
        history: FileHistory
    ) -> Window:
        """Create input window with completion and history."""

    def _create_info_window(self) -> Window:
        """Create info line window."""

    def _create_menu_window(self) -> Window:
        """Create completion menu window."""

    def _create_divider(self) -> Window:
        """Create horizontal divider line."""

    def _create_welcome_banner(self, app_name: str) -> str:
        """Create intro banner with ASCII art."""
```

**Extracted from:**
- Lines 500-606 of current repl.py (intro banner)
- Lines 634-638 of current repl.py (create_divider_window)
- Lines 916-1020 of current repl.py (window creation)
- Lines 1021-1032 of current repl.py (Layout assembly)

---

### 6. `key_bindings.py` - Keyboard Event Handling (400 lines)

**Responsibility:** Manage all keyboard bindings and event handlers

**Public API:**
```python
class KeyBindingManager:
    """Manages keyboard bindings for REPL.

    Extracts key binding logic from massive _start_repl method.
    Each binding is a focused, testable method.
    """

    def __init__(
        self,
        config: Config,
        state: REPLState,
        input_buffer: Buffer,
        output_buffer: Buffer,
        output_manager: OutputManager,
        cli: click.Group,
        completer: Completer
    ):
        """Initialize key binding manager with dependencies."""

    def create_bindings(self) -> KeyBindings:
        """Create all key bindings.

        Returns:
            KeyBindings object with all handlers registered
        """

    def _register_navigation_keys(self, kb: KeyBindings) -> None:
        """Register arrow keys, page up/down."""

    def _register_editing_keys(self, kb: KeyBindings) -> None:
        """Register backspace, delete, etc."""

    def _register_completion_keys(self, kb: KeyBindings) -> None:
        """Register tab, escape for completion."""

    def _register_submit_keys(self, kb: KeyBindings) -> None:
        """Register enter, ctrl+j for submission."""

    def _handle_arrow_up(self, event) -> None:
        """Handle up arrow: navigate menu or history."""

    def _handle_arrow_down(self, event) -> None:
        """Handle down arrow: navigate menu or move cursor."""

    def _handle_tab(self, event) -> None:
        """Handle tab: trigger or navigate completion."""

    def _handle_enter(self, event) -> None:
        """Handle enter: execute command or select completion."""

    def _handle_ctrl_j(self, event) -> None:
        """Handle ctrl+j: insert newline for multiline."""

    def _execute_command(self, command_text: str) -> None:
        """Execute a command and handle output/errors."""
```

**Extracted from:**
- Lines 1033-1398 of current repl.py (key bindings setup)
- Lines 680-850 of current repl.py (on_text_changed handler logic)
- Lines 900-1400 of current repl.py (accept_handler logic)

---

## Class Diagrams

### Current Architecture (Monolith)

```
┌─────────────────────────────────────────────────────────────┐
│                          REPL                               │
│                     (1,576 lines)                           │
├─────────────────────────────────────────────────────────────┤
│ - app_name: str                                             │
│ - context_factory: Callable                                 │
│ - cli: click.Group                                          │
│ - config: Config                                            │
│ - plugins: List[CommandPlugin]                              │
│ - validation_rules: Dict[str, ValidationRule]               │
├─────────────────────────────────────────────────────────────┤
│ + __init__(...)                                             │
│ + start(prompt_text, enable_agent_mode)                     │
│ + _load_plugins()                                           │
│ + _extract_validation_rule(cmd, path)                       │
│ + _validate_command(cmd_name, args)                         │
│ + _start_repl(prompt_text, enable_agent_mode) [1,100 lines]│
│   ├─ [nested] formatted_text_to_ansi_string()              │
│   ├─ [nested] ANSILexer                                     │
│   ├─ [nested] OutputCapture                                 │
│   ├─ [nested] create_divider_window()                       │
│   ├─ [nested] get_argument_placeholder_text()               │
│   ├─ [nested] append_to_output_buffer()                     │
│   ├─ [nested] on_text_changed()                             │
│   ├─ [nested] accept_handler()                              │
│   ├─ [nested] 12+ more key bindings                         │
│   └─ [state dict] mutable state                             │
└─────────────────────────────────────────────────────────────┘
```

### Target Architecture (Modular)

```
┌─────────────────────────┐
│       REPL              │
│    (300 lines)          │
├─────────────────────────┤
│ - app_name              │
│ - config: Config        │
│ - plugins               │
│ - validation_rules      │
├─────────────────────────┤
│ + start()               │
│ + _load_plugins()       │
│ + _start_repl()         │
└──────────┬──────────────┘
           │ orchestrates
           │
     ┌─────┴─────┬──────────┬───────────┬────────────┬─────────────┐
     │           │          │           │            │             │
     ▼           ▼          ▼           ▼            ▼             ▼
┌─────────┐ ┌─────────┐ ┌────────┐ ┌────────┐ ┌───────────┐ ┌──────────┐
│REPLState│ │Layout   │ │Key     │ │Output  │ │Formatting │ │Output    │
│         │ │Builder  │ │Binding │ │Capture │ │           │ │Manager   │
│(150 ln) │ │(400 ln) │ │Manager │ │(150 ln)│ │(200 ln)   │ │          │
├─────────┤ ├─────────┤ │(400 ln)│ ├────────┤ ├───────────┤ ├──────────┤
│+reset   │ │+build() │ ├────────┤ │+write()│ │+fmt_to_   │ │+append() │
│+set_    │ │+create_ │ │+create_│ │+flush()│ │  ansi()   │ │+clear()  │
│ status()│ │ output()│ │ binding│ │        │ │           │ │          │
│+clear_  │ │+create_ │ │+handle_│ │        │ │+ANSILexer │ │          │
│ status()│ │ input() │ │ arrow()│ │        │ │           │ │          │
└─────────┘ │+create_ │ │+handle_│ └────────┘ └───────────┘ └──────────┘
            │ menu()  │ │ enter()│
            └─────────┘ └────────┘
```

**Dependencies:**
- REPL → Config, REPLState, LayoutBuilder, KeyBindingManager, OutputCapture, OutputManager
- LayoutBuilder → Config, REPLState, Buffer
- KeyBindingManager → Config, REPLState, Buffer, OutputManager, click.Group
- OutputCapture → Config, Callable
- OutputManager → Buffer, Config, Formatting
- Formatting → Config

---

## Data Flow

### User Input → Command Execution

```
User Input
    │
    ▼
┌───────────────────────┐
│  prompt_toolkit       │
│  Input Buffer         │
└───────┬───────────────┘
        │
        ▼
┌───────────────────────┐
│  on_text_changed()    │
│  (KeyBindingManager)  │
├───────────────────────┤
│ 1. Update state       │
│ 2. Check for /slash   │
│ 3. Trigger completion │
│ 4. Show placeholder   │
└───────┬───────────────┘
        │
        ▼
┌───────────────────────┐
│  User Presses Enter   │
└───────┬───────────────┘
        │
        ▼
┌───────────────────────┐
│  accept_handler()     │
│  (KeyBindingManager)  │
├───────────────────────┤
│ 1. Parse command      │
│ 2. Validate           │
│ 3. Execute            │
└───────┬───────────────┘
        │
        ▼
┌───────────────────────┐
│  _validate_command()  │
│  (REPL)               │
├───────────────────────┤
│ - Check rules         │
│ - Use Click parser    │
│ - Return result       │
└───────┬───────────────┘
        │
        │ If valid
        ▼
┌───────────────────────┐
│  click.Command.invoke │
├───────────────────────┤
│ - stdout redirected   │
│ - stderr redirected   │
└───────┬───────────────┘
        │
        ▼
┌───────────────────────┐
│  OutputCapture.write()│
├───────────────────────┤
│ - Intercept output    │
│ - Style if stderr     │
│ - Call callback       │
└───────┬───────────────┘
        │
        ▼
┌───────────────────────┐
│  OutputManager        │
│  .append_line()       │
├───────────────────────┤
│ 1. Format text        │
│ 2. Append to buffer   │
│ 3. Auto-scroll        │
└───────┬───────────────┘
        │
        ▼
┌───────────────────────┐
│  Output Buffer        │
│  (prompt_toolkit)     │
├───────────────────────┤
│ - Render with ANSI    │
│ - Display to user     │
└───────────────────────┘
```

### Completion Flow

```
User Types "/"
    │
    ▼
on_text_changed()
    │
    ├─> state.slash_command_active = True
    │
    ▼
SlashCommandCompleter
    │
    ├─> Get completions from CLI
    │
    ▼
state.completions = [...]
    │
    ▼
Render Menu Window
    │
    ▼
User Presses ↑↓
    │
    ▼
handle_arrow_up/down()
    │
    ├─> state.selected_idx += 1
    │
    ▼
Update Menu Highlight
    │
    ▼
User Presses Enter
    │
    ▼
accept_handler()
    │
    ├─> Get selected completion
    ├─> Insert into buffer
    └─> Execute if complete
```

---

## Plugin Lifecycle

### Discovery → Registration → Execution

```
┌─────────────────────────────────────────────────────────────┐
│                    REPL.__init__()                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              _load_plugins()                                │
├─────────────────────────────────────────────────────────────┤
│  1. entry_points(group="repl.commands")                     │
│     ├─> example.commands:HelloCommandsPlugin               │
│     └─> <other plugins>                                     │
│                                                             │
│  2. For each entry point:                                   │
│     ├─> plugin_class = ep.load()                            │
│     ├─> plugin = plugin_class()                             │
│     ├─> plugins.append(plugin)                              │
│     └─> plugin.register(cli, context_factory)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           Plugin.register(cli, context_factory)             │
├─────────────────────────────────────────────────────────────┤
│  @click.command()                                           │
│  @click.argument("env", type=click.Choice([...]))           │
│  def deploy(env):                                           │
│      print(f"Deploying to {env}")                           │
│                                                             │
│  cli.add_command(deploy, name="deploy")                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              _introspect_commands()                         │
├─────────────────────────────────────────────────────────────┤
│  For each command in cli.commands:                          │
│    ├─> Extract params (arguments, options)                  │
│    ├─> Check types (click.Choice, etc.)                     │
│    ├─> Determine validation level (required/optional/none)  │
│    └─> Store ValidationRule(...)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              validation_rules: Dict                         │
├─────────────────────────────────────────────────────────────┤
│  "deploy" → ValidationRule(                                 │
│      level="required",                                      │
│      required_args=["env"],                                 │
│      choice_params={"env": ["dev", "staging", "prod"]},     │
│      click_command=<deploy command>                         │
│  )                                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   User runs command                         │
│                   "/deploy dev"                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            _validate_command("deploy", ["dev"])             │
├─────────────────────────────────────────────────────────────┤
│  rule = validation_rules["deploy"]                          │
│  ctx = click.Context(rule.click_command)                    │
│  rule.click_command.parse_args(ctx, ["dev"])                │
│  → Success! ValidationResult(status="valid")                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                cli.invoke(["deploy", "dev"])                │
├─────────────────────────────────────────────────────────────┤
│  → Calls deploy(env="dev")                                  │
│  → stdout redirected to OutputCapture                       │
│  → Output appears in REPL                                   │
└─────────────────────────────────────────────────────────────┘
```

**Timeline:**
1. **Initialization Time:** Plugins discovered and registered
2. **Startup Time:** Validation rules extracted from Click commands
3. **Runtime:** Commands validated and executed on demand

---

## Migration Strategy

### Phase 2 Execution Order

**Task 2.2: Extract State Management** (8 hours)
- Create `state.py` with REPLState dataclass
- Replace `state = {}` dict with `state = REPLState()`
- Update all `state["key"]` to `state.key`
- Add helper methods (reset_completions, set_status, etc.)

**Task 2.3: Extract Formatting** (6 hours)
- Create `formatting.py`
- Move `formatted_text_to_ansi_string()` function
- Move `ANSILexer` class
- Update imports in `repl.py`

**Task 2.4: Extract Output Capture** (8 hours)
- Create `output_capture.py`
- Move `OutputCapture` class
- Create `OutputManager` class for append_to_output_buffer logic
- Update imports and instantiation in `repl.py`

**Task 2.5: Extract Layout Builder** (12 hours)
- Create `layout.py`
- Create `LayoutBuilder` class
- Move all window creation logic (output, status, input, info, menu, divider)
- Move intro banner creation
- Replace inline layout code with `layout = builder.build(...)`

**Task 2.6: Extract Key Bindings** (12 hours)
- Create `key_bindings.py`
- Create `KeyBindingManager` class
- Move all key binding registration
- Move event handlers (on_text_changed, accept_handler, arrows, tab, enter, etc.)
- Replace inline key binding code with `bindings = manager.create_bindings()`

**Task 2.7: Refactor Core REPL** (8 hours)
- Import all new modules
- Remove extracted code
- Replace nested functions with class instantiations
- Verify `_start_repl()` is now ~100 lines
- Verify `repl.py` is now ~300 lines total

### Testing Strategy

**After each extraction:**
1. Run full test suite (must pass 160/160)
2. Manually test example app
3. Commit with clear message
4. Continue to next extraction

**No functionality changes** - pure refactoring

### Rollback Plan

Each task is independently committable. If issues arise:
1. Identify failing task
2. `git revert <commit>`
3. Fix issue
4. Re-apply refactoring

---

## Success Metrics

### Before Refactoring
- ❌ repl.py: 1,576 lines (3.2x over limit)
- ❌ _start_repl(): ~1,100 lines (22x over limit)
- ❌ 20+ nested closures
- ❌ Mutable dict state
- ❌ 15 responsibilities in one class

### After Refactoring
- ✅ repl.py: ~300 lines (under 500 limit)
- ✅ _start_repl(): ~100 lines (under 50 limit for orchestration)
- ✅ 0 nested closures (all extracted to classes)
- ✅ Typed REPLState dataclass
- ✅ Single responsibility per module
- ✅ All 160 tests passing
- ✅ All modules ≤ 500 lines
- ✅ All functions ≤ 50 lines

---

## Approval Required

**This architecture must be approved before proceeding with Task 2.2.**

Questions to consider:
1. Is the module breakdown sensible?
2. Are responsibilities clearly separated?
3. Are dependencies manageable?
4. Is the migration strategy sound?

**Once approved, we will proceed with Task 2.2: Extract State Management.**

---

**Document Version:** 1.0
**Status:** Awaiting User Approval
**Next Step:** Task 2.2 - Extract State Management
