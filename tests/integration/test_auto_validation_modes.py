"""Integration tests for automatic validation in CLI and REPL modes."""
import subprocess
import sys


class TestCLIModeValidation:
    """Test that validation works in CLI mode."""

    def test_cli_missing_required_arg(self):
        """Test CLI blocks on missing required argument."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "hello"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should fail because hello requires text argument
        assert result.returncode != 0
        # Error message should mention missing or required
        assert "required" in result.stderr.lower() or "missing" in result.stderr.lower()

    def test_cli_valid_required_arg(self):
        """Test CLI succeeds with valid required argument."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "hello", "World"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "hello - World" in result.stdout

    def test_cli_invalid_choice(self):
        """Test CLI blocks on invalid choice value."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "deploy", "invalid"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should fail because "invalid" is not a valid choice
        assert result.returncode != 0
        # Error message should mention the valid choices
        assert "dev" in result.stderr or "staging" in result.stderr or "prod" in result.stderr

    def test_cli_valid_choice_dev(self):
        """Test CLI succeeds with valid choice value 'dev'."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "deploy", "dev"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "Deploying to dev" in result.stdout
        assert "successful" in result.stdout

    def test_cli_valid_choice_staging(self):
        """Test CLI succeeds with valid choice value 'staging'."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "deploy", "staging"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "Deploying to staging" in result.stdout

    def test_cli_valid_choice_prod_shows_warning(self):
        """Test CLI succeeds with 'prod' and shows warning."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "deploy", "prod"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "WARNING" in result.stdout
        assert "PRODUCTION" in result.stdout
        assert "Deploying to prod" in result.stdout

    def test_cli_subcommand_missing_arg(self):
        """Test CLI blocks on subcommand missing required argument."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "sub", "red"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should fail because sub red requires text argument
        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "missing" in result.stderr.lower()

    def test_cli_subcommand_with_arg(self):
        """Test CLI succeeds with subcommand and required argument."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "sub", "red", "test message"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "RED: test message" in result.stdout

    def test_cli_optional_arg_empty(self):
        """Test CLI succeeds with optional argument empty."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "list_files"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # list_files has nargs=-1 without required=True, so it should work
        assert result.returncode == 0

    def test_cli_command_no_params(self):
        """Test CLI succeeds with command that has no parameters."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "quit"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "Goodbye" in result.stdout

    def test_cli_error_message_format(self):
        """Test that CLI error messages are shown in stderr."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "hello"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode != 0
        # Error should be in stderr
        assert len(result.stderr) > 0
        # Should mention the error (Click shows MissingParameter exception)
        assert "text" in result.stderr.lower() or "parameter" in result.stderr.lower()

    def test_cli_built_in_print_command(self):
        """Test CLI validation for built-in print command."""
        # Print command requires text argument
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "print"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should fail because print requires text
        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "missing" in result.stderr.lower()

    def test_cli_built_in_print_command_with_text(self):
        """Test CLI succeeds with print command and text."""
        result = subprocess.run(
            [sys.executable, "-m", "demo.cli", "print", "test", "message"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "test message" in result.stdout
