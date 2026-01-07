# cli-repl-kit Refactoring Plan

**Created:** 2026-01-07
**Target:** Transform from C+ (70%) to A+ (95-100%)
**Estimated Effort:** 120-160 hours over 4 weeks
**Current Issues:** Code Review identified 1,644-line monolith, nested closure hell, violated SOLID principles

---

## Overview

This plan addresses all issues identified in `CODE_REVIEW.md` and brings the codebase into full compliance with updated `CLAUDE.md` standards. The refactoring will be done incrementally with TDD, maintaining 160 passing tests throughout.

### Success Criteria

**MUST achieve before considering refactor complete:**
- ✅ All files ≤ 500 lines
- ✅ All functions ≤ 50 lines
- ✅ Max 2 levels of nesting
- ✅ Zero commented-out code
- ✅ Zero placeholder functions
- ✅ 100% type hints (mypy --strict passes)
- ✅ 90%+ branch coverage
- ✅ All 160+ tests passing
- ✅ Performance: startup < 500ms, memory < 50MB
- ✅ Architecture diagram in docs/
- ✅ Progressive examples (01-05)
- ✅ "How It Works" section in README

---

## Phase 1: Emergency Cleanup (Week 1, Days 1-2)
**Goal:** Remove technical debt, fix critical violations
**Estimated Time:** 16 hours

### Task 1.1: Delete All Commented Code (2 hours)
**Location:** `cli_repl_kit/core/repl.py` lines 612-696

**Actions:**
1. Delete all lines with `# PRESERVED` prefix
2. Delete commented-out old implementation
3. Run all tests to ensure nothing breaks
4. Commit: "chore: Remove commented code - trust git history"

**Acceptance Criteria:**
```bash
# Must return no results
grep -r "# PRESERVED" cli_repl_kit/
grep -r "def render_output" cli_repl_kit/  # Old function should be gone
```

**Tests:** All 160 tests must still pass

---

### Task 1.2: Fix/Remove Broken Commands (4 hours)
**Location:** `cli_repl_kit/core/repl.py` lines 242-273

**Problem:** `status_command()` and `info_command()` are registered but do nothing

**Option A: Remove (Recommended for speed)**
```python
# Delete status_command and info_command registration
# They're not working anyway
```

**Option B: Implement Properly**
```python
@self.cli.command(name="status")
@click.argument("text", nargs=-1, required=False)
def status_command(text):
    """Set or clear status line text."""
    # Need access to REPL state - requires refactoring first
    # DEFER to Phase 2 after state management refactor
```

**Decision:** Remove for now, re-implement in Phase 3 after state refactor

**Actions:**
1. Delete `status_command()` and `info_command()` registration
2. Update tests to remove these commands
3. Document in Progress_Tracker.md as "Deferred to Phase 3"
4. Commit: "fix: Remove unimplemented status/info commands"

**Tests Modified:**
- `test_repl_core.py` - remove status/info command tests
- Expected test count: 160 → ~156

---

### Task 1.3: Fix Function Naming (6 hours)
**Location:** Throughout `cli_repl_kit/core/repl.py`

**Renames Required:**

| Old Name | New Name | Line | Reason |
|----------|----------|------|--------|
| `formatted_to_ansi()` | `formatted_text_to_ansi_string()` | 28 | Explicit about input type |
| `get_command_args()` | `get_argument_placeholder_text()` | 627 | Returns placeholder, not args |
| `grey_line()` | `create_divider_window()` | 653 | Returns Window, not line |
| `add_output_line()` | `append_to_output_buffer()` | TBD | Writes to buffer, not list |

**Actions:**
1. Rename each function
2. Update all call sites
3. Update tests
4. Run tests after each rename
5. Commit after each: "refactor: Rename {old} to {new} for clarity"

**Tests:** All tests must pass after each rename

---

### Task 1.4: Fix Parameter Name Mismatches (4 hours)
**Location:** `example/commands.py` lines 35-40

**Bug:**
```python
@click.argument("text", nargs=-1, required=True)
def hello(message):  # ← Parameter name doesn't match argument name
```

**Fix:**
```python
@click.argument("text", nargs=-1, required=True)
def hello(text):  # Match parameter to argument name
    """Say hello with custom text."""
    message = " ".join(text)
    print(f"hello - {message}")
```

