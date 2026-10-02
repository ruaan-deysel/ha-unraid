# Copyright (c) 2026 Ruaan Deysel

"""Tests for serving Unraid dashboard cards."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.core import HomeAssistant

from custom_components.unraid import async_setup, frontend
from custom_components.unraid.frontend import (
    CARD_FILES,
    FRONTEND_PATH,
    FRONTEND_URL_BASE,
    _frontend_digest,
    async_register_frontend,
)

MANIFEST = Path(frontend.__file__).parent / "manifest.json"


def _expected_urls() -> dict[str, str]:
    version = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
    digest = _frontend_digest(FRONTEND_PATH)
    urls: dict[str, str] = {}
    for filename in CARD_FILES:
        path = FRONTEND_PATH / filename
        if not path.is_file():
            continue
        base = f"{FRONTEND_URL_BASE}/{filename}"
        urls[base] = f"{base}?v={version}-{digest}"
    return urls


class FakeResources:
    """A storage resource collection with the Home Assistant CRUD contract."""

    def __init__(self, items: list[dict] | None = None) -> None:
        """Initialize fake resources."""
        self.items = items or []
        self.async_get_info = AsyncMock(return_value={"resources": len(self.items)})
        self.async_create_item = AsyncMock(side_effect=self._create)
        self.async_update_item = AsyncMock(side_effect=self._update)
        self.async_delete_item = AsyncMock(side_effect=self._delete)

    def async_items(self) -> list[dict]:
        """Return loaded resources."""
        return list(self.items)

    def _create(self, data: dict) -> dict:
        item = {
            "id": f"res-{len(self.items)}",
            "url": data["url"],
            "type": data["res_type"],
        }
        self.items.append(item)
        return item

    def _update(self, item_id: str, data: dict) -> dict:
        item = next(it for it in self.items if it["id"] == item_id)
        item.update(url=data["url"], type=data["res_type"])
        return item

    def _delete(self, item_id: str) -> None:
        self.items = [it for it in self.items if it["id"] != item_id]


@pytest.fixture
def http(hass: HomeAssistant):
    """Pretend the web components are loaded with a storage dashboard."""
    mock = MagicMock()
    mock.async_register_static_paths = AsyncMock()
    hass.http = mock
    hass.config.components.update({"http", "frontend", "lovelace"})
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=FakeResources())
    return mock


async def test_registers_bundle_once(
    hass: HomeAssistant, http: MagicMock, enable_custom_integrations: None
) -> None:
    """The static path and the Lovelace module resources register once."""
    expected = _expected_urls()
    with (
        patch.object(frontend, "ResourceStorageCollection", FakeResources),
        patch.object(frontend, "add_extra_js_url") as add_js,
    ):
        await async_register_frontend(hass)
        await async_register_frontend(hass)

    http.async_register_static_paths.assert_awaited_once()
    (configs,) = http.async_register_static_paths.await_args.args
    assert [(c.url_path, c.path, c.cache_headers) for c in configs] == [
        (FRONTEND_URL_BASE, str(FRONTEND_PATH), False)
    ]
    resources = hass.data[LOVELACE_DATA].resources
    assert [item["url"] for item in resources.items] == list(expected.values())
    assert resources.async_create_item.await_count == len(expected)
    add_js.assert_not_called()


async def test_updates_resource_when_bundle_changes(
    hass: HomeAssistant, http: MagicMock, enable_custom_integrations: None
) -> None:
    """Resource entries are updated when digest differs."""
    stale_url = f"{FRONTEND_URL_BASE}/unraid-cards.js?v=old"
    resources = FakeResources([{"id": "res-0", "url": stale_url, "type": "module"}])
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=resources)

    with patch.object(frontend, "ResourceStorageCollection", FakeResources):
        await async_register_frontend(hass)

    assert any("unraid-cards.js" in item["url"] for item in resources.items)
    resources.async_update_item.assert_awaited()


async def test_deletes_stale_bundle_resources_on_upgrade(
    hass: HomeAssistant, http: MagicMock, enable_custom_integrations: None
) -> None:
    """Stale individual bundle entries from earlier releases are deleted."""
    stale_resources = [
        {
            "id": "res-old-server",
            "url": f"{FRONTEND_URL_BASE}/unraid-server-card.js?v=old",
            "type": "module",
        },
        {
            "id": "res-old-storage",
            "url": f"{FRONTEND_URL_BASE}/unraid-storage-card.js",
            "type": "module",
        },
        {
            "id": "res-unrelated",
            "url": "/hacsfiles/custom-card/card.js",
            "type": "module",
        },
    ]
    resources = FakeResources(stale_resources)
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=resources)

    with patch.object(frontend, "ResourceStorageCollection", FakeResources):
        await async_register_frontend(hass)

    remaining_urls = [item["url"] for item in resources.items]
    assert not any("unraid-server-card.js" in url for url in remaining_urls)
    assert not any("unraid-storage-card.js" in url for url in remaining_urls)
    assert any("unraid-cards.js" in url for url in remaining_urls)
    assert any("/hacsfiles/custom-card/card.js" in url for url in remaining_urls)
    assert resources.async_delete_item.await_count == 2


async def test_skips_when_http_or_frontend_missing(hass: HomeAssistant) -> None:
    """Registration is skipped when http or frontend is not loaded."""
    hass.config.components = {"sensor"}
    mock_http = MagicMock()
    mock_http.async_register_static_paths = AsyncMock()
    hass.http = mock_http

    await async_register_frontend(hass)
    mock_http.async_register_static_paths.assert_not_called()


async def test_falls_back_to_extra_js_url_in_yaml_mode(
    hass: HomeAssistant, http: MagicMock, enable_custom_integrations: None
) -> None:
    """YAML mode falls back to add_extra_js_url."""
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=None)
    with patch.object(frontend, "add_extra_js_url") as add_js:
        await async_register_frontend(hass)

    assert add_js.call_count > 0


async def test_logs_error_on_exception(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    enable_custom_integrations: None,
) -> None:
    """Exceptions are logged and do not raise."""
    hass.config.components.update({"http", "frontend"})
    mock_http = MagicMock()
    mock_http.async_register_static_paths = AsyncMock(
        side_effect=RuntimeError("disk full")
    )
    hass.http = mock_http

    await async_register_frontend(hass)
    assert "Unable to register optional dashboard card frontend" in caplog.text
    assert not hass.data.get(frontend._REGISTERED)


def test_frontend_digest_helper(tmp_path: Path) -> None:
    """Test _frontend_digest handles valid, empty, and missing paths."""
    f = tmp_path / "test.js"
    f.write_text("console.log('hi');")
    sub = tmp_path / "chunks"
    sub.mkdir()
    f2 = sub / "chunk.js"
    f2.write_text("console.log('chunk');")
    digest = _frontend_digest(tmp_path)
    assert len(digest) == 8

    missing = tmp_path / "nonexistent"
    assert _frontend_digest(missing) == "none"

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert _frontend_digest(empty_dir) == "none"


async def test_async_setup_registers_frontend(
    hass: HomeAssistant, http: MagicMock, enable_custom_integrations: None
) -> None:
    """async_setup invokes async_register_frontend."""
    with patch("custom_components.unraid.async_register_frontend") as mock_reg:
        result = await async_setup(hass, {})
        assert result is True
        mock_reg.assert_awaited_once_with(hass)
