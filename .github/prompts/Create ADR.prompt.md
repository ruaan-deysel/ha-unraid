---
description: Create Architectural Decision Record for important design choices
---

# Create Architectural Decision Record (ADR)

Document an important architectural or design decision for the ha-unraid integration.

If not provided, ask for:

- What decision needs to be documented
- Context: Why is this decision being made
- Options considered
- Chosen approach and rationale

## ADR Structure

Create a new ADR in `docs/development/adr/NNNN-title-of-decision.md`:

```markdown
# ADR-NNNN: [Title of Decision]

**Status:** Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-XXXX

**Date:** YYYY-MM-DD

## Context and Problem Statement

[Describe the context and background. What is the issue we're trying to address?]

**Key considerations:**

- [Consideration 1]
- [Consideration 2]

## Decision Drivers

- [Driver 1: e.g., "Must follow HA Core quality scale"]
- [Driver 2: e.g., "Minimize API calls to Unraid server"]

## Considered Options

### Option 1: [Title]

**Pros:** ...
**Cons:** ...

### Option 2: [Title]

**Pros:** ...
**Cons:** ...

## Decision Outcome

**Chosen option:** Option X - [Title]

**Rationale:** [Why this option was selected]

**Consequences:**

- Positive: ...
- Negative: ...

## Implementation Notes

**Files affected:**

- `custom_components/unraid/[file.py]`

## Validation

- [ ] Success criterion 1
- [ ] Success criterion 2
```

## Common ADR Topics for ha-unraid

### Data Management
- Coordinator polling intervals (why 30s / 5min / 15min)
- Optional service graceful degradation pattern
- Pydantic model `extra="ignore"` forward compatibility

### Entity Design
- Single device per server vs per-subsystem devices
- Entity unique ID format (`{server_uuid}_{resource_id}`)
- Translation key naming conventions

### API Integration
- SSL auto-detection fallback
- Version checking (MIN_API_VERSION, MIN_UNRAID_VERSION)
- Session injection via `async_get_clientsession`

### Architecture
- Triple coordinator pattern vs single/dual
- Button entities not extending UnraidBaseEntity (action-only, no coordinator)
- Repair flows for persistent auth failures

## Process

1. Check existing ADRs in `docs/development/adr/`
2. Use next sequential number (0001, 0002, etc.)
3. Create the directory if it doesn't exist
4. Focus on the "why" not just the "what"
5. Reference in `docs/development/DECISIONS.md`

## Integration Context

- **Domain:** `unraid`
- **Class prefix:** `Unraid`
- **Architecture docs:** `AGENTS.md`
- **Decisions log:** `docs/development/DECISIONS.md`