**Actions:**
1. Fix all parameter mismatches in example/commands.py
2. Fix malformed docstrings (echo command has two)
3. Verify examples still work
4. Commit: "fix: Align parameter names with Click arguments in examples"

**Tests:** Run example app manually to verify

---

## Phase 2: Architecture Refactoring (Week 1, Days 3-5 + Week 2, Days 1-2)
**Goal:** Split monolith into maintainable modules
**Estimated Time:** 40 hours

### Task 2.1: Create Architecture Diagram (4 hours)

**File:** `docs/architecture.md`

**Content Required:**
```markdown
# cli-repl-kit Architecture

## Module Structure

Current (1,644 lines):
- repl.py [MONOLITH - 1,644 lines]

Target (6 modules, each ≤ 500 lines):
- repl.py [Core orchestration - 300 lines]
- state.py [State management - 150 lines]
- layout.py [UI layout - 400 lines]
- output_capture.py [stdout/stderr - 150 lines]
- key_bindings.py [Keyboard handlers - 400 lines]
- formatting.py [ANSI/formatting - 200 lines]

## Class Diagram
[ASCII or Mermaid diagram showing class relationships]

## Data Flow
[Diagram showing how user input flows through system]

## Plugin Lifecycle
[Diagram showing when plugins are discovered, loaded, registered]
```

**Actions:**
1. Create architecture.md with diagrams
2. Review with user before coding
3. Commit: "docs: Add architecture diagram for refactoring"

**Acceptance:** User approves architecture before proceeding

---

### Task 2.2: Extract State Management (8 hours)

**New File:** `cli_repl_kit/core/state.py` (~150 lines)

**Create REPLState Dataclass:**
```python
"""State management for REPL sessions."""
from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class REPLState:
    """Tracks the state of a REPL session.

    This replaces the mutable dict pattern with a typed, documented,
    testable state object.

    Attributes:
        completions: List of available command completions for current input
        selected_idx: Index of currently selected completion (0-based)
        placeholder_active: True if placeholder text (<text>) is being shown
        placeholder_start: Cursor position where placeholder begins
        status_text: Formatted text for status line display
        info_text: Formatted text for info line display
        slash_command_active: True when user input starts with /
        is_multiline: True when input contains newlines
        menu_keep_visible: Keep completion menu visible after command execution

    Example:
        >>> state = REPLState()
        >>> state.slash_command_active = True
        >>> state.selected_idx = 2
    """
    completions: List[str] = field(default_factory=list)
    selected_idx: int = 0
    placeholder_active: bool = False
    placeholder_start: int = 0
    status_text: List[Any] = field(default_factory=list)
    info_text: List[Any] = field(default_factory=list)
    slash_command_active: bool = False
    is_multiline: bool = False
    menu_keep_visible: bool = False

    def reset_completions(self) -> None:
        """Clear completion state."""
        self.completions = []
        self.selected_idx = 0

    def set_status(self, text: List[Any]) -> None:
        """Set status line content."""
        self.status_text = text

    def clear_status(self) -> None:
        """Clear status line."""
        self.status_text = []
```

**Unit Tests Required:**
```python
# tests/unit/test_state.py
def test_repl_state_defaults()
def test_repl_state_reset_completions()
def test_repl_state_set_status()
def test_repl_state_clear_status()
def test_repl_state_immutable_with_frozen()  # Optional enhancement
```

**Actions:**
1. Write tests first (TDD)
2. Create state.py with REPLState dataclass
3. Run tests until passing
4. Update repl.py to import and use REPLState
5. Replace all `state["key"]` with `state.key`
6. Run all tests
7. Commit: "refactor: Extract state management to dataclass"

**Tests:** All existing tests + 5 new state tests

---

### Task 2.3: Extract Formatting Functions (6 hours)

**New File:** `cli_repl_kit/core/formatting.py` (~200 lines)

**Extract:**
- `formatted_text_to_ansi_string()` (was `formatted_to_ansi`)
- `ANSILexer` class
- Any ANSI-related utilities

