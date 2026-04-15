---
applyTo: "custom_components/unraid/config_flow.py"
---

# Config Flow Guidelines — ha-unraid

Refer to `AGENTS.md` for full project documentation.

## Flow Steps

- **`async_step_user`**: Initial setup — host, port, API key input
- **`async_step_reauth_confirm`**: Re-authentication when API key changes
- **`async_step_reconfigure`**: Change host/port/SSL after initial setup

## SSL Auto-Detection

The config flow delegates protocol probing to `unraid-api` and retries with
`verify_ssl=False` when certificate verification fails:

```python
try:
    await api_client.test_connection()
except CannotConnectError as err:
    if "ssl" in str(err).lower() or "certificate" in str(err).lower():
        api_client = UnraidClient(..., verify_ssl=False, session=session)
        await api_client.test_connection()
```

## Version Checking

Enforce API version compatibility before accepting configuration:

```python
server_info = await api_client.get_server_info()
# Compare server_info.api_version against MIN_API_VERSION
```

The integration checks the GraphQL API version from `get_server_info()` against
`MIN_API_VERSION` from `unraid-api`. No Unraid OS version requirement — the API
is upgradeable independently via the Unraid Connect plugin.

## Options Flow

`OptionsFlowWithReload` handles UPS capacity/power settings:

- `CONF_UPS_CAPACITY_VA` — UPS VA rating (0 = informational only)
- `CONF_UPS_NOMINAL_POWER` — Nominal power in watts (0 = disabled)

## Error IDs

Return string error IDs (not exceptions) to the UI:

- `required` — Missing host/API key
- `invalid_hostname` — Host exceeds max length
- `cannot_connect` — Connection failed
- `invalid_auth` — Bad API key
- `unknown` — Unexpected error
- `unsupported_version` — Unraid/API too old

## Abort Reasons

- `already_configured` — Duplicate server detected by unique ID
- `reauth_successful` — Returned by `async_step_reauth_confirm` on success via `self.async_update_reload_and_abort(...)`
- `no_options_available` — Returned by options flow when UPS options are not applicable

## Unique Config Entry

Set unique ID from server UUID (or fallback host) during `async_step_user`:

```python
unique_id = self._server_uuid or user_input[CONF_HOST]
await self.async_set_unique_id(unique_id)
self._abort_if_unique_id_configured()
```

`async_step_reauth_confirm` and `async_step_reconfigure` update existing entries
via `_get_reauth_entry()` / `_get_reconfigure_entry()`.

## Validation

- Hostname: max 253 chars
- Port: 1–65535
- API key: non-empty string
- Use `vol.Schema` with `voluptuous` validators

## Repair Issues

Reauth success should clear the auth repair issue created by runtime logic:

```python
ir.async_delete_issue(self.hass, DOMAIN, REPAIR_AUTH_FAILED)
```
