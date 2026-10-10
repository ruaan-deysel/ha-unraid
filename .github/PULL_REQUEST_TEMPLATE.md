# Pull Request

## Description

<!-- Provide a clear and concise description of what this PR does -->

## Type of Change

<!-- Check all that apply -->

- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New sensor or entity platform
- [ ] New feature or enhancement
- [ ] Breaking change (change that causes existing automations or setups to fail)
- [ ] Documentation update
- [ ] Code refactoring (no functional changes)
- [ ] Test additions or improvements
- [ ] Frontend topology card or UI update

## Pre-Submission Governance

<!--
  REQUIRED for everyone, including AI agents and automation.
  Every box below is mandatory. If any box is left unchecked, the automated
  "PR Governance" check fails and the PR will not be reviewed or merged.
  Do not open multiple overlapping or back-to-back PRs for the same work;
  batch related changes together to avoid wasting CI runner capacity.
-->

- [ ] I built and ran the project locally and verified this change actually works (not just that it compiles)
- [ ] I ran `pytest` locally and all tests pass
- [ ] I ran `./script/lint` locally and it passes
- [ ] I pasted real local verification output under **Testing Performed** below (no placeholder text)
- [ ] This PR is self-contained and is not a duplicate; I have not opened other overlapping or back-to-back PRs for the same change
- [ ] If an AI agent created or assisted with this PR, a human reviewed and verified the changes before submission

## Related Issues

<!-- Link to related issues, or specify "None" for self-contained changes -->
<!-- Examples: Fixes #123, Closes https://github.com/..., Related to #456, or None -->

Fixes #

## Critical Rule: Never Bypass unraid-api

<!-- MANDATORY — All communication with the Unraid server must go through unraid-api. Failure to comply blocks merge. -->

- [ ] This PR does not bypass `unraid-api`: no direct GraphQL, HTTP/REST, WebSocket, SSH, or raw socket calls to the Unraid server have been added
- [ ] All communication with the Unraid server strictly uses `UnraidClient` from `unraid-api`
- [ ] If functionality needed for this PR is missing or incomplete in `unraid-api`, an issue has been filed at https://github.com/ruaan-deysel/unraid-api and this PR waits for the library to ship it

## Changes Made

<!-- List the main changes in this PR -->

-
-
-

## Home Assistant Quality Scale & Standards

<!-- Check all that apply to confirm compliance with modern Home Assistant development standards -->

- [ ] Verified against the [Home Assistant Developer Docs](https://developers.home-assistant.io/) and Quality Scale rules
- [ ] Uses `entry.runtime_data` patterns where applicable (no new `hass.data[DOMAIN]` usage)
- [ ] All entities read from coordinator state (`coordinator.data`) and avoid direct API/network calls
- [ ] New/updated entities use integration base entity classes appropriately
- [ ] Sensor implementations use modern native properties (no `unit_of_measurement`)
- [ ] Uses Home Assistant session helpers (no direct `aiohttp.ClientSession()` instantiation)
- [ ] Diagnostics redaction handled when sensitive fields are exposed
- [ ] Not applicable (documentation-only or metadata-only change)

## Testing Performed

<!-- Check all that apply and describe what you tested -->

- [ ] Ran unit tests (`pytest`)
- [ ] Ran linter (`./script/lint`)
- [ ] Ran type checking (`./script/type-check or mypy custom_components/unraid`)
- [ ] Ran pre-commit checks (`pre-commit run --all-files`)
- [ ] Tested live in local Home Assistant (`./script/develop`)
- [ ] Not applicable (documentation-only or metadata-only change)

### Test Results

```text
[Paste relevant local command output and verification notes]
```

## Documentation

<!-- Check all that apply -->

- [ ] Code comments added/updated where needed
- [ ] README.md updated (if needed)
- [ ] CHANGELOG.md updated under [Unreleased]
- [ ] AGENTS.md / developer documentation updated (if architecture or process changed)
- [ ] No documentation needed

## Breaking Changes

<!-- If this PR introduces breaking changes, describe them and provide migration instructions -->

## Checklist

<!-- Ensure you've completed all required items before submitting -->

- [ ] I have updated CHANGELOG.md under [Unreleased] with details of this change
- [ ] I verified my code against Home Assistant integration quality rules and used no deprecated APIs
- [ ] I linked related issues or noted "None" in **Related Issues**
- [ ] I completed all required sections in this template and removed placeholder-only content
- [ ] My code follows the project's coding standards and Home Assistant patterns
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas (if applicable)
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works (if applicable)
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published (if applicable)
- [ ] No sensitive information (tokens, passwords, personal data) is included