**Structure:**
```python
"""ANSI formatting and lexing utilities."""
from typing import List, Tuple, Any
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.formatted_text import ANSI
from cli_repl_kit.core.config import Config

def formatted_text_to_ansi_string(
    formatted_text: List[Tuple[str, str]],
    config: Config
) -> str:
    """Convert FormattedText to ANSI escape codes.

    Args:
        formatted_text: List of (style, text) tuples
        config: Config object with ansi_colors settings

    Returns:
        String with ANSI escape codes embedded

    Example:
        >>> text = [("red", "Error"), ("", " occurred")]
        >>> formatted_text_to_ansi_string(text, config)
        '\x1b[31mError\x1b[0m occurred'
    """
    # Implementation...

class ANSILexer(Lexer):
    """Lexer that interprets ANSI escape codes.

    Converts ANSI-escaped text into FormattedText for
    prompt_toolkit rendering.

    Example:
        >>> lexer = ANSILexer()
        >>> document = Document("\\x1b[31mRed text\\x1b[0m")
        >>> lexer.lex_document(document)
    """
    # Implementation...
```

**Actions:**
1. Create formatting.py
2. Move functions from repl.py
3. Add type hints
4. Add docstrings with examples
5. Update imports in repl.py
6. Run tests
7. Commit: "refactor: Extract formatting functions to separate module"

**Tests:** Existing tests should still pass

---

### Task 2.4: Extract Output Capture (8 hours)

**New File:** `cli_repl_kit/core/output_capture.py` (~150 lines)

**Extract:**
- `OutputCapture` class
- Related buffer management

**Structure:**
```python
"""Output capture for stdout/stderr redirection."""
import io
from typing import Callable, List, Tuple, Any
from cli_repl_kit.core.config import Config

class OutputCapture(io.StringIO):
    """Capture stdout/stderr and redirect to output buffer.

    This class intercepts writes to stdout/stderr and sends them
    to the REPL output buffer with appropriate styling.

    Attributes:
        stream_type: Either "stdout" or "stderr"
        output_callback: Function to call with captured text
        config: Config for styling decisions

    Example:
        >>> def handle_output(text):
        ...     print(f"Captured: {text}")
        >>> capture = OutputCapture("stdout", handle_output, config)
        >>> capture.write("Hello")
        >>> # Calls handle_output([("", "Hello")])
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
        # Implementation with validation...
```

**Unit Tests:**
```python
# tests/unit/test_output_capture.py
def test_output_capture_stdout()
def test_output_capture_stderr()
def test_output_capture_invalid_stream_type()
def test_output_capture_write_returns_count()
def test_output_capture_ignores_empty()
```

**Actions:**
1. Write tests first
2. Create output_capture.py
3. Add validation (ValueError for invalid stream_type)
4. Fix write() to return bytes written
5. Update repl.py imports
6. Run tests
7. Commit: "refactor: Extract output capture to separate module"

**Tests:** All existing + 5 new tests

---

### Task 2.5: Extract Layout Builder (12 hours)

**New File:** `cli_repl_kit/core/layout.py` (~400 lines)

**Create LayoutBuilder Class:**
```python
"""UI layout construction for REPL."""
from typing import Callable, Any
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.buffer import Buffer
from cli_repl_kit.core.config import Config
from cli_repl_kit.core.state import REPLState
from cli_repl_kit.core.formatting import ANSILexer

class LayoutBuilder:
    """Builds prompt_toolkit Layout for REPL.

    Separates layout construction from REPL orchestration.
    Makes UI components testable and reusable.

    Attributes:
        config: Configuration for dimensions, colors
        state: REPLState for dynamic content

    Example:
        >>> builder = LayoutBuilder(config, state)
        >>> layout = builder.build(input_buffer, output_buffer)
        >>> app = Application(layout=layout)
    """

    def __init__(self, config: Config, state: REPLState):
        """Initialize layout builder.

        Args:
            config: REPL configuration
            state: REPL state object
        """
        self.config = config
        self.state = state

    def build(
        self,
        input_buffer: Buffer,
        output_buffer: Buffer
    ) -> Layout:
        """Build complete REPL layout.

        Args:
            input_buffer: Buffer for user input
            output_buffer: Buffer for command output

        Returns:
            Complete Layout with all windows
        """
        return Layout(
            HSplit([
                self._create_output_window(output_buffer),
                self._create_status_window(),
                self._create_divider(),
                self._create_input_window(input_buffer),
                self._create_divider(),
                self._create_info_window(),
                self._create_menu_window(),
            ])
        )

    def _create_output_window(self, buffer: Buffer) -> Window:
        """Create output display window."""
        # Max 50 lines per function rule!
        pass

    def _create_divider(self) -> Window:
        """Create horizontal divider line."""
        divider_color = self.config.colors.divider
        # Use terminal width, not hard-coded 200!
        import shutil
        width = shutil.get_terminal_size().columns
        return Window(
            height=1,
            content=FormattedTextControl(
                text=lambda: [(divider_color, "─" * width)]
            )
        )
```

