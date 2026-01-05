# Claude Code-Style UI Implementation Plan

## Research Summary

### Current Problem
Your `cli-repl-kit` uses `click_repl` which relies on prompt-toolkit's **floating menu** approach. This prevents:
- Placing a grey line **between** input and menu (menu floats on top)
- Full control over menu positioning
- Multi-area layout with dividers

### The Solution: prompt-toolkit's Layout System

The key is to **stop using floating menus** and instead build a **custom layout** with fixed screen areas:

```
┌─────────────────────────────────┐
│  OUTPUT AREA (scrollable)       │
│  stdout/stderr appears here     │
├─────────────────────────────────┤
│  STATUS AREA (collapsible)      │  ← Initially height=0
│  [status messages, todos, etc]  │
├─────────────────────────────────┤  ← Grey divider line
│  INPUT AREA (multi-line)        │
│  > /command                     │
├─────────────────────────────────┤  ← Grey divider line
│  MENU/COMPLETION AREA           │
│  /help        Show commands     │
└─────────────────────────────────┘
```

**Core Components:**
1. **`HSplit`** - Stacks areas vertically (output, status, input, menu)
2. **`Window`** - Container for each area
3. **`TextControl`** - Display static/dynamic text (output, status, dividers, menu)
4. **`EditBufferControl`** - Multi-line input editing
5. **`Layout`** - Root container wrapping HSplit
6. **`ConditionalContainer`** - Show/hide status area dynamically

---

## Implementation Phases (Prioritized)

### Phase 1: Core Layout Infrastructure (PRIORITY)
**Goal:** Replace `click_repl` with custom layout system

**Files to modify:**
- `/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/core/repl.py`

**Implementation:**
1. Create `HSplit` with 6 areas:
   - Output window (scrollable, dynamic height)
   - Status window (collapsible, initially height=0)
   - Top grey divider (1 line, fixed)
   - Input window (multi-line, 3-4 lines preferred)
   - Bottom grey divider (1 line, fixed)
   - Menu window (scrollable, dynamic height)

2. Replace `click_repl.repl()` with `PromptSession` using custom layout

3. Setup dynamic text controls:
   - Output area: Lambda function returning output history
   - Status area: Lambda function returning status messages (empty initially)
   - Menu area: Lambda function rendering completions

4. **Use existing styles from simple-agent:**
   - Purple highlight: `#6B4FBB`
   - Grey text: `#808080`
   - Import from `/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/ui/styles.py`

**Key Code Pattern:**
```python
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.layout.controls import TextControl, EditBufferControl
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.layout.dimension import Dimension as D

# Grey divider helper
def grey_line():
    return Window(
        height=1,
        content=TextControl(
            text=FormattedText([('#808080', '─' * 200)])
        )
    )

# Build layout
layout = Layout(
    HSplit([
        Window(content=output_control, height=D(preferred=15)),
        Window(content=status_control, height=0),  # Initially hidden
        grey_line(),
        Window(content=input_control, height=D(preferred=3)),
        grey_line(),
        Window(content=menu_control, height=D(preferred=5)),
    ])
)
```

**Testing:**
- Verify grey lines appear above AND below input
- Verify menu appears in fixed area (not floating)
- Verify multi-line input works

---

### Phase 2: Multi-line Input Area (PRIORITY)
**Goal:** Implement proper multi-line editing with visual feedback

**Files to modify:**
- `/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/core/repl.py`

