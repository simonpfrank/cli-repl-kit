"""Entry point for Hello World demo app."""

import sys

from cli_repl_kit import REPL


def main():
    """Start the Hello World CLI/REPL.

    Supports both modes:
    - CLI mode: When called with arguments (e.g., `python -m example.cli hello World`)
    - REPL mode: When called without arguments (enters interactive mode)
    """
    repl = REPL(app_name="Hello World Demo")

    # If arguments provided, run in CLI mode (execute command and exit)
    if len(sys.argv) > 1:
        # Pass arguments to Click CLI for direct execution
        try:
            repl.cli(sys.argv[1:], standalone_mode=False)
        except SystemExit as e:
            # Click raises SystemExit, catch it to handle exit codes properly
            sys.exit(e.code)
    else:
        # No arguments - enter REPL mode
        repl.start(enable_agent_mode=True)


if __name__ == "__main__":
    main()
