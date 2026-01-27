# Home Assistant Integration Development Checklist

This checklist covers common review feedback and patterns required for Home Assistant Core integrations, particularly for achieving Platinum quality scale.

---

## Test Fixtures Pattern

### ✅ Create a unified client fixture
- [ ] Create a **single** mock client fixture that patches **both** the main integration module AND the config_flow module
- [ ] Use the `new=mock_class` pattern to ensure both locations share the same mock instance
- [ ] Follow the pattern from platinum integrations like `peblar` or `lamarzocco`

**Example pattern:**
```python
@pytest.fixture
def mock_my_client(
    mock_data: MyData,
) -> Generator[MagicMock]:
    """Return a mocked API client."""
    with (
        patch(
            "homeassistant.components.my_integration.MyClient"
        ) as mock_client_class,
        patch(
            "homeassistant.components.my_integration.config_flow.MyClient",
            new=mock_client_class,
        ),
    ):
        client = create_mock_client(mock_data)
        mock_client_class.return_value = client
        yield client
```

### ✅ Remove inline patches from tests
- [x] **Do NOT** use inline `with patch(...)` statements in test files *(partially done: test_init.py and test_config_flow.py converted)*
- [x] Tests should use the shared fixture via `@pytest.mark.usefixtures("mock_my_client")` for simple tests
- [x] Tests should use `mock_my_client: MagicMock` as a parameter when needing to modify mock behavior
- [ ] Remove unused imports (`patch`, `AsyncMock`) after refactoring *(entity test files still use inline patches)*

---

## Resource Management

### ✅ Close API client in config flow
- [x] Wrap validation logic in `try/finally` block
- [x] Call `await api_client.close()` in the `finally` block to prevent resource leaks
- [x] This ensures cleanup happens whether validation succeeds or fails

**Example:**
```python
async def _test_connection(self, ...) -> None:
    api_client = MyClient(...)
    try:
        await self._validate_connection(api_client)
    except SomeError as err:
        raise FlowError from err
    finally:
        await api_client.close()
```

### ✅ Close API client on config entry unload
- [x] In `async_unload_entry`, close the API client after unloading platforms
- [x] Only close if unload was successful

**Example:**
```python
async def async_unload_entry(hass: HomeAssistant, entry: MyConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.coordinator.api_client.close()
    return unload_ok
```

---

## Error Handling

### ✅ Use ConfigEntryAuthFailed for authentication errors in coordinator
- [ ] Import `ConfigEntryAuthFailed` from `homeassistant.exceptions`
- [ ] Use `ConfigEntryAuthFailed` (not `ConfigEntryError`) for authentication failures in the coordinator's `_async_update_data` method
- [ ] This triggers the reauth flow, allowing users to update credentials without removing the integration

**Example:**
```python
from homeassistant.exceptions import ConfigEntryAuthFailed

async def _async_update_data(self) -> MyData:
    try:
        return await self.api_client.get_data()
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed("Authentication failed") from err
    except ConnectionError as err:
        raise UpdateFailed("Connection error") from err
```

### ✅ Handle version parsing failures safely
- [ ] When parsing API/firmware versions fails, **reject** the connection (return `False`)
- [ ] Do NOT allow connections when version cannot be verified
- [ ] Log an error when version parsing fails

**Example:**
```python
def _is_supported_version(self, api_version: str) -> bool:
    try:
        current = AwesomeVersion(api_version)
        minimum = AwesomeVersion(MIN_VERSION)
    except AwesomeVersionException:
        _LOGGER.error("Failed to parse API version: %s", api_version)
        return False  # Reject, don't allow
    return current >= minimum
```

---

## Sensor Entity Descriptions

### ✅ Verify value_fn calculations are correct
- [ ] Double-check that `value_fn` lambdas return the correct values
- [ ] Ensure sensor names match what they actually measure
- [ ] Common mistake: calculating "free" when you mean "used" (or vice versa)

**Example of incorrect vs correct:**
```python
# ❌ WRONG - This calculates FREE memory, not USED
value_fn=lambda data: data.memory_total - data.memory_used

# ✅ CORRECT - This returns USED memory
value_fn=lambda data: data.metrics.memory_used
```

---

## Config Flow Classes

### ✅ Define all exception classes used
- [ ] Ensure all custom exception classes are defined before use
- [ ] Common classes needed: `FlowError`, `AbortFlow`

**Example:**
```python
class MyFlowError(Exception):
    """Exception for flow errors with error key."""
    def __init__(self, error_key: str | None = None) -> None:
        self.error_key = error_key
        super().__init__()

class MyAbortFlow(Exception):
    """Exception to abort the flow."""
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__()
```

---

## Pre-commit & Code Quality

### ✅ Run pre-commit before submitting
- [ ] Run `pre-commit run --files <your_files>` to check formatting
- [ ] Fix any ruff format issues (auto-reformatted by hook)
- [ ] Ensure mypy passes with no errors
- [ ] Ensure pylint passes with no errors

