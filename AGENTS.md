# AGENTS.md

## Core Development Environment

- Use Poetry to manage dependencies and use the Python version range defined in `pyproject.toml` (currently `^3.12`).
- Use the project-local `.venv` for local development. Run tests with `poetry run python -m pytest`.
- GitHub Actions runs pytest with coverage on Ubuntu under Python 3.12 and 3.13.

## Python Preferences

- Follow the user's current instructions and the project's configuration. Preserve existing API contracts and apply these preferences within the requested scope.
- Changes must pass Ruff checks (`poetry run ruff check .`) and Pyright checks when Pyright is available. Use the settings in `pyproject.toml`.
- Explicitly define and use a `TypedDict` for every dictionary with fixed keys.
- Reason about thread safety as if the GIL were absent, regardless of the Python version, interpreter build, or runtime setting. Use explicit synchronization or thread-safe abstractions for shared mutable state, including compound read-modify-write and check-then-act operations. Avoid relying on incidental atomicity of built-in operations.
- Separate statement blocks such as `if` and `try` from adjacent statements with blank lines. Treat declarations used only by the block and immediately preceding it as part of the block. Treat immediately following cleanup of objects associated with the block as part of it too.
- Leave a blank line after parameter validation in a function body.
- When a function signature spans multiple lines, indent continuation parameters two levels and the closing parenthesis one level relative to the `def` statement. End the function header with `# fmt: skip  # Preserve the project's multiline parameter indentation.`