**Unit Tests:**
```python
# tests/unit/test_layout.py
def test_layout_builder_creates_layout()
def test_layout_builder_divider_uses_terminal_width()
def test_layout_builder_output_window()
def test_layout_builder_input_window()
def test_layout_builder_menu_window()
def test_layout_builder_status_window()
```

**Actions:**
1. Write tests
2. Create LayoutBuilder class
3. Extract layout logic from repl.py
4. Fix magic number (200) to use terminal width
5. Keep each method under 50 lines
6. Update repl.py to use LayoutBuilder
7. Run tests
8. Commit: "refactor: Extract layout construction to LayoutBuilder class"

**Tests:** All existing + 6 new tests

---

### Task 2.6: Extract Key Bindings (12 hours)

**New File:** `cli_repl_kit/core/key_bindings.py` (~400 lines)

**Create KeyBindingManager Class:**
```python
"""Keyboard event handlers for REPL."""
from typing import Callable, Any
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.buffer import Buffer
from cli_repl_kit.core.state import REPLState
from cli_repl_kit.core.config import Config

class KeyBindingManager:
    """Manages keyboard bindings for REPL.

    Extracts key binding logic from massive _start_repl method.
    Each binding is a focused, testable method.

    Attributes:
        config: REPL configuration
        state: REPL state
        input_buffer: Input buffer
        output_buffer: Output buffer

    Example:
        >>> manager = KeyBindingManager(config, state, input_buf, output_buf)
        >>> bindings = manager.create_bindings()
        >>> app = Application(key_bindings=bindings)
    """

    def __init__(
        self,
        config: Config,
        state: REPLState,
        input_buffer: Buffer,
        output_buffer: Buffer,
        completion_callback: Callable,
        accept_callback: Callable
    ):
        """Initialize key binding manager."""
        self.config = config
        self.state = state
        self.input_buffer = input_buffer
        self.output_buffer = output_buffer
        self.completion_callback = completion_callback
        self.accept_callback = accept_callback

    def create_bindings(self) -> KeyBindings:
        """Create all key bindings.

        Returns:
            KeyBindings object with all handlers registered
        """
        kb = KeyBindings()

        # Register each handler
        self._register_navigation_keys(kb)
        self._register_editing_keys(kb)
        self._register_completion_keys(kb)
        self._register_submit_keys(kb)

        return kb

    def _register_navigation_keys(self, kb: KeyBindings) -> None:
        """Register arrow keys, page up/down."""
        @kb.add("up")
        def handle_up(event):
            """Handle up arrow."""
            self._handle_arrow_up(event)

        # Keep each handler under 50 lines!

    def _handle_arrow_up(self, event) -> None:
        """Handle up arrow navigation.

        Context-dependent:
        - If menu visible: navigate menu
        - If at start: navigate history
        - Otherwise: move cursor
        """
        # Extracted logic, testable independently
        pass
```

**Unit Tests:**
```python
# tests/unit/test_key_bindings.py
def test_key_binding_manager_creates_bindings()
def test_handle_arrow_up_navigates_menu()
def test_handle_arrow_up_navigates_history()
def test_handle_arrow_up_moves_cursor()
def test_handle_enter_submits()
def test_handle_ctrl_j_multiline()
def test_handle_tab_completes()
```

**Actions:**
1. Write tests for each handler
2. Create KeyBindingManager class
3. Extract key handlers from repl.py
4. Each handler method < 50 lines
5. Update repl.py to use KeyBindingManager
6. Run tests
7. Commit: "refactor: Extract key bindings to KeyBindingManager class"

**Tests:** All existing + 7 new tests

---

### Task 2.7: Refactor Core REPL (8 hours)

**Goal:** Reduce repl.py from 1,644 lines to ~300 lines

