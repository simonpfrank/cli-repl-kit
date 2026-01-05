"""Entry point for Hello World demo app."""

from cli_repl_kit import REPL


def main():
    """Start the Hello World CLI/REPL."""
    repl = REPL(app_name="Hello World Demo")
    repl.start(enable_agent_mode=True)  # Enable free text input


if __name__ == "__main__":
    main()
