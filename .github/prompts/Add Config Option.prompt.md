---
description: Add a new configuration option to the Unraid integration
---

# Add Config Option

Add a new option to the Unraid integration's options flow.

## Context

Read these files before starting:
- `AGENTS.md` — Full project documentation
- `custom_components/unraid/config_flow.py` — `UnraidOptionsFlowHandler` class
- `custom_components/unraid/const.py` — Configuration key constants
- `custom_components/unraid/strings.json` — Translation keys for options UI

## Steps

1. **Add constant** to `const.py`:
   ```python
   CONF_MY_OPTION: Final = "my_option"
   DEFAULT_MY_OPTION: Final = some_default
   ```

2. **Update options flow** in `config_flow.py`:
   - Add field to `vol.Schema` in `UnraidOptionsFlowHandler.async_step_init()`
   - Add default value handling from `self.config_entry.options.get()`

3. **Add translations** to `strings.json`:
   ```json
   "options": {
     "step": {
       "init": {
         "data": {
           "my_option": "My Option Label"
         },
         "data_description": {
           "my_option": "Description shown below the field"
         }
       }
     }
   }
   ```

4. **Use the option** where needed:
   ```python
   my_option = entry.options.get(CONF_MY_OPTION, DEFAULT_MY_OPTION)
   ```

5. **Test the option** in `tests/test_config_flow.py`

## Rules

- Options flow uses `OptionsFlowWithReload` — entry reloads automatically on save
- Use appropriate `vol` validators and selectors for the UI
- Provide `data_description` for user guidance
- Test both default values and user-provided values