**After extraction, repl.py should only:**
```python
"""Core REPL orchestration."""
from cli_repl_kit.core.state import REPLState
from cli_repl_kit.core.layout import LayoutBuilder
from cli_repl_kit.core.key_bindings import KeyBindingManager
from cli_repl_kit.core.output_capture import OutputCapture
from cli_repl_kit.core.formatting import ANSILexer
from cli_repl_kit.core.config import Config

class REPL:
    """Main REPL orchestrator.

    Responsibilities (ONLY):
    - Plugin discovery and loading
    - Validation rule extraction
    - CLI/REPL mode switching
    - Orchestrating components (not implementing them)

    Does NOT:
    - Build layouts (LayoutBuilder does)
    - Handle keys (KeyBindingManager does)
    - Manage state (REPLState does)
    - Capture output (OutputCapture does)
    """

    def __init__(self, app_name, context_factory=None, ...):
        """Initialize REPL with configuration."""
        # 30-40 lines max

    def _load_plugins(self):
        """Discover and load plugins."""
        # 20-30 lines max

    def start(self, prompt_text=">", enable_agent_mode=False):
        """Start REPL or execute CLI command."""
        if len(sys.argv) > 1:
            self.cli.main(...)
        else:
            self._start_repl(prompt_text, enable_agent_mode)

    def _start_repl(self, prompt_text, enable_agent_mode):
        """Start interactive REPL."""
        # AFTER refactoring: ~100 lines (was 1,160!)

        # Create components
        state = REPLState()
        layout_builder = LayoutBuilder(self.config, state)
        key_manager = KeyBindingManager(...)

        # Build application
        layout = layout_builder.build(input_buffer, output_buffer)
        bindings = key_manager.create_bindings()

        # Run
        app = Application(layout=layout, key_bindings=bindings, ...)
        app.run()
```

**Actions:**
1. Import all extracted modules
2. Replace nested functions with class method calls
3. Verify all 20+ nested functions are now extracted
4. Ensure _start_repl is under 150 lines (target: 100)
5. Run all tests
6. Check file size: should be ~300 lines
7. Commit: "refactor: Reduce repl.py to orchestration only"

**Acceptance:**
```bash
wc -l cli_repl_kit/core/repl.py
# Must show ~300 lines (was 1,644)
```

**Tests:** All 160+ tests must still pass

---

## Phase 3: Type Safety & Documentation (Week 2, Days 3-5)
**Goal:** 100% type coverage, complete documentation
**Estimated Time:** 24 hours

### Task 3.1: Add Type Hints to All Code (12 hours)

**Target:** 100% type hint coverage, mypy --strict passes

**Files to Annotate:**
1. `cli_repl_kit/core/repl.py`
2. `cli_repl_kit/core/state.py` (should already have)
3. `cli_repl_kit/core/layout.py`
4. `cli_repl_kit/core/key_bindings.py`
5. `cli_repl_kit/core/output_capture.py`
6. `cli_repl_kit/core/formatting.py`
7. `cli_repl_kit/core/config.py`
8. `cli_repl_kit/plugins/base.py`
9. `cli_repl_kit/plugins/validation.py`
10. All test files

**Example Before:**
```python
def get_argument_placeholder_text(cmd_name, subcmd_name=None):
    """Get placeholder text."""
    # ...
```

**Example After:**
```python
from typing import Optional

def get_argument_placeholder_text(
    cmd_name: str,
    subcmd_name: Optional[str] = None
) -> Optional[str]:
    """Get placeholder text for a command's first argument.

    Args:
        cmd_name: Name of the top-level command (e.g., "deploy")
        subcmd_name: Name of subcommand if cmd_name is a group

    Returns:
        Placeholder text like "<environment>" if command has arguments,
        or None if command has no arguments or doesn't exist.

    Example:
        >>> get_argument_placeholder_text("deploy")
        "<environment>"
        >>> get_argument_placeholder_text("quit")
        None
    """
    # ...
```

**Actions:**
1. Install mypy: `pip install mypy`
2. Run `mypy --strict cli_repl_kit/` (expect many errors)
3. Fix errors file by file, starting with state.py (easiest)
4. Add NewType for domain types:
   ```python
   from typing import NewType
   CommandName = NewType('CommandName', str)
   CommandPath = NewType('CommandPath', str)
   ```
5. Eliminate all `Any` types (document if truly necessary)
6. Run `mypy --strict` until 0 errors
7. Commit: "feat: Add 100% type hint coverage, mypy --strict passes"

**Acceptance:**
```bash
mypy --strict cli_repl_kit/
# Success: no issues found
```

**Tests:** All tests must still pass

---

