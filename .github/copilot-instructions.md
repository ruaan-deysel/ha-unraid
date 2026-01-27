# Home Assistant Unraid Integration - AI Agent Guidelines

## Code Quality Standards - ZERO TOLERANCE ⚠️

**🚨 CRITICAL - ABSOLUTE REQUIREMENT 🚨**: This project enforces ZERO TOLERANCE for code quality violations.

### MANDATORY LINTING POLICY

**EVERY SINGLE CODE CHANGE MUST:**
1. ✅ Run `./scripts/lint` IMMEDIATELY after any code modification
2. ✅ Achieve ZERO warnings (exit code 0)
3. ✅ Achieve ZERO errors (exit code 0)
4. ✅ Fix ALL issues before proceeding to next step
5. ✅ Re-run lint after fixes to confirm clean state

**NO EXCEPTIONS. NO EXCUSES. NO WORKAROUNDS.**

### Enforcement Rules

1. **Linting**:
   - Run `./scripts/lint` after EVERY code change - no exceptions
   - Exit code MUST be 0 (zero warnings, zero errors)
   - If lint shows ANY output beyond "All checks passed!", you MUST fix it
   - Never proceed to testing or committing with linting issues
   - Never add `# noqa` comments or ignore linting warnings

2. **Security**:
   - All security issues must be addressed immediately
   - Use latest security best practices
   - No hardcoded credentials or secrets
   - Validate all user inputs

3. **HA Standards**:
   - Follow latest Home Assistant development standards
   - Meet quality scale requirements for HACS
   - Use proper entity patterns and device classes

4. **Testing**:
   - All new code must have corresponding tests
   - Run `pytest` before committing
   - All tests must pass (100%)

5. **Type Safety**:
   - Use type hints for all functions
   - Pydantic models enforce runtime validation
   - No `Any` types without justification

6. **Dev Environment**:
   - Code must work in Home Assistant devcontainer
   - Test in devcontainer before committing
   - Use `./scripts/develop` for integration testing

### Workflow Mandate - STRICT SEQUENCE

```bash
# 1. Make code changes
# 2. IMMEDIATELY run lint (auto-fixes most issues)
./scripts/lint
# ↓ MUST show "All checks passed!" or STOP and fix issues ↓

# 3. Run tests to verify changes
pytest
# ↓ MUST show "X passed" with 0 failures or STOP and fix ↓

# 4. Test in live environment
./scripts/develop
```

### ❌ NEVER COMMIT CODE WITH

**AUTOMATIC REJECTION - No discussion, no exceptions:**
- ❌ ANY linting warnings (even "minor" ones)
- ❌ ANY linting errors
- ❌ Type hint violations
- ❌ Unhandled security vulnerabilities
- ❌ Missing tests for new functionality
- ❌ Deprecated Home Assistant APIs
- ❌ Code that fails in HA devcontainer environment
- ❌ Ignored lint warnings (`# noqa`, `# type: ignore` without justification)
- ❌ Non-zero exit code from `./scripts/lint`

### Verification Checklist

Before considering ANY code change complete:
- [ ] Code written
- [ ] `./scripts/lint` run → Exit code 0 ✅
- [ ] All warnings fixed (if any appeared)
- [ ] `./scripts/lint` re-run → Exit code 0 ✅ (confirm)
- [ ] `pytest` run → All tests pass ✅
- [ ] Changes tested in `./scripts/develop` ✅
- [ ] No new warnings in HA logs ✅

**If ANY checkbox is unchecked, code is NOT complete.**

## Project Overview

This is a **Home Assistant custom integration** for Unraid 7.2+ servers via the GraphQL API. The project is in active development (feature branch `001-unraid-graphql-integration`) implementing a complete rebuild from SSH-based monitoring to GraphQL-based real-time data access.

**Key Architecture Points:**
- **Domain**: `unraid` - all entities use this integration domain
- **Data Flow**: Dual coordinator pattern (30s for system metrics, 5min for storage/disks)
- **Data Validation**: Pydantic v2 models in [models.py](../custom_components/unraid/models.py) handle all API responses
- **Authentication**: HTTPS with `x-api-key` header to Unraid GraphQL endpoint
- **Entity IDs**: Format `{system_uuid}_{resource_id}` for stability across restarts

## Development Commands

**MANDATORY SCRIPTS** - Never bypass these:

```bash
# Initial setup - run once
./scripts/setup

# Format and lint code - RUN AFTER EVERY CODE CHANGE
./scripts/lint
# Uses ruff for formatting + linting with auto-fix enabled
# Exit code 0 = clean, non-zero = issues must be fixed

# Run tests - MUST PASS before committing
pytest
# Or run specific test file:
pytest tests/test_models.py

# Run Home Assistant locally - for integration testing
./scripts/develop
# CRITICAL: Sets PYTHONPATH to include custom_components/
# Never use bare `hass` command - will fail to load integration
```

