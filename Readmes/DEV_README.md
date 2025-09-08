# AI Project

A Python project for AI development.

## Installation

This project uses `uv` for dependency management. Install dependencies with:

```bash
uv sync
```

## Code Quality Checks

This project uses multiple tools to ensure code quality and consistency. Run these checks before committing your code:

### Ruff (Fast Python Linter)

Ruff is an extremely fast Python linter that checks for various code issues:

```bash
# Check all Python files in the current directory
uv tool run ruff check

# Check a specific file
uv tool run ruff check main.py

# Auto-fix fixable issues
uv tool run ruff check --fix

# Check with all rules enabled
uv tool run ruff check --select ALL
```

### Pylint (Comprehensive Code Analyzer)

Pylint provides more comprehensive analysis including:
- Code errors and warnings
- Refactoring suggestions
- Code complexity analysis
- Unused variables (including module-level)
- Convention violations

```bash
# Check all Python files in the current directory
uv tool run pylint .

# Check a specific file
uv tool run pylint main.py

# Check with a specific configuration
uv tool run pylint --rcfile=.pylintrc main.py

# Generate a detailed report
uv tool run pylint --reports=y main.py
```

### Running All Checks

For convenience, you can run both linters:

```bash
# Run both Ruff and Pylint
uv tool run ruff check && uv tool run pylint .
```
