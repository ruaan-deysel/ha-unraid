---
description: Create a structured implementation plan for a new feature or change
---

# Create Implementation Plan

Create a detailed implementation plan for a feature or change in the ha-unraid integration.

## Context

Read these files first:
- `AGENTS.md` — Full project documentation and architecture
- `custom_components/unraid/__init__.py` — Entry point and runtime data
- `custom_components/unraid/coordinator.py` — Data flow
- `custom_components/unraid/const.py` — Constants and configuration

## Plan Structure

### 1. Summary
- What is being implemented and why
- Which parts of the codebase are affected

### 2. Data Flow
- Where does the data come from? (Which API endpoint / coordinator)
- What data class changes are needed?
- Which coordinator should handle it?

### 3. Files Modified
For each file, describe:
- What changes are needed
- Any new classes, functions, or constants
- Impact on existing code

### 4. Files Created
- New files and their purpose
- How they integrate with existing code

### 5. Translation & Icon Changes
- New keys in `strings.json`
- New entries in `icons.json`

### 6. Test Plan
- What test scenarios to cover
- Which fixtures need updating
- Expected test file location

### 7. Quality Scale Impact
- Does this affect any `quality_scale.yaml` rules?
- Any new quality requirements to address?

## Rules

- Check `AGENTS.md` "Ask First" section — some changes require maintainer approval
- Prefer entity-based controls over service actions
- Follow existing patterns in the codebase
- Consider backwards compatibility (unique IDs must not change)
- Plan for graceful degradation if new API features aren't available
