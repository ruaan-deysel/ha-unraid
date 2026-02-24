---
applyTo: "custom_components/unraid/manifest.json"
---

# Manifest Guidelines — ha-unraid

Refer to [`AGENTS.md`](/AGENTS.md) for full project documentation.

## Current Manifest

```json
{
  "domain": "unraid",
  "name": "Unraid",
  "codeowners": ["@ruaan-deysel"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/ruaan-deysel/ha-unraid",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/ruaan-deysel/ha-unraid/issues",
  "requirements": ["unraid-api>=1.5.0"],
  "version": "YYYY.M.P"
}
```

## Rules

- **version**: CalVer format `YYYY.M.patch` (e.g., `2026.2.3`)
- **requirements**: Only list PyPI packages needed at runtime (not dev deps)
- **iot_class**: Must be `local_polling` (integration polls local server)
- **config_flow**: Must be `true` (UI-only setup, no YAML)
- **domain**: Must be `unraid` — never change this
- **codeowners**: GitHub usernames of maintainers
- Do not add `homeassistant` or its dependencies to `requirements` — HA provides them
- Adding new requirements requires review — ask first
