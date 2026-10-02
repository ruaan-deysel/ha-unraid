# Copyright (c) 2026 Ruaan Deysel

"""Serve the Lovelace dashboard card bundles from the integration."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Final

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http.server import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.loader import async_get_integration
from homeassistant.util.hass_dict import HassKey

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

FRONTEND_URL_BASE: Final = f"/{DOMAIN}"
FRONTEND_PATH: Final = Path(__file__).parent / "frontend"
CARD_FILES: Final = ("unraid-cards.js",)
_REGISTERED: HassKey[bool] = HassKey(f"{DOMAIN}_frontend_registered")
_STATIC_REGISTERED: HassKey[bool] = HassKey(f"{DOMAIN}_frontend_static_registered")


def _frontend_digest(path: Path) -> str:
    """Short content hash of all frontend assets for cache busting."""
    if not path.is_dir():
        return "none"
    hasher = hashlib.sha256()
    has_files = False
    for file_path in sorted(path.rglob("*.js")):
        if file_path.is_file():
            has_files = True
            hasher.update(file_path.relative_to(path).as_posix().encode())
            hasher.update(file_path.read_bytes())
    if not has_files:
        return "none"
    return hasher.hexdigest()[:8]


def _frontend_assets_info(path: Path, files: tuple[str, ...]) -> tuple[str, list[str]]:
    """Return content hash and existing entry filenames off the event loop."""
    digest = _frontend_digest(path)
    existing = [filename for filename in files if (path / filename).is_file()]
    return digest, existing


async def async_register_frontend(hass: HomeAssistant) -> None:
    """
    Serve card bundles and register them as Lovelace resources once.

    Called from async_setup, so it runs once per Home Assistant instance
    rather than once per config entry. Static assets are served without long-lived
    cache headers (cache_headers=False), while each resource URL carries the
    integration version plus a content hash of the frontend build so new releases
    or rebuilds under the same version reliably bust browser caches.
    """
    if hass.data.get(_REGISTERED):
        return
    if not {"http", "frontend"} <= hass.config.components:
        _LOGGER.debug("http/frontend not loaded; dashboard bundles not registered")
        return
    try:
        integration = await async_get_integration(hass, DOMAIN)
        if not hass.data.get(_STATIC_REGISTERED):
            await hass.http.async_register_static_paths(
                [
                    StaticPathConfig(
                        FRONTEND_URL_BASE, str(FRONTEND_PATH), cache_headers=False
                    )
                ]
            )
            hass.data[_STATIC_REGISTERED] = True

        urls: dict[str, str] = {}
        digest, existing_files = await hass.async_add_executor_job(
            _frontend_assets_info, FRONTEND_PATH, CARD_FILES
        )
        for filename in existing_files:
            url = f"{FRONTEND_URL_BASE}/{filename}"
            urls[url] = f"{url}?v={integration.version}-{digest}"

        await _async_register_resources(hass, urls)
    except Exception:
        _LOGGER.exception("Unable to register optional dashboard card frontend")
    else:
        hass.data[_REGISTERED] = True


async def _async_register_resources(hass: HomeAssistant, urls: dict[str, str]) -> None:
    """Register URLs in storage collection or fallback to extra js url."""
    lovelace = hass.data.get(LOVELACE_DATA)
    resources = lovelace.resources if lovelace is not None else None
    if isinstance(resources, ResourceStorageCollection):
        await resources.async_get_info()
        existing_by_url = {
            item["url"].partition("?")[0]: item for item in resources.async_items()
        }
        for base_url, item in existing_by_url.items():
            if base_url.startswith(f"{FRONTEND_URL_BASE}/") and base_url not in urls:
                await resources.async_delete_item(item["id"])
        for base_url, versioned_url in urls.items():
            existing = existing_by_url.get(base_url)
            if existing is None:
                await resources.async_create_item(
                    {"url": versioned_url, "res_type": "module"}
                )
            elif (
                existing.get("url") != versioned_url or existing.get("type") != "module"
            ):
                await resources.async_update_item(
                    existing["id"], {"url": versioned_url, "res_type": "module"}
                )
    else:
        for url in urls.values():
            add_extra_js_url(hass, url)
