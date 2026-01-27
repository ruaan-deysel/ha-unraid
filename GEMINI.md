# Home Assistant Unraid Integration (`ha-unraid`)

## Project Overview

This is a **Home Assistant custom integration** that allows monitoring and control of Unraid servers.
It connects to Unraid servers using the **GraphQL API** (introduced in Unraid 7.2.0).

*   **Domain:** `unraid`
*   **Language:** Python 3.13+
*   **Core Dependency:** `unraid-api` (Python client library)
*   **Communication:** GraphQL over HTTP/HTTPS (local polling)

### Key Features
*   **System Monitoring:** CPU, Memory, Uptime, Temperatures.
*   **Storage:** Array status, Disk health/usage, Parity check status.
*   **Control:** Start/Stop Docker containers and VMs.
*   **Power:** UPS monitoring (battery, load, power).
*   **Notifications:** Unraid system notifications.

## Architecture

The integration follows the standard Home Assistant component structure:

*   **`custom_components/unraid/`**: The core integration code.
    *   `__init__.py`: Setup and teardown logic, including the `UnraidRuntimeData` class.
    *   `config_flow.py`: Handles the UI setup (user inputs API key/Host).
    *   `coordinator.py`: Implements `DataUpdateCoordinator` to fetch data from the Unraid API efficiently. There are likely separate coordinators for system (fast poll) and storage (slow poll) data.
    *   `sensor.py`, `binary_sensor.py`, `switch.py`, `button.py`: Entity implementations.
    *   `manifest.json`: Metadata for Home Assistant.
*   **`tests/`**: Pytest-based test suite.
*   **`scripts/`**: Helper scripts for development tasks.

## Development Workflow

### Prerequisites
*   `uv` (for package management)
*   Docker (for running Home Assistant via Dev Container or `scripts/develop`)

### Setup
The project uses `uv` to manage dependencies.

```bash
./scripts/setup
```

This will:
1.  Install `uv` (if missing).
2.  Install dependencies into a virtual environment (`.venv`).
3.  Install `pre-commit` hooks.

### Linting & Formatting
Strict code quality is enforced using `ruff`.

```bash
./scripts/lint
```
*   Runs `ruff format` and `ruff check --fix`.
*   **Rule:** Code must pass linting with zero warnings before committing.

### Testing
Tests use `pytest` and `pytest-homeassistant-custom-component`.

```bash
pytest
```
*   **Fixtures:** Common test data (system info, storage data) is generated via helpers in `tests/conftest.py` (e.g., `make_system_data`, `make_storage_data`).
*   **Mocking:** The Unraid API client is mocked in tests to avoid real network calls.

### Running a Dev Instance
To start a standalone Home Assistant instance with this integration loaded:

```bash
./scripts/develop
```
*   Config is stored in `config/`.
*   `custom_components/` is added to `PYTHONPATH`.

## Contribution Guidelines

*   **Branching:** Create feature branches from `main`.
*   **Style:** Follow existing patterns (typed Python, async/await).
*   **Testing:** Add tests for new features. Ensure coverage remains high.
*   **Commits:** Write clear commit messages.

## Useful Paths

*   **Manifest:** `custom_components/unraid/manifest.json`
*   **Constants:** `custom_components/unraid/const.py`
*   **Translations:** `custom_components/unraid/translations/en.json`
*   **Test Fixtures:** `tests/fixtures/` & `tests/conftest.py`
