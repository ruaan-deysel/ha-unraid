---
applyTo: "**/*.md"
---

# Markdown Documentation Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## Documentation Hierarchy

- **`AGENTS.md`** — Single source of truth for all AI agents
- **`CLAUDE.md`** / **`GEMINI.md`** — Thin wrappers pointing to `AGENTS.md`
- **`.github/copilot-instructions.md`** — Copilot wrapper with quick reference
- **`README.md`** — User-facing documentation
- **`CHANGELOG.md`** — Release notes

## Rules

- Keep `AGENTS.md` as the authoritative source — update it, not the wrappers
- `CLAUDE.md` and `GEMINI.md` should remain thin (just reference `AGENTS.md`)
- Use GitHub-flavored Markdown
- Code blocks must specify language (```python, ```yaml, ```bash, etc.)
- Prefer tables for structured data
- Keep lines reasonable length for readability in editors

## CHANGELOG.md

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [Version] - YYYY-MM-DD
### Added
### Changed
### Fixed
### Removed
```

## README.md

User-facing — avoid internal development details. Focus on:
- Installation instructions
- Configuration steps
- Feature descriptions
- Troubleshooting
