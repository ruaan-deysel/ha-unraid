# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## GitHub is used for everything

GitHub is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. Run `./scripts/setup` to install dependencies and pre-commit hooks.
3. If you've changed something, update the documentation.
4. Make sure your code passes all checks (`./scripts/lint`).
5. Test your contribution (`pytest`).
6. Issue that pull request!

## Keep Pull Requests Small and Focused

**Important**: Please submit small, focused pull requests that address a single issue or feature.

### Why Small PRs Matter

- **Easier to review**: Reviewers can quickly understand the changes and provide meaningful feedback
- **Faster to merge**: Small PRs are approved and merged more quickly
- **Easier to test**: Focused changes are simpler to test thoroughly
- **Easier to debug**: If something breaks, it's easier to identify the cause
- **Less risk**: Smaller changes have less chance of introducing unintended side effects

### What Makes a Good PR

Good examples:

- Fix a specific bug (one issue, one PR)
- Add a single new sensor type
- Update documentation for a particular feature
- Refactor one specific module or function

Avoid:

- Combining multiple bug fixes in one PR
- Mixing bug fixes with new features
- Refactoring code while also adding features
- Making unrelated changes across multiple files

### If You Have Multiple Changes

If you have multiple improvements or fixes:

1. Create separate branches for each change
2. Submit separate pull requests for each branch
3. Reference related PRs in the description if they depend on each other

This approach makes it much easier to review, test, and merge your contributions!

## Development Workflow

```bash
# 1. Setup (once)
./scripts/setup

# 2. Make code changes

# 3. Lint (auto-fixes most issues)
./scripts/lint

# 4. Run tests
pytest

# 5. Test in live HA instance (optional)
./scripts/develop
```

## Use a Consistent Coding Style

- **Formatter/Linter**: [Ruff](https://docs.astral.sh/ruff/) (line-length 88, Python 3.13)
- **Type hints**: Required on all public functions
- **Imports**: Use `from __future__ import annotations`
- See [`AGENTS.md`](AGENTS.md) for full code style documentation

## Test your code modification

This custom component provides a Home Assistant integration for Unraid servers.

It comes with a development environment in a container, easy to launch
if you use Visual Studio Code. With this container you will have a standalone
Home Assistant instance running and already configured with the included
[`configuration.yaml`](./config/configuration.yaml) file.

Use `./scripts/develop` to start a local HA instance with the integration loaded.

## Any contributions you make will be under the Apache License 2.0

In short, when you submit code changes, your submissions are understood to be under the same [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issues](../../issues)

GitHub issues are used to track public bugs.
Report a bug by [opening a new issue](../../issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## License

By contributing, you agree that your contributions will be licensed under its Apache License 2.0.
