# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

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

## Github is used for everything

Github is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. If you've changed something, update the documentation.
3. Make sure your code lints (using `scripts/lint`).
4. Test you contribution.
5. Issue that pull request!

## Keep Pull Requests Small and Focused

**Important**: Please submit small, focused pull requests that address a single issue or feature.

### Why Small PRs Matter

- **Easier to review**: Reviewers can quickly understand the changes and provide meaningful feedback
- **Faster to merge**: Small PRs are approved and merged more quickly
- **Easier to test**: Focused changes are simpler to test thoroughly
- **Easier to debug**: If something breaks, it's easier to identify the cause
- **Less risk**: Smaller changes have less chance of introducing unintended side effects

### What Makes a Good PR

✅ **Good Examples**:
- Fix a specific bug (one issue, one PR)
- Add a single new sensor type
- Update documentation for a particular feature
- Refactor one specific module or function

❌ **Avoid**:
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

## Any contributions you make will be under the Apache License 2.0

In short, when you submit code changes, your submissions are understood to be under the same [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](../../issues)

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

## Use a Consistent Coding Style

Use [ruff](https://github.com/astral-sh/ruff) for formatting and linting. Run `./scripts/lint` after every code change.

## Test your code modification

This custom component provides a Home Assistant integration for Unraid servers.

It comes with development environment in a container, easy to launch
if you use Visual Studio Code. With this container you will have a stand alone
Home Assistant instance running and already configured with the included
[`configuration.yaml`](./config/configuration.yaml)
file.

## License

By contributing, you agree that your contributions will be licensed under its Apache License 2.0.
