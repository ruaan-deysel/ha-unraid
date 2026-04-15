---
applyTo: "custom_components/unraid/__init__.py,custom_components/unraid/config_flow.py,custom_components/unraid/coordinator.py"
---

# API Usage Guidelines — ha-unraid

Refer to `AGENTS.md` for full project documentation.

## Architecture Boundary

This integration uses the external `unraid-api` library rather than an in-repo
`api/` package.

Data flow must stay:

`Entities -> Coordinators -> UnraidClient (unraid-api) -> Unraid server`

- Entities read coordinator data only.
- Coordinators and config flow own API calls and exception mapping.
- Do not add direct network I/O in entities.

## UnraidClient Construction

- Always pass HA's shared session (`async_get_clientsession`).
- Never create ad-hoc synchronous network clients.
- Close temporary config-flow clients created for connection tests.

## Error Mapping Rules

- Auth failures -> `ConfigEntryAuthFailed` (coordinator) or `InvalidAuthError` (flow)
- Connectivity/timeouts -> `UpdateFailed` (coordinator) or `CannotConnectError` (flow)
- Version incompatibility -> `UnsupportedVersionError` in flow
- Wrap entity action failures in `HomeAssistantError` with translation keys

## Compatibility Checks

- Check API version from `get_server_info().api_version` against `MIN_API_VERSION` during config flow.
- No Unraid OS version requirement — the API is upgradeable independently via Unraid Connect.

## Dependency Management

- Current runtime dependency: `unraid-api>=1.6.0`.
- Dependency upgrades require review first.
- If upgraded, sync `manifest.json`, docs, and agent instructions in the same PR.
