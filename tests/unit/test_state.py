"""Unit tests for REPL state management."""
from cli_repl_kit.core.state import REPLState


class TestREPLStateDefaults:
    """Test REPLState default values."""

    def test_default_completions_empty_list(self):
        """Test completions defaults to empty list."""
        state = REPLState()
        assert state.completions == []

    def test_default_selected_idx_zero(self):
        """Test selected_idx defaults to 0."""
        state = REPLState()
        assert state.selected_idx == 0

    def test_default_placeholder_inactive(self):
        """Test placeholder_active defaults to False."""
        state = REPLState()
        assert state.placeholder_active is False

    def test_default_placeholder_start_zero(self):
        """Test placeholder_start defaults to 0."""
        state = REPLState()
        assert state.placeholder_start == 0

    def test_default_status_text_empty(self):
        """Test status_text defaults to empty list."""
        state = REPLState()
        assert state.status_text == []

    def test_default_info_text_empty(self):
        """Test info_text defaults to empty list."""
        state = REPLState()
        assert state.info_text == []

    def test_default_slash_command_inactive(self):
        """Test slash_command_active defaults to False."""
        state = REPLState()
        assert state.slash_command_active is False

    def test_default_not_multiline(self):
        """Test is_multiline defaults to False."""
        state = REPLState()
        assert state.is_multiline is False

    def test_default_menu_not_kept_visible(self):
        """Test menu_keep_visible defaults to False."""
        state = REPLState()
        assert state.menu_keep_visible is False


class TestREPLStateCustomValues:
    """Test REPLState with custom values."""

    def test_create_with_completions(self):
        """Test creating state with completions."""
        state = REPLState(completions=["hello", "help"])
        assert state.completions == ["hello", "help"]
        assert state.selected_idx == 0  # Other fields still default

    def test_create_with_selected_idx(self):
        """Test creating state with selected index."""
        state = REPLState(selected_idx=5)
        assert state.selected_idx == 5

    def test_create_with_all_fields(self):
        """Test creating state with all fields specified."""
        state = REPLState(
            completions=["cmd1", "cmd2"],
            selected_idx=1,
            placeholder_active=True,
            placeholder_start=10,
            status_text=[("cyan", "Status")],
            info_text=[("yellow", "Info")],
            slash_command_active=True,
            is_multiline=True,
            menu_keep_visible=True,
        )
        assert state.completions == ["cmd1", "cmd2"]
        assert state.selected_idx == 1
        assert state.placeholder_active is True
        assert state.placeholder_start == 10
        assert state.status_text == [("cyan", "Status")]
        assert state.info_text == [("yellow", "Info")]
        assert state.slash_command_active is True
        assert state.is_multiline is True
        assert state.menu_keep_visible is True


class TestREPLStateResetCompletions:
    """Test reset_completions() method."""

    def test_reset_completions_clears_list(self):
        """Test reset_completions clears the completions list."""
        state = REPLState(completions=["hello", "help"], selected_idx=2)
        state.reset_completions()
        assert state.completions == []

    def test_reset_completions_resets_index(self):
        """Test reset_completions resets selected_idx to 0."""
        state = REPLState(completions=["hello", "help"], selected_idx=5)
        state.reset_completions()
        assert state.selected_idx == 0

    def test_reset_completions_preserves_other_fields(self):
        """Test reset_completions doesn't affect other fields."""
        state = REPLState(
            completions=["hello"],
            selected_idx=1,
            slash_command_active=True,
            is_multiline=True,
        )
        state.reset_completions()
        assert state.completions == []
        assert state.selected_idx == 0
        # Other fields unchanged
        assert state.slash_command_active is True
        assert state.is_multiline is True


class TestREPLStateSetStatus:
    """Test set_status() method."""

    def test_set_status_updates_text(self):
        """Test set_status updates status_text."""
        state = REPLState()
        state.set_status([("cyan", "Ready")])
        assert state.status_text == [("cyan", "Ready")]

    def test_set_status_replaces_existing(self):
        """Test set_status replaces existing status text."""
        state = REPLState(status_text=[("red", "Error")])
        state.set_status([("green", "Success")])
        assert state.status_text == [("green", "Success")]

    def test_set_status_with_empty_list(self):
        """Test set_status with empty list."""
        state = REPLState(status_text=[("cyan", "Status")])
        state.set_status([])
        assert state.status_text == []


class TestREPLStateClearStatus:
    """Test clear_status() method."""

    def test_clear_status_empties_list(self):
        """Test clear_status empties status_text."""
        state = REPLState(status_text=[("cyan", "Status")])
        state.clear_status()
        assert state.status_text == []

    def test_clear_status_when_already_empty(self):
        """Test clear_status when status_text already empty."""
        state = REPLState()
        state.clear_status()
        assert state.status_text == []


class TestREPLStateSetInfo:
    """Test set_info() method."""

    def test_set_info_updates_text(self):
        """Test set_info updates info_text."""
        state = REPLState()
        state.set_info([("yellow", "Help available")])
        assert state.info_text == [("yellow", "Help available")]

    def test_set_info_replaces_existing(self):
        """Test set_info replaces existing info text."""
        state = REPLState(info_text=[("red", "Warning")])
        state.set_info([("green", "Tip")])
        assert state.info_text == [("green", "Tip")]


class TestREPLStateClearInfo:
    """Test clear_info() method."""

    def test_clear_info_empties_list(self):
        """Test clear_info empties info_text."""
        state = REPLState(info_text=[("yellow", "Info")])
        state.clear_info()
        assert state.info_text == []

    def test_clear_info_when_already_empty(self):
        """Test clear_info when info_text already empty."""
        state = REPLState()
        state.clear_info()
        assert state.info_text == []


class TestREPLStateMutability:
    """Test that REPLState is mutable (not frozen)."""

    def test_can_modify_completions(self):
        """Test we can modify completions after creation."""
        state = REPLState()
        state.completions = ["hello", "help"]
        assert state.completions == ["hello", "help"]

    def test_can_modify_selected_idx(self):
        """Test we can modify selected_idx after creation."""
        state = REPLState()
        state.selected_idx = 3
        assert state.selected_idx == 3

    def test_can_modify_flags(self):
        """Test we can modify boolean flags after creation."""
        state = REPLState()
        state.slash_command_active = True
        state.is_multiline = True
        state.placeholder_active = True
        assert state.slash_command_active is True
        assert state.is_multiline is True
        assert state.placeholder_active is True
