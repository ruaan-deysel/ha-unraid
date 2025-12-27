"""Config flow for Unraid integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir

from .api import UnraidAPIClient
from .const import (
    CONF_STORAGE_INTERVAL,
    CONF_SYSTEM_INTERVAL,
    CONF_UPS_CAPACITY_VA,
    DEFAULT_STORAGE_POLL_INTERVAL,
    DEFAULT_SYSTEM_POLL_INTERVAL,
    DEFAULT_UPS_CAPACITY_VA,
    DOMAIN,
    REPAIR_AUTH_FAILED,
)

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

MIN_API_VERSION = "4.21.0"
MIN_UNRAID_VERSION = "7.2.0"
MAX_HOSTNAME_LEN = 253


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Unraid."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._reauth_entry: config_entries.ConfigEntry | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,  # noqa: ARG004
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return UnraidOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate inputs
            validation_errors = self._validate_inputs(user_input)
            if validation_errors:
                errors.update(validation_errors)
            else:
                # Try to connect to server
                try:
                    _LOGGER.debug(
                        "Testing connection to Unraid server: %s", user_input[CONF_HOST]
                    )
                    await self._test_connection(user_input)
                    _LOGGER.info(
                        "Successfully connected to Unraid server: %s",
                        user_input[CONF_HOST],
                    )
                except InvalidAuthError:
                    errors["base"] = "invalid_auth"
                    _LOGGER.warning(
                        "Invalid authentication for %s", user_input[CONF_HOST]
                    )
                except CannotConnectError:
                    errors["base"] = "cannot_connect"
                    _LOGGER.warning("Cannot connect to %s", user_input[CONF_HOST])
                except UnsupportedVersionError:
                    errors["base"] = "unsupported_version"
                    _LOGGER.warning("Unsupported version for %s", user_input[CONF_HOST])
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception(
                        "Unexpected error connecting to %s", user_input[CONF_HOST]
                    )
                    errors["base"] = "unknown"

            # If no errors, create entry
            if not errors:
                host = user_input[CONF_HOST]
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()

                _LOGGER.info("Creating config entry for %s", host)
                return self.async_create_entry(
                    title=host,
                    data=user_input,
                    options={
                        CONF_SYSTEM_INTERVAL: DEFAULT_SYSTEM_POLL_INTERVAL,
                        CONF_STORAGE_INTERVAL: DEFAULT_STORAGE_POLL_INTERVAL,
                        CONF_UPS_CAPACITY_VA: DEFAULT_UPS_CAPACITY_VA,
                    },
                )

        # Show form - simplified to just Host and API Key
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    def _validate_inputs(self, user_input: dict[str, Any]) -> dict[str, str]:
        """Validate user inputs."""
        errors = {}

        # Host validation
        host = user_input.get(CONF_HOST, "").strip()
        if not host:
            errors[CONF_HOST] = "required"
        elif len(host) > MAX_HOSTNAME_LEN:
            errors[CONF_HOST] = "invalid_hostname"

        # API key validation
        api_key = user_input.get(CONF_API_KEY, "").strip()
        if not api_key:
            errors[CONF_API_KEY] = "required"

        return errors

    async def _test_connection(self, user_input: dict[str, Any]) -> None:
        """Test connection to Unraid server and validate version."""
        host = user_input[CONF_HOST].strip()
        api_key = user_input[CONF_API_KEY].strip()

        # Auto-detect settings: default port 443, SSL verification enabled
        # The API client handles myunraid.net redirects automatically
        api_client = UnraidAPIClient(
            host=host,
            api_key=api_key,
            port=443,
            verify_ssl=True,
        )

        try:
            # Test connection
            await api_client.test_connection()

            # Get version
            version_info = await api_client.get_version()

            # Check version - api.py returns "api" not "api_version"
            api_version = version_info.get("api", "0.0.0")
            unraid_version = version_info.get("unraid", "0.0.0")

            if not self._is_supported_version(api_version):
                msg = (
                    f"Unraid {unraid_version} (API {api_version}) not supported. "
                    f"Minimum required: Unraid {MIN_UNRAID_VERSION} "
                    f"(API {MIN_API_VERSION})"
                )
                raise UnsupportedVersionError(msg)

        except InvalidAuthError:
            raise
        except CannotConnectError:
            raise
        except UnsupportedVersionError:
            raise
        except aiohttp.ClientResponseError as err:
            if err.status in (401, 403):
                msg = "Invalid API key or insufficient permissions"
                raise InvalidAuthError(msg) from err
            msg = f"HTTP error {err.status}: {err.message}"
            raise CannotConnectError(msg) from err
        except aiohttp.ClientConnectorError as err:
            msg = f"Cannot connect to {host} - {err}"
            raise CannotConnectError(msg) from err
        except aiohttp.ClientError as err:
            msg = f"Connection error: {err}"
            raise CannotConnectError(msg) from err
        except Exception as err:
            error_str = str(err).lower()
            if "401" in error_str or "unauthorized" in error_str:
                msg = "Invalid API key or insufficient permissions"
                raise InvalidAuthError(msg) from err
            if "ssl" in error_str or "certificate" in error_str:
                msg = f"SSL error: {err}. Try disabling SSL verification."
                raise CannotConnectError(msg) from err
            _LOGGER.exception("Unexpected error during connection test")
            raise CannotConnectError(f"Unexpected error: {err}") from err

        finally:
            await api_client.close()

    def _is_supported_version(self, api_version: str) -> bool:
        """Check if API version is supported using proper version parsing."""
        try:
            from packaging.version import InvalidVersion, Version

            # Parse versions properly handling suffixes like "-beta", "a", etc.
            current = Version(api_version)
            minimum = Version(MIN_API_VERSION)
            return current >= minimum
        except InvalidVersion:
            # Fallback to basic comparison if packaging fails
            _LOGGER.warning(
                "Could not parse API version '%s', assuming supported", api_version
            )
            return True

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ) -> FlowResult:
        """Handle reauth when API key becomes invalid."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauth confirmation - prompt for new API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if self._reauth_entry is None:
                return self.async_abort(reason="reauth_failed")

            # Test the new API key
            test_input = {
                CONF_HOST: self._reauth_entry.data[CONF_HOST],
                CONF_API_KEY: user_input[CONF_API_KEY],
            }

            try:
                await self._test_connection(test_input)

                # Update config entry with new API key
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={**self._reauth_entry.data, **user_input},
                )

                # Clear auth repair issue
                ir.async_delete_issue(self.hass, DOMAIN, REPAIR_AUTH_FAILED)

                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

            except InvalidAuthError:
                errors["base"] = "invalid_auth"
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except UnsupportedVersionError:
                errors["base"] = "unsupported_version"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error during reauth")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
            description_placeholders={
                "host": self._reauth_entry.data[CONF_HOST] if self._reauth_entry else ""
            },
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        reconfigure_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if reconfigure_entry is None:
            return self.async_abort(reason="reconfigure_failed")

        if user_input is not None:
            # Validate inputs
            validation_errors = self._validate_inputs(user_input)
            if validation_errors:
                errors.update(validation_errors)
            else:
                try:
                    await self._test_connection(user_input)

                    # Update the config entry with new data
                    self.hass.config_entries.async_update_entry(
                        reconfigure_entry,
                        data=user_input,
                    )

                    await self.hass.config_entries.async_reload(
                        reconfigure_entry.entry_id
                    )
                    return self.async_abort(reason="reconfigure_successful")

                except InvalidAuthError:
                    errors["base"] = "invalid_auth"
                except CannotConnectError:
                    errors["base"] = "cannot_connect"
                except UnsupportedVersionError:
                    errors["base"] = "unsupported_version"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected error during reconfigure")
                    errors["base"] = "unknown"

        # Pre-fill form with existing values
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST, default=reconfigure_entry.data.get(CONF_HOST, "")
                    ): str,
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )


class UnraidOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Unraid options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the init step to configure polling intervals and UPS settings."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SYSTEM_INTERVAL,
                    default=options.get(
                        CONF_SYSTEM_INTERVAL, DEFAULT_SYSTEM_POLL_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                vol.Optional(
                    CONF_STORAGE_INTERVAL,
                    default=options.get(
                        CONF_STORAGE_INTERVAL, DEFAULT_STORAGE_POLL_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                vol.Optional(
                    CONF_UPS_CAPACITY_VA,
                    default=options.get(CONF_UPS_CAPACITY_VA, DEFAULT_UPS_CAPACITY_VA),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100000)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )


class InvalidAuthError(HomeAssistantError):
    """Exception for invalid authentication."""


class CannotConnectError(HomeAssistantError):
    """Exception for cannot connect to server."""


class UnsupportedVersionError(HomeAssistantError):
    """Exception for unsupported version."""
