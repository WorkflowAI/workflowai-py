# Contributing to WorkflowAI

## Setup

### Prerequisites

- [Poetry](https://python-poetry.org/docs/#installation) for dependency management and publishing

### Getting started

```bash
# We recomment configuring the virtual envs in project with poetry so that
# it can easily be picked up by IDEs

# poetry config virtualenvs.in-project true
poetry install --all-extras

# Install the pre-commit hooks
poetry run pre-commit install
# or `make install` to install the pre-commit hooks and the dependencies

# Check the code quality
# Run ruff
poetry run ruff check .
# Run pyright
poetry run pyright
# or `make lint` to run ruff and pyright

# Run the unit and integration tests
# They do not require any configuration
poetry run pytest --ignore=tests/e2e # make test

# Run the end to end tests
# They require the `WORKFLOWAI_TEST_API_URL` and `WORKFLOWAI_TEST_API_KEY` environment variables to be set
# If they are present in the `.env` file, they will be picked up automatically
poetry run pytest tests/e2e
```

#### Configuring VSCode

Suggested extensions are available in the [.vscode/extensions.json](.vscode/extensions.json) file. When you open this project in VSCode or Cursor, you'll be prompted to install these recommended extensions automatically.

To manually install recommended extensions:
1. Open VSCode/Cursor Command Palette (Cmd/Ctrl + Shift + P)
2. Type "Show Recommended Extensions"
3. Install the ones marked with @recommended

These extensions will help ensure consistent code quality and style across all contributors.

### Dependencies

#### Ruff

[Ruff](https://github.com/astral-sh/ruff) is a very fast Python code linter and formatter.

```sh
ruff check . # check the entire project
ruff check src/workflowai/core # check a specific file
ruff check . --fix # fix linting errors automatically in the entire project
```

#### Pyright

[Pyright](https://github.com/microsoft/pyright) is a static type checker for Python.

> We preferred it to `mypy` because it is faster and easier to configure.

#### Pydantic

[Pydantic](https://docs.pydantic.dev/) is a data validation library for Python.
It provides very convenient methods to serialize and deserialize data, introspect its structure, set validation
rules, etc.

#### HTTPX

[HTTPX](https://www.python-httpx.org/) is a modern HTTP library for Python.
