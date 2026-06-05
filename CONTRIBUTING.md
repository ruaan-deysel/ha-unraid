# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## ⚠️ Critical Rule: Never Bypass `unraid-api`

**All communication with the Unraid server must go through the
[`unraid-api`](https://github.com/ruaan-deysel/unraid-api) library (`UnraidClient`).**
This is a hard architectural requirement — not a preference.

**You must never:**
- Add direct GraphQL queries, REST/HTTP calls, WebSockets, SSH, or any other network I/O to the Unraid server from this repo.
- Re-implement, monkey-patch, vendor, or work around `unraid-api` to "get a fix in faster."
- Use `requests`, `httpx`, `websockets`, `paramiko`, `asyncssh`, raw `gql`, or direct `aiohttp.ClientSession()` in `custom_components/unraid/`.

**If a feature you need is not exposed by `unraid-api`:**

1. **Stop** — do not add a workaround here.
2. Open an issue on the library repo: **https://github.com/ruaan-deysel/unraid-api**
3. Wait for the library to ship the capability, then consume it via `UnraidClient`.

This rule is enforced automatically at three levels:
- **`git commit`** — pre-commit hook (`check-api-boundary`) blocks the commit.
- **`./script/check`** — runs the boundary check before linting and type-checking.
- **CI** — `check-api-boundary.yml` workflow blocks the PR from merging.

PRs that bypass the library will be rejected without further review.

## Before Opening an Issue ⚠️

**Please do the following BEFORE creating a new issue:**

1. **Search existing issues** — check **both open AND closed** issues:
   - [Open issues](https://github.com/ruaan-deysel/ha-unraid/issues)
   - [Closed issues](https://github.com/ruaan-deysel/ha-unraid/issues?q=is%3Aissue+is%3Aclosed)
2. **Use the correct channel:**
   - **Bug reports** → [Open a Bug Report issue](https://github.com/ruaan-deysel/ha-unraid/issues/new?template=bug-report.yml)
   - **Feature requests** → [Open a Feature Request issue](https://github.com/ruaan-deysel/ha-unraid/issues/new?template=feature-request.yml)
   - **Questions, setup help, "how do I…"** → [GitHub Discussions](https://github.com/ruaan-deysel/ha-unraid/discussions) (NOT Issues)
3. **Use the issue templates** — do not bypass them. Blank issues are disabled.
4. **Fill in all required fields** — incomplete issues will be closed.

> **Issues that are duplicates, missing required information, or are questions/support requests will be closed without further notice.**

## GitHub is used for everything

GitHub is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. Run `./script/setup` to install dependencies and pre-commit hooks.
3. If you've changed something, update the documentation.
4. Make sure your code passes all checks (`./script/lint`).
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
./script/setup

# 2. Make code changes

# 3. Lint (auto-fixes most issues)
./script/lint

# 4. Run tests
pytest

# 5. Test in live HA instance (optional)
./script/develop
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

Use `./script/develop` to start a local HA instance with the integration loaded.

## Any contributions you make will be under the Apache License 2.0

In short, when you submit code changes, your submissions are understood to be under the same [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issues](../../issues)

GitHub issues are used to track **confirmed bugs and feature requests only**.
For questions, setup help, or troubleshooting, use [GitHub Discussions](https://github.com/ruaan-deysel/ha-unraid/discussions) instead.

Report a bug by [opening a new issue](../../issues/new/choose) — but **search existing open and closed issues first** to avoid duplicates.

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
