---
applyTo: "custom_components/unraid/repairs.py"
---

# Repairs Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## Purpose

`repairs.py` implements HA's repair flows — interactive dialogs that guide users through fixing integration issues (e.g., expired API key).

## Architecture

```
ir.async_create_issue() → User clicks "Fix" → async_create_fix_flow() → RepairsFlow subclass
```

## Current Repair Flows

- **`AuthFailedRepairFlow`** — Triggered when API key is invalid. Redirects user to reauth config flow.

## Creating a New Repair Flow

1. Define a `RepairsFlow` subclass with `async_step_init` and confirmation steps
2. Register it in `async_create_fix_flow()` dispatcher
3. Add the issue ID constant to `const.py` (e.g., `REPAIR_AUTH_FAILED`)
4. Add translation keys to `strings.json` under `issues.{issue_id}`
5. Create the issue with `ir.async_create_issue()` where the error is detected

## Pattern

```python
class MyRepairFlow(RepairsFlow):
    async def async_step_init(self, user_input=None) -> FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None) -> FlowResult:
        if user_input is not None:
            # Perform fix action
            return self.async_create_entry(data={})
        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))
```

## Rules

- Repair flows must be `is_fixable=True` to show the "Fix" button
- Use `is_persistent=True` for issues that survive restarts
- Clear issues on resolution: `ir.async_delete_issue(hass, DOMAIN, issue_id)`
- Always provide `translation_key` and `translation_placeholders`
