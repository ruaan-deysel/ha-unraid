## Description

<!-- Provide a clear and concise description of your changes -->

## Type of Change

<!-- Please check the one that applies to this PR -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🔧 Configuration / CI change
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] ✅ Test update / new tests

## Related Issue

<!-- Link to the issue this PR addresses (e.g. Fixes #123, Closes #456) -->

Fixes #

## Changes Made

<!-- List the specific changes made in this PR -->

-
-
-

## ⚠️ Critical Rule: Never Bypass `unraid-api`

<!-- MANDATORY — All communication with the Unraid server must go through unraid-api. Failure to comply blocks merge. -->

- [ ] This PR does **not** bypass `unraid-api`: no direct GraphQL, HTTP/REST, WebSocket, SSH, or raw socket calls to the Unraid server have been added.
- [ ] All communication with the Unraid server strictly uses `UnraidClient` from `unraid-api`.
- [ ] If functionality needed for this PR is missing or incomplete in `unraid-api`, an issue has been filed at https://github.com/ruaan-deysel/unraid-api and this PR waits for the library to ship it.

## Quality & Architecture Checklist

<!-- Ensure the following Home Assistant integration standards and rules are met -->

- [ ] **Small & Focused**: This PR addresses **only one issue or feature**.
- [ ] **Python Conventions**: Includes `from __future__ import annotations` and explicit type hints on all public functions.
- [ ] **Entity Standards**: Follows `UnraidBaseEntity` / `UnraidEntity`, sets `_attr_has_entity_name = True`, and uses `_attr_translation_key` (no hardcoded English names).
- [ ] **Translations & Icons**: Any new/modified entity names are present in `strings.json` and generated in `translations/en.json`, with corresponding entries in `icons.json`.
- [ ] **Coordinators & State**: Uses the Triple Coordinator pattern; polling intervals remain fixed constants from `const.py` (not user-configurable); runtime data accessed via `config_entry.runtime_data`.
- [ ] **Dynamic Resources & Cleanup**: Any new dynamic/per-resource entities are properly tracked in `cleanup.py` and guarded against spurious removal.
- [ ] **Self-Review**: I have performed a self-review of my code and added explanatory comments for non-obvious logic.

## Validation & Verification

<!-- Please run and verify all local checks before submitting -->

- [ ] Boundary check passes: `./script/check_api_boundary.py` (or `./script/check`)
- [ ] Code formatting & linting pass: `./script/lint` (or `ruff check . && ruff format .`)
- [ ] Type checking passes: `./script/type-check` (or `mypy custom_components/unraid`)
- [ ] Unit tests pass with coverage >= 95%: `./script/test` (or `pytest`)
- [ ] Integration validation passes: `./script/check`
- [ ] Tested in local development environment: `./script/develop` (Home Assistant loads cleanly without unexpected errors or warnings)

## Screenshots / Verification Output (if applicable)

<!-- Add screenshots, logs, or terminal output demonstrating the fix or feature -->

## Additional Context

<!-- Add any other context about the PR here -->

---

**📌 Reminder**: Please keep pull requests small and focused on a single issue or feature. This makes review and testing much easier! If you have multiple changes, please submit separate PRs. See [CONTRIBUTING.md](../CONTRIBUTING.md#keep-pull-requests-small-and-focused) for details.