**Implementation:**
1. Create `Buffer` with `multiline=True`
2. Use `EditBufferControl` to display buffer
3. Add key bindings:
   - **Shift+Enter**: Insert newline (primary method)
   - **Ctrl+J**: Insert newline (fallback for terminals that don't support Shift+Enter)
   - **Enter**: Submit command OR auto-select first completion if available
4. Visual feedback: Show line numbers or continuation markers

**Note on Shift+Enter:** ❌ **CONFIRMED: Shift+Enter does NOT work**
- `s-enter` binding throws `ValueError: Invalid key: s-enter` in prompt-toolkit
- Terminal escape sequences for Shift+Enter are not standardized
- **Solution: Use Ctrl+J as the primary newline insertion method**
- This is documented in the code with comments

**Key Code Pattern:**
```python
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import EditBufferControl
from prompt_toolkit.key_binding import KeyBindings

input_buffer = Buffer(
    multiline=True,
    completer=your_completer,
    complete_while_typing=True
)

input_control = EditBufferControl(buffer=input_buffer)

kb = KeyBindings()

# Try Shift+Enter (may not work in all terminals)
@kb.add('s-enter')
def insert_newline_shift(event):
    event.current_buffer.insert_text('\n')

# Fallback: Ctrl+J
@kb.add('c-j')
def insert_newline_ctrl(event):
    event.current_buffer.insert_text('\n')

@kb.add('enter')
def submit_or_complete(event):
    # If completions available and first one matches, insert it
    if current_completions and len(current_completions) > 0:
        first_completion = current_completions[0]
        # Insert the completion
        event.current_buffer.insert_text(first_completion.text)
    else:
        # Submit command
        event.current_buffer.validate_and_handle()
        # OR process command here
        pass
```

**Testing:**
- Verify Shift+Enter inserts newline (or document if it doesn't work)
- Verify Ctrl+J inserts newline as fallback
- Verify Enter submits command when no completions
- Verify Enter auto-selects first completion when typing `/` or `/xxx`
- Verify input area expands with multiple lines

---

### Phase 3: Menu/Completion Display Area (PRIORITY)
**Goal:** Render completions inside menu window (not floating)

**Files to modify:**
- `/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/core/repl.py`
- `/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/core/completion.py`

**Implementation:**
1. Monitor input buffer for changes
2. Generate completions using existing `SlashCommandCompleter`
3. Render completions as formatted text in menu window
4. **Auto-select first completion:** Always select index 0 when completions appear
5. Highlight selected completion (purple #6B4FBB from existing styles)
6. Handle up/down arrow keys to navigate completions
7. **Enter key behavior:** When completions visible, Enter selects the highlighted completion (default is first)

**Key Code Pattern:**
```python
# Track selected completion
selected_idx = 0
current_completions = []

def render_completions():
    """Render completions with highlighting."""
    lines = []
    for i, comp in enumerate(current_completions):
        if i == selected_idx:
            # Purple highlight
            lines.append(FormattedText([
                ('#6B4FBB', f'{comp.display} {comp.display_meta}')
            ]))
        else:
            # Grey
            lines.append(FormattedText([
                ('#808080', f'{comp.display} {comp.display_meta}')
            ]))
    return '\n'.join(lines)

menu_window = Window(
    content=TextControl(text=render_completions),
    height=D(preferred=5)
)
```

**Testing:**
- Verify completions appear in menu area
- Verify first completion is automatically selected (purple) without needing to press Tab
- Verify typing `/` shows completions with first one selected
- Verify typing `/he` filters to `/help` and auto-selects it
- Verify Enter key inserts the selected (first) completion
- Verify up/down arrows change selection
- Verify Tab also inserts selected completion

---

### Phase 4: Output Area (Scrollable)
**Goal:** Display stdout/stderr above input

**Files to modify:**
- `/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/core/repl.py`

**Implementation:**
1. Capture stdout/stderr to buffer
2. Store output history in list
3. Render output history in output window
4. Enable scrolling with Page Up/Down

**Key Code Pattern:**
```python
output_lines = []  # List of output strings

def add_output(text):
    """Add line to output history."""
    output_lines.append(text)
    # Keep last 1000 lines
    if len(output_lines) > 1000:
        output_lines.pop(0)

def render_output():
    """Render output lines."""
    return '\n'.join(output_lines)

output_window = Window(
    content=TextControl(text=render_output),
    height=D(preferred=15),
    always_include_vertical_scroll=True,
    wrap_lines=True
)
```

**Testing:**
- Verify command output appears in output area
- Verify scrolling works
- Verify new output pushes old output up

---

### Phase 5: Integration & Refinement
**Goal:** Polish and integrate all areas

**Files to modify:**
- `/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/core/repl.py`
- `/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/ui/styles.py`

**Implementation:**
1. Integrate output capturing with Click command execution
2. Auto-scroll output to bottom when new content arrives
3. Clear input buffer after command submission
4. Handle window resizing gracefully
5. **Apply existing simple-agent styles** (purple #6B4FBB, grey #808080)
6. Status area remains at height=0 for now (can be enabled later)

**Testing:**
- Full end-to-end testing of REPL
- Test with various terminal sizes
- Test with long output
- Test with long input

---

## Critical Files

1. **`/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/core/repl.py`** (Main changes)
   - Replace `click_repl.repl()` with custom `PromptSession` + `Layout`
   - Build HSplit structure
   - Implement output capturing
   - Implement completion rendering

2. **`/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/core/completion.py`** (Minor changes)
   - Keep `SlashCommandCompleter` logic
   - May need to adapt for manual rendering

3. **`/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/ui/styles.py`** (Optional)
   - Add prompt-toolkit style definitions
   - Centralize purple/grey colors

---

## Key Architecture Decision

**Current:** `click_repl` wrapper → floating menu → limited control

**New:** `PromptSession` → custom `Layout` → full control

**Trade-off:** More code, but achieves exact Claude Code UI

---

## Resources

- **prompt-toolkit examples:** https://github.com/prompt-toolkit/python-prompt-toolkit/tree/main/examples
  - `full_screen_layout.py` - Multi-area layout example
  - `custom_layout.py` - Layout customization
  - `multiline_input.py` - Multi-line editing

- **prompt-toolkit docs:** https://python-prompt-toolkit.readthedocs.io/en/3.0.52/
  - Layout section: Building complex layouts
  - Windows section: Display containers
  - Controls section: Text and buffer controls

---

## Recommended Phase Order

1. **Phase 1** (Core Layout) - Foundation for everything
2. **Phase 3** (Menu Area) - Get completions working in new layout
3. **Phase 2** (Multi-line Input) - Refine input experience
4. **Phase 4** (Output Area) - Add output capturing
5. **Phase 5** (Integration) - Polish and refinement

**Rationale:** Getting the layout structure right (Phase 1) and completions working (Phase 3) are the hardest parts. Once those work, the rest is refinement.

---

## Success Criteria

✅ Grey lines appear both above AND below input area
✅ Completion menu appears in fixed area below input (not floating)
✅ **Shift+Enter** inserts newline in multi-line input (or Ctrl+J if Shift+Enter doesn't work)
✅ **Enter key auto-selects first completion** when typing `/` or `/xxx`
✅ **First completion is auto-selected (purple)** without pressing Tab
✅ Command output appears in scrollable area above input
✅ **Status area exists** (height=0 initially, expandable later)
✅ **Existing simple-agent styles applied** (purple #6B4FBB, grey #808080)
✅ No flickering or layout issues

## Additional Requirements Summary

1. **Status Area:**
   - Positioned between output area and input area
   - Initially height=0 (collapsed)
   - Can be expanded later for todos, status messages, etc.
   - Lowest implementation priority

2. **Shift+Enter:**
   - Primary method for inserting newlines
   - Ctrl+J as fallback if Shift+Enter doesn't work
   - Must test across terminals and document behavior

3. **Auto-select First Completion:**
   - When user types `/` or `/xxx` and hits Enter, first match is chosen
   - First completion should be purple (selected) by default
   - No need to press Tab to select first item

4. **Existing Styles:**
   - Use colors from `/Users/simonfrank/Documents/dev/python/cli-repl-kit/src/cli_repl_kit/ui/styles.py`
   - Purple: `#6B4FBB`
   - Grey: `#808080`