### Task 3.2: Complete All Docstrings (8 hours)

**Target:** Every public class/function has Google-style docstring with example

**Template:**
```python
def function_name(arg1: Type1, arg2: Type2) -> ReturnType:
    """One-line summary.

    Longer description if needed. Explain what this does and why.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When arg1 is invalid
        TypeError: When arg2 has wrong type

    Example:
        >>> function_name("value", 42)
        "result"
        >>> function_name("", 0)
        Traceback (most recent call last):
        ValueError: arg1 cannot be empty
    """
```

**Actions:**
1. Audit all public functions for docstrings
2. Add missing docstrings
3. Enhance existing docstrings with Args/Returns/Raises/Example
4. Add module docstrings to all files
5. Run: `pydocstyle cli_repl_kit/` to check
6. Commit: "docs: Complete all docstrings with examples"

**Acceptance:**
```bash
pydocstyle cli_repl_kit/
# No errors
```

---

### Task 3.3: Create Progressive Examples (4 hours)

**New Files:**
- `examples/01_basic_hello.py` - One command, prints hello
- `examples/02_with_arguments.py` - Command with arguments
- `examples/03_validation.py` - Using Click.Choice
- `examples/04_subcommands.py` - Groups and subcommands
- `examples/05_advanced.py` - Subprocess, context, styling

**Example 01:**
```python
"""
01 - Basic Hello World

The simplest possible cli-repl-kit application.
Shows: Plugin registration, single command, basic output.

Run:
    python examples/01_basic_hello.py
    > /hello
"""
from cli_repl_kit import REPL, CommandPlugin
import click
import sys

class HelloPlugin(CommandPlugin):
    """Single hello command."""

    @property
    def name(self):
        return "hello_plugin"

    def register(self, cli, context_factory):
        @click.command()
        def hello():
            """Say hello!"""
            print("Hello, World!")

        cli.add_command(hello, name="hello")

def main():
    repl = REPL(app_name="Example 01")
    if len(sys.argv) > 1:
        repl.cli(sys.argv[1:])
    else:
        repl.start()

if __name__ == "__main__":
    main()
```

**Actions:**
1. Create examples/ directory
2. Write examples 01-05, each building on previous
3. Test each example works
4. Add examples/README.md explaining progression
5. Commit: "docs: Add progressive examples 01-05"

---

## Phase 4: Testing & Quality (Week 3)
**Goal:** 90%+ coverage, performance benchmarks, cross-platform
**Estimated Time:** 40 hours

### Task 4.1: Achieve 90% Branch Coverage (16 hours)

**Current:** Likely ~70-80% (need to measure)
**Target:** 90%+ branch coverage

**Actions:**
1. Run: `pytest --cov=cli_repl_kit --cov-report=html --cov-branch`
2. Open htmlcov/index.html
3. Identify uncovered branches
4. Write tests for uncovered code:
   - Error paths
   - Edge cases
   - Validation failures
5. Repeat until 90%+
6. Commit: "test: Achieve 90% branch coverage"

**Acceptance:**
```bash
pytest --cov=cli_repl_kit --cov-branch
# Must show >= 90% branch coverage
```

---

### Task 4.2: Add BDD Integration Tests (12 hours)

**New File:** `tests/integration/test_user_workflows.py`

**Tests Required:**
```python
def test_user_can_run_basic_command():
    """GIVEN user starts REPL
    WHEN they type '/hello World' and press Enter
    THEN they see 'Hello, World!' in output"""
    # Readable test that matches user experience

def test_user_gets_validation_error():
    """GIVEN user starts REPL
    WHEN they type '/deploy' without environment
    THEN they see validation error
    AND command is not executed"""

def test_user_can_use_tab_completion():
    """GIVEN user starts REPL
    WHEN they type '/h' and press Tab
    THEN they see completion menu with /hello, /help"""

def test_user_can_navigate_history():
    """GIVEN user has executed commands
    WHEN they press Up arrow
    THEN they see previous command"""
```

**Actions:**
1. Write BDD-style integration tests
2. Test actual user workflows
3. No mocks - real integration
4. Add at least 10 workflow tests
5. Commit: "test: Add BDD integration tests for user workflows"

**Tests:** +10 new integration tests

---

### Task 4.3: Add Performance Tests (8 hours)

**New File:** `tests/performance/test_benchmarks.py`

