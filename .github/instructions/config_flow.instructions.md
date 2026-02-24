---
applyTo: "custom_components/unraid/config_flow.py"
---

# Config Flow Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## Flow Steps

- **`async_step_user`**: Initial setup — host, port, API key input
- **`async_step_reauth_confirm`**: Re-authentication when API key changes
- **`async_step_reconfigure`**: Change host/port/SSL after initial setup

## SSL Auto-Detection

The config flow tries HTTPS first, falls back to HTTP on `UnraidSSLError`:

```python
try:
    await client.test_connection()  # HTTPS
except UnraidSSLError:
    # Retry without SSL
    use_ssl = False
    client = UnraidClient(host=host, ..., verify_ssl=False)
    await client.test_connection()
```

## Version Checking

Enforce minimum versions before accepting configuration:

```python
MIN_API_VERSION = "4.21.0"
MIN_UNRAID_VERSION = "7.2.0"
```

Use `AwesomeVersion` for version comparison.

## Options Flow

`OptionsFlowWithReload` handles UPS capacity/power settings:

- `CONF_UPS_CAPACITY_VA` — UPS VA rating (0 = informational only)
- `CONF_UPS_NOMINAL_POWER` — Nominal power in watts (0 = disabled)

## Error IDs

Return string error IDs (not exceptions) to the UI:

- `cannot_connect` — Connection failed
- `invalid_auth` — Bad API key
- `timeout` — Connection timed out
- `unknown` — Unexpected error
- `already_configured` — Duplicate server
- `unsupported_version` — Unraid/API too old

## Abort Reasons

- `reauth_successful` — Returned by `async_step_reauth_confirm` on success via `self.async_update_reload_and_abort(...)`

## Unique Config Entry

Set unique ID from server UUID. The helper used after `async_set_unique_id` depends on which flow step is executing:

**`async_step_user`** (initial setup) — abort if already configured:

```python
info = await client.get_server_info()
await self.async_set_unique_id(info.uuid)
self._abort_if_unique_id_configured()
```

**`async_step_reauth_confirm` / `async_step_reconfigure`** — abort if UUID has changed (different server):

```python
info = await client.get_server_info()
await self.async_set_unique_id(info.uuid)
self._abort_if_unique_id_mismatch()
# On reauth success:
return self.async_update_reload_and_abort(
    self._get_reauth_entry(), data_updates={...}
)
```

## Validation

- Hostname: max 253 chars
- Port: 1–65535
- API key: non-empty string
- Use `vol.Schema` with `voluptuous` validators

## Repair Issues

Create repair issues for persistent auth failures:

```python
ir.async_create_issue(
    hass, DOMAIN, REPAIR_AUTH_FAILED,
    is_fixable=True, is_persistent=True,
    severity=ir.IssueSeverity.ERROR,
    translation_key="auth_failed",
)
```
