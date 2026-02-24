---
applyTo: "**/*.py"
---

# Python Code Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## File Organization

1. Module docstring
2. `from __future__ import annotations`
3. Standard library imports
4. Third-party imports (homeassistant, unraid_api, etc.)
5. Local imports (from `.const`, `.coordinator`, etc.)
6. `TYPE_CHECKING` guarded imports
7. Module-level constants and logger

## Naming Conventions

- Classes: `Unraid` prefix (e.g., `UnraidSystemCoordinator`, `UnraidBaseEntity`)
- Constants: `UPPER_SNAKE_CASE` with `Final` type annotation
- Private methods: `_underscore_prefix`
- Logger: `_LOGGER = logging.getLogger(__name__)`

## Type Annotations

- Always use `from __future__ import annotations`
- Type hints on all public functions
- Use `TYPE_CHECKING` guard for imports used only in annotations
- Union types: `str | None` (not `Optional[str]`)
- Coordinator data: `data: UnraidSystemData | None = self.coordinator.data`

## Async Patterns

- All I/O must be async (`await`)
- Never use blocking calls in async context
- Use `async_get_clientsession(hass)` for HTTP sessions
- Catch specific exceptions, never bare `except:`

## Error Handling

```python
# Coordinator: re-raise as HA exceptions
except UnraidAuthenticationError as err:
    raise ConfigEntryAuthFailed(...) from err
except (UnraidConnectionError, UnraidTimeoutError) as err:
    raise UpdateFailed(...) from err

# Entity actions: wrap in HomeAssistantError with translations
except Exception as err:
    raise HomeAssistantError(
        translation_domain=DOMAIN,
        translation_key="...",
        translation_placeholders={"error": str(err)},
    ) from err
```

## ha-unraid Specifics

- API data comes as Pydantic v2 models from `unraid-api` library
- Enum values from API: compare with `.upper()` for case insensitivity
- Constants live in `const.py` — don't hardcode values
- Use `entry.runtime_data` (not `hass.data[DOMAIN]`) for runtime data access