**Tests Required:**
```python
import time
import tracemalloc

def test_startup_time_under_500ms():
    """Startup must be under 500ms."""
    start = time.perf_counter()
    repl = REPL(app_name="Benchmark")
    duration = time.perf_counter() - start
    assert duration < 0.5, f"Startup took {duration:.2f}s (max 0.5s)"

def test_memory_usage_under_50mb():
    """Baseline memory must be under 50MB."""
    tracemalloc.start()
    repl = REPL(app_name="Benchmark")
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    mb = peak / 1024 / 1024
    assert mb < 50, f"Memory usage {mb:.1f}MB (max 50MB)"

def test_command_execution_overhead_under_100ms():
    """Command execution overhead under 100ms."""
    # Measure time from user input to command start
    # Excluding command logic itself
    pass
```

**Actions:**
1. Create tests/performance/
2. Write benchmark tests
3. Run and record baseline
4. Add to CI/CD to track regressions
5. Document results in README
6. Commit: "test: Add performance benchmarks"

---

### Task 4.4: Cross-Platform Testing (4 hours)

**Goal:** Verify works on Linux, macOS, Windows

**Issues to Fix:**
1. `example/commands.py` uses hardcoded `ls` command
2. No platform detection
3. Path handling might not be cross-platform

**Fix:**
```python
import sys
import subprocess
from pathlib import Path

def list_files(path):
    """List files (cross-platform)."""
    target = Path(" ".join(path) if path else ".")

    # Platform-specific command
    if sys.platform == "win32":
        cmd = ["dir", "/W", str(target)]
    else:
        cmd = ["ls", "-la", str(target)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
```

**Actions:**
1. Fix hardcoded commands in examples
2. Use pathlib everywhere
3. Add platform detection where needed
4. Test on Windows (if available)
5. Document platform limitations
6. Commit: "fix: Ensure cross-platform compatibility"

---

## Phase 5: Security & Polish (Week 4)
**Goal:** Production-ready, secure, documented
**Estimated Time:** 40 hours

### Task 5.1: Security Audit (8 hours)

**Checks Required:**
1. ✅ No subprocess with shell=True
2. ✅ All external input validated
3. ✅ No secrets in code/logs
4. ✅ Path traversal prevention
5. ✅ Type boundaries for security

**Actions:**
1. Audit all subprocess calls
2. Add input validation to example commands:
   ```python
   from pathlib import Path

   def validate_path(path_str: str) -> Path:
       """Validate and sanitize path input."""
       path = Path(path_str).resolve()
       # Prevent path traversal
       if not path.is_relative_to(Path.cwd()):
           raise ValueError(f"Path {path} is outside working directory")
       return path
   ```
3. Document security assumptions
4. Add security section to README
5. Commit: "security: Add input validation and document assumptions"

---

### Task 5.2: Add "How It Works" to README (6 hours)

**New Section in README.md:**
```markdown
## How It Works

### Entry Points Discovery

When you install cli-repl-kit, Python's entry point system...

[Diagram showing plugin discovery flow]

### Click Command Tree

Your commands are organized as a Click command tree...

[Diagram showing CLI hierarchy]

### Validation Introspection

The framework automatically generates validation rules...

[Explain the introspection process]

### REPL Event Loop

When you start the REPL, here's what happens:

1. Config loaded from config.yaml
2. Plugins discovered via entry points
3. Validation rules extracted from Click commands
4. Layout built by LayoutBuilder
5. Key bindings registered by KeyBindingManager
6. Application runs with prompt_toolkit
```

**Actions:**
1. Write detailed "How It Works" section
2. Add architecture diagrams
3. Explain plugin lifecycle
4. Explain validation system
5. Commit: "docs: Add 'How It Works' section to README"

---

### Task 5.3: Complete README Updates (4 hours)

**Add Sections:**
- Performance characteristics
- Platform compatibility
- Security considerations
- Troubleshooting expanded
- Contributing guidelines enhanced

**Actions:**
1. Update README with all new content
2. Add performance benchmarks
3. Document platform support
4. Add security best practices
5. Commit: "docs: Complete README with performance, security, platform info"

---

### Task 5.4: CI/CD Pipeline (8 hours)

**New File:** `.github/workflows/quality.yml`