**Development Workflow**:
1. Make code changes
2. **Immediately** run `./scripts/lint` - fix all issues before proceeding
3. Run `pytest` to verify tests pass
4. Use `./scripts/develop` to test in live Home Assistant instance
5. Commit only when lint shows zero issues and tests pass

**Script Details**:
- `./scripts/setup`: Installs dependencies from requirements.txt (homeassistant, pydantic, ruff)
- `./scripts/lint`: Runs `ruff format .` then `ruff check . --fix` (auto-fixes most issues)
- `./scripts/develop`: Exports PYTHONPATH and starts Home Assistant with debug logging

**Development Environment**:
- **Home Assistant Devcontainer**: All development MUST be compatible with HA devcontainer
- The devcontainer provides the official HA development environment
- Scripts must work both locally and in devcontainer
- Use VS Code's "Reopen in Container" for devcontainer development
- Never write code that only works in local environment

## MCP Server Usage - MANDATORY

**🔧 ALWAYS USE AVAILABLE MCP SERVERS**:

When working on this project, you MUST leverage available MCP (Model Context Protocol) servers for enhanced capabilities:

### Context7 (Library Documentation)
- **Purpose**: Fetch up-to-date documentation for Python libraries (Home Assistant, Pydantic, aiohttp, etc.)
- **When to use**:
  - Looking up Home Assistant API documentation
  - Checking Pydantic v2 syntax and patterns
  - Verifying aiohttp usage patterns
  - Understanding Home Assistant entity classes
  - Checking proper type hints and annotations
- **Example queries**:
  - "Home Assistant DataUpdateCoordinator API"
  - "Pydantic v2 ConfigDict options"
  - "aiohttp ClientSession with SSL verification"

### MCP Docker (Browser Automation)
- **Purpose**: Automated browser interactions and testing
- **When to use**:
  - Testing the integration's config flow UI
  - Verifying entity displays in Home Assistant web UI
  - Capturing screenshots of integration setup
  - Testing Options flow interactions
  - Validating error messages display correctly
- **Example use cases**:
  - Navigate to http://localhost:8123 and add integration
  - Screenshot entity states after setup
  - Test Docker container switch toggle
  - Verify diagnostics download

### Perplexity (Research & Reasoning)
- **Purpose**: Web research and complex problem reasoning
- **When to use**:
  - Researching Unraid API changes or new features
  - Understanding Home Assistant best practices
  - Investigating integration patterns from other projects
  - Solving complex architecture decisions
  - Finding security best practices

**RULE**: Before implementing new features or fixing complex issues, check if an MCP server can provide authoritative documentation or assist with testing. Don't rely solely on memory - use Context7 for current API documentation.

## Code Patterns & Conventions

### 1. Pydantic Models (Forward Compatibility)

All GraphQL response models inherit from `UnraidBaseModel` which ignores unknown fields:

```python
class UnraidBaseModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
```

**Why**: Unraid API may add new fields; integration must not break. Always use `Optional` types and provide defaults.

**Example** from [models.py](../custom_components/unraid/models.py):
```python
class InfoSystem(UnraidBaseModel):
    uuid: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
```

### 2. Datetime Parsing

Unraid returns ISO 8601 timestamps with trailing `Z`. Use the `_parse_datetime()` helper:

```python
@field_validator("time", mode="before")
@classmethod
def parse_time(cls, value):
    return _parse_datetime(value)
```

### 3. Entity Naming Convention

**Pattern**: `{platform}.{domain}_{server_hostname}_{resource_name}`
- ✅ `sensor.unraid_tower_cpu_usage`
- ✅ `switch.unraid_tower_plex`
- ❌ `sensor.cpu_usage` (missing domain prefix)

### 4. Enum Handling (Critical for Stability)

GraphQL enums may expand in future Unraid versions. Always handle unknown values gracefully:

**Anti-pattern**:
```python
if container.state == "RUNNING":  # Will break if new enum added
```

**Correct pattern** (see [data-model.md](../specs/001-unraid-graphql-integration/data-model.md)):
```python
# Known states
RUNNING_STATES = {"RUNNING", "IDLE"}
switch_on = container.state in RUNNING_STATES
# Unknown states default to OFF safely
```

## Testing Patterns

### Fixture-Based Tests

All mock API responses live in [tests/fixtures/](../tests/fixtures/). Example from [test_models.py](../tests/test_models.py):

```python
def load_json(name: str):
    return models.json_loads((FIXTURES / name).read_text())

payload = load_json("system_info.json")
```

When adding new GraphQL queries, create corresponding fixture files with realistic Unraid responses.

## Integration Architecture

### File Responsibilities

| File | Purpose | Key Point |
|------|---------|-----------|
| [\_\_init\_\_.py](../custom_components/unraid/__init__.py) | Entry point, coordinator setup | Currently minimal - setup logic goes here |
| [models.py](../custom_components/unraid/models.py) | Pydantic models for all GraphQL responses | Base class ignores unknown fields |
| [const.py](../custom_components/unraid/const.py) | Constants (domain, intervals, platform list) | `PLATFORMS` list drives entity loading |
| manifest.json | Integration metadata | Version, dependencies, codeowners |

