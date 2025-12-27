# Quickstart: Unraid GraphQL Integration Development

**Date**: 2025-12-23
**Feature**: 001-unraid-graphql-integration

## Prerequisites

- Python 3.12+
- Docker Desktop (for devcontainer)
- VS Code with Dev Containers extension
- Unraid 7.2+ server with GraphQL API enabled

## Development Environment Setup

### 1. Clone and Open in Devcontainer

```bash
git clone https://github.com/ruaan-deysel/ha-unraid.git
cd ha-unraid
git checkout 001-unraid-graphql-integration
code .
```

When VS Code opens, click "Reopen in Container" or use `Ctrl+Shift+P` → "Dev Containers: Reopen in Container".

### 2. Install Dependencies

The devcontainer automatically runs setup, but if needed:

```bash
scripts/setup
```

### 3. Enable GraphQL API on Unraid

1. Open Unraid WebGUI: `https://your-unraid-server`
2. Navigate to: **Settings → Management Access → Developer Options**
3. Enable **GraphQL Sandbox**
4. Navigate to: **Settings → Management Access → API**
5. Click **Create API Key**
   - Name: `HomeAssistant`
   - Role: `ADMIN`
6. Copy the generated API key

### 4. Test GraphQL Connection

Visit `https://your-unraid-server/graphql` in your browser to access the GraphQL Sandbox.

Test query:
```graphql
query {
  info {
    versions {
      unraid
    }
  }
}
```

## Running Home Assistant

### Start Development Server

```bash
scripts/develop
```

Access Home Assistant at: `http://localhost:8123`

### Add the Integration

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for "Unraid"
4. Enter:
   - Host: Your Unraid server IP/hostname
   - API Key: The key created above
   - Port: 443 (or your custom port)

## Project Structure

```
custom_components/unraid/
├── __init__.py          # Integration setup
├── manifest.json        # Integration metadata
├── config_flow.py       # UI configuration
├── coordinator.py       # Data polling
├── const.py             # Constants
├── api/
│   ├── client.py        # GraphQL client
│   ├── queries.py       # Query definitions
│   └── models.py        # Pydantic models
├── sensor.py            # Sensor entities
├── switch.py            # Switch entities
├── binary_sensor.py     # Binary sensors
└── diagnostics.py       # Diagnostics

tests/
├── conftest.py          # Test fixtures
├── test_config_flow.py
└── test_api/
```

## Development Workflow

### 1. Code Changes

Edit files in `custom_components/unraid/`. Hot reload is not available; restart Home Assistant to see changes.

### 2. Lint and Format

```bash
scripts/lint
```

### 3. Run Tests

```bash
pytest tests/
```

### 4. View Logs

In Home Assistant: **Settings → System → Logs**

Filter by `custom_components.unraid` for integration-specific logs.

## Key Implementation Notes

### GraphQL Client

Use `aiohttp` for async HTTP requests:

```python
async with aiohttp.ClientSession() as session:
    async with session.post(
        f"https://{host}/graphql",
        headers={"x-api-key": api_key},
        json={"query": QUERY},
        ssl=ssl_context
    ) as response:
        data = await response.json()
```

### Pydantic Models

Use `extra="ignore"` for forward compatibility:

```python
from pydantic import BaseModel, ConfigDict

class SystemInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    uptime: int
    cpu_usage: float
```

### DataUpdateCoordinator

Two coordinators with different intervals:

```python
# System data - 30 second polling
class UnraidSystemCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client, update_interval=30):
        super().__init__(
            hass,
            _LOGGER,
            name="Unraid System",
            update_interval=timedelta(seconds=update_interval),
        )

# Storage data - 5 minute polling
class UnraidStorageCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client, update_interval=300):
        ...
```

### Entity Unique IDs

Pattern: `{server_uuid}_{resource_id}`

```python
@property
def unique_id(self) -> str:
    return f"{self.coordinator.server_uuid}_{self._container_id}"
```

## Testing with Mock Data

Create test fixtures in `tests/conftest.py`:

```python
@pytest.fixture
def mock_system_data():
    return {
        "info": {
            "os": {"uptime": 86400},
            "cpu": {"brand": "Intel"},
            "memory": {"total": 32000000000, "used": 16000000000}
        }
    }
```

## Troubleshooting

### Connection Refused

- Verify Unraid server is accessible from HA
- Check port is correct (default: 443)
- Ensure HTTPS is enabled on Unraid

### Invalid API Key

- Regenerate API key in Unraid WebGUI
- Ensure key has ADMIN role

### SSL Certificate Error

- For self-signed certs, may need to disable SSL verification in dev
- Production should use valid certs or HA's trust store

### No Entities Created

- Check logs for GraphQL errors
- Verify API returns data in GraphQL Sandbox
- Ensure Unraid version is 7.2+

## Useful Commands

```bash
# Format code
scripts/lint

# Run specific test
pytest tests/test_config_flow.py -v

# Run with coverage
pytest --cov=custom_components/unraid tests/

# Check Home Assistant config
hass --config ./config --script check_config
```

## Next Steps

After development environment is set up:

1. Implement `api/client.py` - GraphQL client
2. Implement `api/models.py` - Pydantic models
3. Implement `config_flow.py` - User configuration
4. Implement `coordinator.py` - Data polling
5. Implement entity platforms (sensor, switch, binary_sensor)
6. Add diagnostics support
7. Write tests

See `tasks.md` for detailed implementation tasks.