```yaml
name: Quality Checks

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov mypy ruff radon

      - name: Check file size limits
        run: |
          find cli_repl_kit -name "*.py" -exec wc -l {} \; | \
          awk '$1 > 500 {print "FAIL: " $2 " has " $1 " lines (max 500)"; exit 1}'

      - name: Check function complexity
        run: radon cc cli_repl_kit --min C --show-complexity

      - name: Check for commented code
        run: |
          if grep -r "# PRESERVED" cli_repl_kit/; then
            echo "FAIL: Commented code found"
            exit 1
          fi

      - name: Type checking
        run: mypy --strict cli_repl_kit/

      - name: Linting
        run: ruff check cli_repl_kit/

      - name: Tests with coverage
        run: pytest --cov=cli_repl_kit --cov-branch --cov-report=term-missing

      - name: Coverage threshold
        run: |
          coverage report --fail-under=90
```

**Actions:**
1. Create .github/workflows/quality.yml
2. Test locally with act (if available)
3. Push and verify runs
4. Fix any failures
5. Add badge to README
6. Commit: "ci: Add quality checks pipeline"

---

### Task 5.5: Final Quality Review (8 hours)

**Checklist:**
- [ ] All files ≤ 500 lines
- [ ] All functions ≤ 50 lines
- [ ] Max 2 nesting levels
- [ ] Zero commented code
- [ ] Zero placeholder functions
- [ ] mypy --strict passes
- [ ] ruff check passes
- [ ] radon cc all C or better
- [ ] 90%+ branch coverage
- [ ] All 180+ tests passing
- [ ] Performance benchmarks pass
- [ ] Examples all work
- [ ] README complete
- [ ] CI/CD passing

**Actions:**
1. Run full quality suite
2. Fix any remaining issues
3. Manual testing of examples
4. Performance verification
5. Commit: "chore: Final quality review and fixes"

---

### Task 5.6: Release Preparation (6 hours)

**Actions:**
1. Update version to 1.0.0
2. Write CHANGELOG.md
3. Tag release: `git tag v1.0.0`
4. Create GitHub release
5. Update installation docs
6. Announce refactoring complete

---

## Success Metrics

### Before Refactoring (Current State)
- **Grade:** C+ (70/100)
- **Largest File:** 1,644 lines
- **Largest Function:** 1,160 lines
- **Type Coverage:** ~40%
- **Branch Coverage:** ~70%
- **Commented Code:** ~100 lines
- **Violations:** Multiple SOLID principles

### After Refactoring (Target State)
- **Grade:** A+ (95-100/100)
- **Largest File:** ≤ 500 lines
- **Largest Function:** ≤ 50 lines
- **Type Coverage:** 100% (mypy --strict)
- **Branch Coverage:** ≥ 90%
- **Commented Code:** 0 lines
- **Violations:** 0 (SOLID compliant)

---

## Risk Mitigation

### Risk: Breaking Existing Tests
**Mitigation:** Run tests after every commit, maintain green build

### Risk: Scope Creep
**Mitigation:** Stick to plan, don't add features, focus on refactoring only

### Risk: Time Overrun
**Mitigation:** Time-box each task, defer non-critical items to v1.1

### Risk: Lost Functionality
**Mitigation:** Manual testing of examples after each phase

---

## Timeline

### Week 1: Emergency Cleanup + Architecture Start
- Days 1-2: Tasks 1.1-1.4 (Cleanup)
- Days 3-5: Tasks 2.1-2.3 (State, Formatting, Output)

### Week 2: Architecture Complete + Documentation
- Days 1-2: Tasks 2.4-2.7 (Layout, Keys, Core)
- Days 3-5: Tasks 3.1-3.3 (Types, Docs, Examples)

### Week 3: Testing & Quality
- Days 1-5: Tasks 4.1-4.4 (Coverage, BDD, Performance, Cross-platform)

### Week 4: Security & Release
- Days 1-5: Tasks 5.1-5.6 (Security, README, CI/CD, Review, Release)

---

## Notes

- This plan follows TDD: tests written before code
- Each task is independently committable
- All 160+ tests must pass throughout
- Use updated CLAUDE.md workflow strictly
- Get user approval on architecture (Task 2.1) before proceeding
- Time estimates are conservative; actual may be faster with focus

---

**Created:** 2026-01-07
**Author:** Claude (based on CODE_REVIEW.md analysis)
**Status:** Ready for user approval
**Next Step:** Review this plan, then start Task 1.1
