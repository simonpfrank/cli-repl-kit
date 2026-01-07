# Security Considerations

**Last Updated:** 2026-01-07

## Overview

cli-repl-kit is designed with security in mind for building interactive command-line tools. This document outlines security assumptions, best practices, and potential risks.

## Security Model

### Trust Boundary

cli-repl-kit operates within the following trust boundaries:

1. **Trusted User**: The framework assumes commands are executed by a trusted user in their own environment
2. **Local Execution**: All commands run locally with the user's permissions
3. **No Network Exposure**: The REPL is not designed for remote or multi-user scenarios

### Threat Model

**In Scope:**
- Path traversal attacks via user input
- Command injection via subprocess
- Input validation bypasses
- Accidental execution of destructive commands

**Out of Scope:**
- Network-based attacks (framework is local-only)
- Multi-tenant security (single-user design)
- Cryptographic operations (not provided)
- Authentication/Authorization (single-user, local environment)

## Security Features

### 1. Safe Subprocess Execution

✅ **All subprocess calls use `shell=False`**

The framework and examples NEVER use `shell=True`, which prevents shell injection attacks.

```python
# SAFE - No shell injection possible
result = subprocess.run(
    ["ls", "-la", path],  # Array of arguments
    capture_output=True,
    text=True,
    check=True
)
```

❌ **Avoid this pattern:**
```python
# DANGEROUS - Shell injection possible
result = subprocess.run(
    f"ls -la {path}",  # String command
    shell=True  # NEVER DO THIS
)
```

### 2. Path Traversal Prevention

Example commands include path validation to prevent traversal attacks:

```python
from pathlib import Path

def list_files(path):
    # Validate path
    target_path = Path(path).resolve()
    cwd = Path.cwd().resolve()

    # Security: Prevent path traversal outside current directory
    if not str(target_path).startswith(str(cwd)):
        print(f"Error: Path '{path}' is outside current directory")
        return
```

### 3. Input Validation

Click's built-in validation is automatically enforced:

```python
@click.argument("env", type=click.Choice(["dev", "staging", "prod"]))
def deploy(env):
    """Deploy - automatically validates env is one of the allowed values."""
    pass
```

The framework's `ValidationManager` introspects Click decorators and validates input before execution.

### 4. Cross-Platform Safety

Platform-specific commands are handled safely:

```python
import sys

if sys.platform == "win32":
    cmd = ["dir", "/W", str(target_path)]
else:
    cmd = ["ls", "-la", str(target_path)]
```

## Security Best Practices

### For Framework Users

1. **Validate All User Input**
   - Use Click's `type=` parameter for validation
   - Add custom validation for complex inputs
   - Never trust user input in subprocess calls

2. **Restrict Path Access**
   ```python
   from pathlib import Path

   def validate_path(path_str: str) -> Path:
       """Validate path is within allowed directory."""
       path = Path(path_str).resolve()
       allowed_dir = Path.cwd().resolve()

       if not str(path).startswith(str(allowed_dir)):
           raise ValueError(f"Path outside allowed directory: {path}")

       return path
   ```

3. **Whitelist Commands**
   ```python
   ALLOWED_COMMANDS = ["git", "npm", "python"]

   def run_command(cmd):
       if cmd[0] not in ALLOWED_COMMANDS:
           raise ValueError(f"Command not allowed: {cmd[0]}")
       subprocess.run(cmd, ...)
   ```

4. **Use Timeouts**
   ```python
   subprocess.run(
       cmd,
       timeout=10,  # Prevent hanging
       ...
   )
   ```

5. **Handle Sensitive Data**
   - Never log passwords or API keys
   - Use environment variables for secrets
   - Clear sensitive data from memory when done

### For Framework Developers

1. **No `shell=True`** - EVER
2. **Validate all user inputs** before processing
3. **Use type hints** for better IDE support
4. **Document security assumptions** in code comments
5. **Review all subprocess calls** during code review

## Known Limitations

### 1. Local Execution Only

The framework is designed for local, single-user use. It does NOT provide:
- Multi-user isolation
- Network security
- Authentication/Authorization
- Sandboxing or containerization

### 2. User Permissions

Commands execute with the user's full permissions. Users can:
- Delete files they have permission to delete
- Modify system configuration
- Execute any command available on their system

**Mitigation**: This is by design for a CLI tool. Users should:
- Run in isolated environments (containers, VMs) if needed
- Use appropriate file system permissions
- Implement command whitelisting for production tools

### 3. Plugin Trust

Plugins discovered via entry points are fully trusted and execute with full user permissions.

**Mitigation**:
- Only install plugins from trusted sources
- Review plugin code before installation
- Use virtual environments to isolate dependencies

## Security Checklist for Production

Before deploying a cli-repl-kit based tool:

- [ ] All subprocess calls use `shell=False`
- [ ] All user inputs are validated
- [ ] Path inputs are restricted to allowed directories
- [ ] Commands are whitelisted if executing external tools
- [ ] Sensitive data (passwords, keys) are never logged
- [ ] Timeouts are set for all subprocess calls
- [ ] Error messages don't leak sensitive information
- [ ] Dependencies are reviewed and up-to-date
- [ ] Plugin sources are trusted and verified

## Reporting Security Issues

If you discover a security vulnerability in cli-repl-kit:

1. **DO NOT** open a public GitHub issue
2. Email the maintainer privately (see README for contact)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

## Security Audit Results

**Last Audit:** 2026-01-07

### Findings

✅ **No critical issues found**

**Verified:**
- All subprocess calls use `shell=False`
- No SQL injection vectors (framework doesn't use databases)
- No XSS vectors (CLI-only, no web interface)
- Path traversal prevention implemented in examples
- Input validation enforced via Click types

**Recommendations Implemented:**
1. Added path traversal prevention to example commands
2. Added security warnings to shell execution examples
3. Documented cross-platform command handling
4. Created this security documentation

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [subprocess security](https://docs.python.org/3/library/subprocess.html#security-considerations)
- [Click Security](https://click.palletsprojects.com/en/8.1.x/documentation/#documenting-arguments)
