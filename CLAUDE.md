# ha-unraid Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-23

## Active Technologies
- Python 3.12+ (Home Assistant 2025.6+ requirement) + homeassistant, unraid-api>=1.3.1, aiohttp (for session injection), pydantic v2 (001-unraid-api-migration)
- N/A (no local storage, data fetched from Unraid server via API) (001-unraid-api-migration)

- Python 3.12+ (Home Assistant 2025.6+ requirement) + homeassistant, aiohttp (GraphQL over HTTPS), pydantic v2 (data validation) (001-unraid-graphql-integration)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12+ (Home Assistant 2025.6+ requirement): Follow standard conventions

## Recent Changes
- 001-unraid-api-migration: Added Python 3.12+ (Home Assistant 2025.6+ requirement) + homeassistant, unraid-api>=1.3.1, aiohttp (for session injection), pydantic v2

- 001-unraid-graphql-integration: Added Python 3.12+ (Home Assistant 2025.6+ requirement) + homeassistant, aiohttp (GraphQL over HTTPS), pydantic v2 (data validation)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
