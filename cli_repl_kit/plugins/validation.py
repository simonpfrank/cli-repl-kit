"""Automatic validation system for Click commands."""
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import click


@dataclass
class ValidationRule:
    """Auto-generated validation rule from Click command introspection.

    This class stores metadata extracted from Click commands to enable
    automatic validation without requiring manual validation methods.

    Attributes:
        level: Validation level - "required" (block if invalid),
               "optional" (warn if invalid), or "none" (no validation)
        required_args: List of required argument names
        optional_args: List of optional argument names
        arg_count_min: Minimum number of positional arguments
        arg_count_max: Maximum number of positional arguments (-1 for unlimited)
        choice_params: Dict mapping parameter names to valid choice lists
        type_params: Dict mapping parameter names to Click types
        required_options: List of required option names
        option_names: Dict mapping option names to their flags (e.g., ["--env", "-e"])
        click_command: Reference to the original Click command object
    """

    level: Literal["required", "optional", "none"]
    required_args: List[str] = field(default_factory=list)
    optional_args: List[str] = field(default_factory=list)
    arg_count_min: int = 0
    arg_count_max: int = 0
    choice_params: Dict[str, List[str]] = field(default_factory=dict)
    type_params: Dict[str, click.ParamType] = field(default_factory=dict)
    required_options: List[str] = field(default_factory=list)
    option_names: Dict[str, List[str]] = field(default_factory=dict)
    click_command: Optional[click.Command] = None