### Coordinator Pattern (To Be Implemented)

From [plan.md](../specs/001-unraid-graphql-integration/plan.md):
- **UnraidSystemCoordinator**: 30s polling for metrics, Docker, VMs, UPS
- **UnraidStorageCoordinator**: 5min polling for array, disks, disk health

Why dual coordinators? Disk SMART queries are expensive; system metrics need responsiveness.

## Critical Specification References

**Must read before implementing**:
1. [spec.md](../specs/001-unraid-graphql-integration/spec.md) - User stories with acceptance criteria
2. [data-model.md](../specs/001-unraid-graphql-integration/data-model.md) - Complete enum documentation and state mappings
3. [contracts/queries.graphql](../specs/001-unraid-graphql-integration/contracts/queries.graphql) - Exact GraphQL queries (when created)

**Key Acceptance Criteria Examples**:
- Connection timeout: 30s for queries, 60s for mutations
- Error format: `"cannot_connect"`, `"invalid_auth"`, `"unsupported_version"` error IDs
- Minimum Unraid version: 7.2.0 (API v4.21.0+)

## Home Assistant Integration Requirements

### Config Flow

Must implement:
- **ConfigFlow**: Initial setup with host, API key validation
- **OptionsFlow**: Allow changing polling intervals after setup
- Error handling: Return error ID strings, not exceptions to user

### Entity Patterns

**Sensors**: Use appropriate `device_class` and `state_class`:
```python
device_class=SensorDeviceClass.DATA_SIZE  # For storage
state_class=SensorStateClass.MEASUREMENT  # For metrics
```

**Switches**: Docker/VM controls must:
1. Call GraphQL mutation
2. Wait for confirmation (up to 60s timeout)
3. Return state based on mutation response, not optimistic updates

### Diagnostics

Implement `async_get_config_entry_diagnostics()` to expose:
- Connection status
- Last successful poll times
- Coordinator data (redacted credentials)

## Security Requirements

**Authentication**:
- API keys stored in HA encrypted config entry storage ONLY
- Never log API keys or credentials
- Use `aiohttp.ClientSession` with SSL verification enabled by default
- Support custom CA certificates for self-signed certs

**Input Validation**:
- All GraphQL responses validated through Pydantic models
- Sanitize all user inputs in config flow
- Validate hostname/IP format before connection attempts

**Error Handling**:
- Never expose internal paths or credentials in error messages
- Use Home Assistant's exception hierarchy for proper error propagation
- Redact sensitive data in diagnostics output

## Home Assistant Best Practices (2025 Standards)

**Entity Design**:
- Use `device_class` and `state_class` for all sensors
- Set `entity_category` for diagnostic/config entities
- Provide `translation_key` for internationalization support
- Include `suggested_display_precision` for numeric sensors

**Async/Await Patterns**:
- Never block the event loop - use `async`/`await` exclusively
- Use `asyncio.gather()` for parallel operations
- Timeout all network calls (30s queries, 60s mutations)

**DataUpdateCoordinator**:
- Single coordinator per polling interval (dual coordinator pattern here)
- Handle `UpdateFailed` exceptions properly
- Implement exponential backoff for connection failures

**Config Flow**:
- Validate inputs before creating config entry
- Provide clear error messages with error IDs (e.g., "cannot_connect")
- Support options flow for runtime configuration changes

## Common Pitfalls

1. **Don't use blocking I/O**: All network calls must be `async`/`await`
2. **Don't store state in entities**: Use coordinator data as source of truth
3. **Don't hardcode enum values**: Unraid API evolves; use sets/mappings
4. **Don't skip unique_id**: Required for entity registry stability
5. **Test fixture data must be realistic**: Copy from actual Unraid API responses
6. **Don't bypass scripts**: Always use `./scripts/lint` - never commit with warnings
7. **Don't ignore type hints**: Ruff enforces type checking - add hints to all functions
8. **Don't use deprecated HA APIs**: Check HA dev docs for current patterns

## Quick Reference Links

- Current branch spec: [specs/001-unraid-graphql-integration/spec.md](../specs/001-unraid-graphql-integration/spec.md)
- Unraid GraphQL API: `https://your-server/graphql` (explore with GraphiQL in Unraid WebGUI)
- HA Integration docs: https://developers.home-assistant.io/docs/creating_integration_manifest
- Pydantic v2 docs: https://docs.pydantic.dev/latest/

## Current Status (As of 2025-12-23)

**Implemented**:
- ✅ Pydantic models for system info, metrics, array, Docker, VMs
- ✅ Base model with forward compatibility
- ✅ Test structure with fixtures
- ✅ Development/lint scripts

**In Progress**:
- 🚧 Config flow implementation
- 🚧 GraphQL API client
- 🚧 Coordinator setup

**Not Started**:
- ❌ Entity platforms (sensor, switch, binary_sensor)
- ❌ Diagnostics implementation
