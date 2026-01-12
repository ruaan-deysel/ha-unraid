<!--
================================================================================
SYNC IMPACT REPORT
================================================================================
Version Change: N/A (initial) → 1.0.0
Modified Principles: N/A (new constitution)
Added Sections:
  - Core Principles (5 principles for HA integration quality)
  - Home Assistant Standards section
  - Development Workflow section
  - Governance section
Removed Sections: N/A (new constitution)
Templates Requiring Updates:
  - .specify/templates/plan-template.md: ✅ Compatible (generic Constitution Check)
  - .specify/templates/spec-template.md: ✅ Compatible (no constitution references)
  - .specify/templates/tasks-template.md: ✅ Compatible (no constitution references)
  - .specify/templates/agent-file-template.md: ✅ Compatible (no constitution references)
  - .specify/templates/checklist-template.md: ✅ Compatible (no constitution references)
Follow-up TODOs: None
================================================================================
-->

# ha-unraid Constitution

## Core Principles

### I. Home Assistant Quality Compliance

All code MUST comply with Home Assistant integration quality standards and architectural
patterns. This is NON-NEGOTIABLE and serves as the foundation for all development work.

- All integrations MUST pass Home Assistant's integration quality checklist
- Code MUST follow Home Assistant's coding style and conventions
- MUST use Home Assistant's recommended libraries and patterns
- MUST NOT use deprecated Home Assistant APIs
- MUST handle errors and exceptions according to Home Assistant guidelines
- MUST use UNRAID-API python library for Unraid communication
- MUST NOT introduce dependencies that conflict with HA core requirements
- All changes MUST be tested against current stable HA releases before merge

**Rationale**: Home Assistant has established quality standards to ensure integrations
are stable, secure, and maintainable. Non-compliance creates technical debt and risks
breaking user installations.

### II. Entity State and Data Model Adherence

All entities MUST adhere to Home Assistant's entity state patterns and data models.

- MUST use appropriate entity platforms (sensor, binary_sensor, switch, etc.)
- Entity state MUST conform to HA's state machine patterns
- Attributes MUST follow HA naming conventions (snake_case)
- MUST implement proper state restoration where applicable
- Entity unique IDs MUST be stable across restarts and updates
- Device classes and state classes MUST be used appropriately

**Rationale**: Consistent entity implementation ensures integrations work predictably
with HA automations, dashboards, and voice assistants. Deviations break user workflows.

### III. Config Flow Implementation

All configuration MUST be implemented through proper config flow with user-friendly UI.

- MUST implement ConfigFlow for user-facing configuration
- MUST provide clear, descriptive step titles and descriptions
- MUST validate user input with helpful error messages
- Options flow SHOULD be implemented for runtime configuration changes
- MUST handle connection errors gracefully with actionable feedback
- Multi-step flows MUST maintain state correctly

**Rationale**: Config flow is HA's standard for integration setup. Proper implementation
ensures users can configure integrations without YAML editing and provides a consistent
experience.

### IV. Discovery and Diagnostics Support

Integration MUST properly support Home Assistant's discovery and diagnostics frameworks.

- SHOULD implement SSDP, Zeroconf, or DHCP discovery where applicable
- MUST implement diagnostics for troubleshooting (redacting sensitive data)
- MUST provide meaningful debug logging at appropriate levels
- Repair flows SHOULD be implemented for recoverable issues
- MUST handle service unavailability gracefully without spamming logs

**Rationale**: Discovery improves user experience by auto-detecting devices. Diagnostics
enable effective troubleshooting without exposing sensitive information. These features
are expected in modern HA integrations.

### V. Release Compatibility

Integration MUST maintain compatibility with current stable Home Assistant releases.

- MUST support minimum HA version as declared in manifest.json
- Breaking changes MUST be documented and versioned appropriately
- Deprecated HA APIs MUST be updated proactively before removal
- MUST test against HA beta releases to catch breaking changes early
- SHOULD maintain backwards compatibility where reasonably possible

**Rationale**: Users expect integrations to work reliably with stable HA releases.
Proactive compatibility testing prevents integration failures during HA updates.

## Home Assistant Standards

This section captures specific Home Assistant technical requirements that all code
must meet.

### Manifest Requirements

- `manifest.json` MUST specify correct `version`, `domain`, and `requirements`
- `iot_class` MUST accurately reflect the integration's connectivity pattern
- `codeowners` MUST list active maintainers
- `quality_scale` SHOULD be targeted and maintained appropriately

### Async Implementation

- All I/O operations MUST be async
- MUST NOT block the event loop
- Coordinators MUST be used for data polling
- MUST implement proper async context managers for connections

### Error Handling

- MUST use HA's exception hierarchy appropriately
- ConfigEntryNotReady for temporary setup failures
- HomeAssistantError for runtime errors
- MUST NOT expose internal exceptions to users

## Development Workflow

### Code Review Requirements

- All PRs MUST pass automated linting (ruff)
- All PRs MUST include appropriate test coverage where applicable
- Breaking changes MUST be clearly documented in PR description
- UI strings MUST be localized (strings.json)

### Testing Gates

- Integration MUST run without errors in development environment
- Config flow MUST be tested for happy path and error cases
- Diagnostics output MUST be validated
- Entity states MUST be verified against expected values

### Deployment Approval

- HACS compatibility MUST be verified before release
- Changelog MUST be updated for each release
- Version numbers MUST follow semantic versioning

## Governance

This constitution supersedes all other development practices for the ha-unraid project.
All contributions MUST comply with these principles.

### Amendment Procedure

1. Proposed amendments MUST be documented with rationale
2. Breaking changes to principles require MAJOR version bump
3. New principles or significant expansions require MINOR version bump
4. Clarifications and typo fixes require PATCH version bump

### Compliance Review

- All PRs and code reviews MUST verify compliance with these principles
- Complexity that violates principles MUST be explicitly justified
- Violations without justification MUST be corrected before merge

### Versioning Policy

This constitution follows semantic versioning:
- MAJOR: Principle removals or backward-incompatible redefinitions
- MINOR: New principles added or materially expanded guidance
- PATCH: Clarifications, wording improvements, non-semantic refinements

**Version**: 1.0.0 | **Ratified**: 2025-12-23 | **Last Amended**: 2025-12-23