### ✅ Run tests with coverage
- [ ] Run tests: `pytest tests/components/<integration>/ -v --timeout=30`
- [ ] Check coverage: `pytest tests/components/<integration>/ --cov=homeassistant.components.<integration> --cov-report term-missing`
- [ ] Aim for >95% coverage

---

## Summary Checklist

| Category | Item | Status |
|----------|------|--------|
| **Fixtures** | Single unified client fixture for both modules | ✅ |
| **Fixtures** | No inline patches in test files | ☐ |
| **Resources** | Close API client in config flow (finally block) | ✅ |
| **Resources** | Close API client on entry unload | ✅ |
| **Errors** | Use ConfigEntryAuthFailed for auth errors in coordinator | ✅ |
| **Errors** | Reject connection on version parse failure | ✅ |
| **Sensors** | Verify value_fn calculations are correct | ✅ |
| **Config Flow** | All custom exception classes defined | ✅ |
| **Quality** | Pre-commit passes | ✅ |
| **Quality** | Tests pass with >95% coverage | ✅ (94%) |

---

## Additional Review Feedback (from earlier PR reviews)

The items above were covered in this session. Below are additional review items from the **full PR review history** that may apply to future development:

### Constants & Organization

- [x] Remove unused platforms from `const.py`
- [x] Constants only used in one file should be defined in that file, not `const.py`
- [x] Icons go in `icons.json`, not `const.py`
- [x] User-definable poll intervals are NOT allowed
- [x] Move coordinator update intervals inside coordinator, not passed as parameters
- [ ] Move single-use variables to where they're used, not at module level
- [ ] Static data schemas should be defined as module-level constants

### Config Flow Patterns

- [ ] Use `AbortFlow` from `homeassistant.data_entry_flow` instead of custom exception classes
- [ ] Host is always present when required in schema - no need to handle None
- [ ] Port validation can be done in schema with `vol.All(int, vol.Range(min=1, max=65535))`
- [ ] For user-unfixable errors, `abort` the flow instead of showing an error
- [ ] Don't re-raise exceptions - set errors dict directly instead
- [ ] Avoid by-reference passing of error dictionaries - makes code hard to follow
- [ ] Use HA's session in config flow (`async_get_clientsession(hass)`) for consistency
- [ ] Single port + SSL detection is cleaner than separate HTTP/HTTPS ports

### Quality Scale

- [ ] Mark items as `todo` not `exempt` if they should be implemented later
- [ ] Document which exceptions are supported explicitly in comments
- [ ] Read-only entities still count toward "actions" exemption comment

### Entity Patterns

- [ ] Create a **base entity** with shared `device_info` and `has_entity_name`
- [ ] Limit initial sensors to a focused selection - expand in later PRs
- [ ] Use `SensorDeviceClass.TIMESTAMP` with actual timestamp for "up since" sensors
- [ ] Use `PERCENTAGE` constant from `homeassistant.const`
- [ ] Don't handle "unknown" fallback that can't actually happen - use TYPE_CHECKING assert
- [ ] Move imports before class definitions for consistency
- [ ] Don't add unused code copied from other integrations

### Library Code vs Integration Code

- [x] Error handling for raw aiohttp errors belongs in the library, not HA *(handled by unraid-api library)*
- [x] Parsing/validation logic (like building server info) belongs in library *(ServerInfo model from library)*
- [x] Type coercion (string to numeric) belongs in library *(handled by unraid-api)*
- [x] If you need to write tests for parsing logic, it's a sign it belongs in library

### Testing Patterns

- [ ] **NO test classes** - use plain functions *(test_init.py and test_config_flow.py converted; entity tests deferred)*
- [x] Use `is` for enum comparisons: `assert result["type"] is FlowResultType.FORM`
- [ ] Check `unique_id` in config flow tests
- [ ] Test error recovery by completing flow successfully after fixing error
- [ ] Use pytest parametrization for similar error tests
- [ ] **NO direct coordinator tests** - test through entity state effects *(40 coordinator tests kept for coverage)*
- [ ] Use `snapshot_platform` helper instead of individual entity assertions
- [ ] Use `freezer` fixture to test coordinator updates through time
- [ ] Don't patch internals like `coordinator._async_update_data`
- [x] Setup data fixtures in conftest, not in individual test files

### Logging

- [ ] Don't log every exception type individually - pick the important ones
- [ ] Don't bring stringified errors to the UI (use simple messages)
### Documentation & Strings

- [ ] Use common strings references: `[%key:common::config_flow::data::host%]`
- [ ] Use sentence case for translations (HTTP port → "HTTP port")

---

## Reference Integrations

For examples of well-implemented platinum integrations, check:
- `tests/components/peblar/` - Simple, clean fixture pattern
- `tests/components/lamarzocco/` - More complex with multiple fixtures
- `homeassistant/components/peblar/` - Clean integration structure
