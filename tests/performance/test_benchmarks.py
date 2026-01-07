"""Performance benchmarks for cli-repl-kit.

These tests ensure the framework maintains acceptable performance characteristics:
- Startup time < 500ms
- Memory usage < 50MB
- Command execution overhead < 100ms
"""
import time
import tracemalloc
from pathlib import Path
import click
import pytest

from cli_repl_kit import REPL


class TestStartupPerformance:
    """Test REPL startup performance."""

    def test_startup_time_under_500ms(self):
        """Startup must be under 500ms.

        GIVEN a fresh REPL instance
        WHEN the REPL is initialized
        THEN initialization completes in under 500ms
        """
        start = time.perf_counter()
        repl = REPL(app_name="Benchmark")
        duration = time.perf_counter() - start

        # Print for visibility
        print(f"\nStartup time: {duration*1000:.2f}ms")

        assert duration < 0.5, f"Startup took {duration:.3f}s (max 0.5s)"

    def test_startup_with_plugins_under_1s(self):
        """Startup with plugin discovery under 1 second.

        GIVEN a REPL with plugin discovery enabled
        WHEN the REPL is initialized
        THEN initialization completes in under 1 second
        """
        start = time.perf_counter()
        repl = REPL(
            app_name="Benchmark",
            plugin_group="repl.commands"
        )
        duration = time.perf_counter() - start

        print(f"\nStartup with plugins: {duration*1000:.2f}ms")

        assert duration < 1.0, f"Startup took {duration:.3f}s (max 1.0s)"


class TestMemoryUsage:
    """Test memory footprint."""

    def test_memory_usage_under_50mb(self):
        """Baseline memory must be under 50MB.

        GIVEN a fresh REPL instance
        WHEN memory usage is measured
        THEN peak memory is under 50MB
        """
        tracemalloc.start()

        # Create REPL instance
        repl = REPL(app_name="Benchmark")

        # Get memory stats
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Convert to MB
        current_mb = current / 1024 / 1024
        peak_mb = peak / 1024 / 1024

        print(f"\nMemory usage: current={current_mb:.2f}MB, peak={peak_mb:.2f}MB")

        assert peak_mb < 50, f"Memory usage {peak_mb:.1f}MB (max 50MB)"

    def test_memory_with_commands_under_60mb(self):
        """Memory with commands registered under 60MB.

        GIVEN a REPL with multiple commands registered
        WHEN memory usage is measured
        THEN peak memory is under 60MB
        """
        tracemalloc.start()

        repl = REPL(app_name="Benchmark")

        # Register several commands to simulate real usage
        @repl.cli.command()
        @click.argument("arg1")
        def cmd1(arg1):
            """Command 1."""
            pass

        @repl.cli.command()
        @click.argument("arg1")
        @click.option("--opt1", "-o")
        def cmd2(arg1, opt1):
            """Command 2."""
            pass

        @repl.cli.group()
        def group1():
            """Group 1."""
            pass

        @group1.command()
        def subcmd1():
            """Subcommand 1."""
            pass

        # Introspect to build validation rules
        repl.validation_manager.introspect_commands()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024
        print(f"\nMemory with commands: {peak_mb:.2f}MB")

        assert peak_mb < 60, f"Memory usage {peak_mb:.1f}MB (max 60MB)"


class TestCommandExecutionOverhead:
    """Test command execution performance."""

    def test_validation_overhead_under_10ms(self):
        """Validation overhead under 10ms per command.

        GIVEN a REPL with validation enabled
        WHEN a command is validated
        THEN validation completes in under 10ms
        """
        repl = REPL(app_name="Benchmark")

        @repl.cli.command()
        @click.argument("name")
        @click.argument("env", type=click.Choice(["dev", "prod"]))
        def deploy(name, env):
            """Deploy command."""
            pass

        # Introspect to build rules
        repl.validation_manager.introspect_commands()

        # Measure validation time
        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            repl.validation_manager.validate_command("deploy", ["myapp", "prod"])

        duration = time.perf_counter() - start
        avg_ms = (duration / iterations) * 1000

        print(f"\nValidation overhead: {avg_ms:.3f}ms per command")

        assert avg_ms < 10, f"Validation took {avg_ms:.2f}ms (max 10ms)"

    def test_completion_generation_under_50ms(self):
        """Completion generation under 50ms.

        GIVEN a REPL with multiple commands
        WHEN completions are generated
        THEN generation completes in under 50ms
        """
        repl = REPL(app_name="Benchmark")

        # Register multiple commands
        for i in range(20):
            @repl.cli.command(name=f"command{i}")
            def cmd():
                """Test command."""
                pass

        from cli_repl_kit.core.completion import SlashCommandCompleter
        from prompt_toolkit.document import Document

        # Build command dict
        commands = {name: cmd.help or "" for name, cmd in repl.cli.commands.items()}
        completer = SlashCommandCompleter(commands, repl.cli)

        # Measure completion time
        iterations = 50
        start = time.perf_counter()

        for _ in range(iterations):
            doc = Document("/comm")
            list(completer.get_completions(doc, None))

        duration = time.perf_counter() - start
        avg_ms = (duration / iterations) * 1000

        print(f"\nCompletion generation: {avg_ms:.3f}ms per request")

        assert avg_ms < 50, f"Completion took {avg_ms:.2f}ms (max 50ms)"


class TestConfigurationLoading:
    """Test configuration loading performance."""

    def test_config_load_under_100ms(self, tmp_path):
        """Config loading under 100ms.

        GIVEN a config file
        WHEN config is loaded
        THEN loading completes in under 100ms
        """
        from cli_repl_kit.core.config import Config

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
appearance:
  ascii_art_text: "Test App"
  box_width: 80
colors:
  divider: "cyan"
  prompt: "green"
""")

        # Measure load time
        iterations = 10
        start = time.perf_counter()

        for _ in range(iterations):
            Config.load(str(config_file))

        duration = time.perf_counter() - start
        avg_ms = (duration / iterations) * 1000

        print(f"\nConfig load time: {avg_ms:.3f}ms")

        assert avg_ms < 100, f"Config load took {avg_ms:.2f}ms (max 100ms)"


@pytest.mark.benchmark
class TestRegressionPrevention:
    """Benchmark tests that prevent performance regressions.

    These tests document current performance and will fail if
    performance degrades significantly in future changes.
    """

    def test_repl_initialization_baseline(self):
        """Document baseline REPL initialization time."""
        times = []

        for _ in range(10):
            start = time.perf_counter()
            REPL(app_name="Benchmark")
            times.append(time.perf_counter() - start)

        avg_ms = (sum(times) / len(times)) * 1000
        min_ms = min(times) * 1000
        max_ms = max(times) * 1000

        print(f"\nREPL init: avg={avg_ms:.2f}ms, min={min_ms:.2f}ms, max={max_ms:.2f}ms")

        # This is a baseline - document current performance
        # Fail if significantly slower than 500ms
        assert avg_ms < 500, f"Average init time {avg_ms:.2f}ms exceeds baseline"
