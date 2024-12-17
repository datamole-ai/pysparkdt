# Contributing to pysparkdt

## Suggesting changes
1. Create an [issue](https://github.com/datamole-ai/pysparkdt/issues) describing the change you want to make.

## General workflow

### Environment setup
pysparkdt uses [Poetry](https://python-poetry.org/) for managing dependencies.
Follow the instructions on the Poetry website to install it.
We recommend [pyenv](https://github.com/pyenv/pyenv)
([installer](https://github.com/pyenv/pyenv-installer)) for managing Python versions.
```bash
# Install Python 3.12
pyenv install 3.12

# Use pyenv's Python 3.12 for the current folder
pyenv local 3.12

# Create virtual environment (install all optional dependencies)
poetry install --extras all

# Activate Poetry virtual environment in the current shell
poetry shell
```

You can also use `poetry run` to run commands in the virtual environment without activating it in the current shell (via `poetry shell`).


### Test the newly implemented changes
Create unit tests by creating a Python script in the folder `tests` prefixed with `test_`.
The script should contain functions also prefixed with `test_` that make assertions.
See the `tests` folder for reference.

## Pull Requests & Git

* Split your work into separate and atomic pull requests. Put any
  non-obvious reasoning behind any change to the pull request description.
  Separate “preparatory” changes and modifications from new features &
  improvements.
* The pull requests are squashed when merged. The PR title is used as the commit title.
  The PR description is used as the commit description.
* Use conventional commit messages in the PR title and description.
  See [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
  Usage of conventional commit PR titles and descriptions is enforced by the CI pipeline.
* Prefer adding new commits over amending existing ones during the review process.
  The latter makes it harder to review changes and track down modifications.


## Code style

* The line length is limited to 79 characters in Python code,
except if it would make the code less readable.
* `ruff` is used for formatting and linting Python code.
The following commands can be used to properly format the code and check
for linting errors with automatic fixing:
```bash
poetry run ruff format .
poetry run ruff check . --fix
```
The following commands can be used to check if the code is properly
formatted and check for linting errors:
```bash
poetry run ruff format --check .
poetry run ruff check .
```

All of the above code style requirements are enforced by the CI pipeline.
