"""Config flow for Unraid integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import OptionsFlowWithReload
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_SSL
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from unraid_api import UnraidClient
from unraid_api.exceptions import (
    UnraidAuthenticationError,
    UnraidConnectionError,
    UnraidSSLError,
    UnraidTimeoutError,
    UnraidVersionError,
)

from .const import (
    CONF_UPS_CAPACITY_VA,
    CONF_UPS_NOMINAL_POWER,
    DEFAULT_PORT,
    DEFAULT_UPS_CAPACITY_VA,
    DEFAULT_UPS_NOMINAL_POWER,
    DOMAIN,
    PLACEHOLDER_UUIDS,
    REPAIR_AUTH_FAILED,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult

_LOGGER = logging.getLogger(__name__)

MAX_HOSTNAME_LEN = 253
MIN_PORT = 1
MAX_PORT = 65535


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Unraid."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._server_uuid: str | None = None
        self._server_hostname: str | None = None
        self._use_ssl: bool = True  # Track whether SSL connection succeeded

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,  # noqa: ARG004
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return UnraidOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
                    errors[CONF_API_KEY] = "invalid_auth"
                    _LOGGER.warning(
                        "Invalid authentication for %s", user_input[CONF_HOST]
                    )
                except CannotConnectError:
                    errors[CONF_HOST] = "cannot_connect"
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
                # Use server UUID as unique ID (stable across hostname changes)
                # Fall back to host if UUID not available
                unique_id = self._server_uuid or user_input[CONF_HOST]
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                # Use server hostname as title (more readable than IP)
                title = self._server_hostname or user_input[CONF_HOST]

                _LOGGER.info(
                    "Creating config entry for %s (UUID: %s) port=%s ssl=%s",
                    title,
                    unique_id,
                    user_input.get(CONF_PORT, DEFAULT_PORT),
                    self._use_ssl,
                )
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input.get(CONF_PORT, DEFAULT_PORT),
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_SSL: self._use_ssl,
                    },
                    options={
                        CONF_UPS_CAPACITY_VA: DEFAULT_UPS_CAPACITY_VA,
                        CONF_UPS_NOMINAL_POWER: DEFAULT_UPS_NOMINAL_POWER,
                    },
                )

        # Show form with Host, Port, and API Key
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_PORT, max=MAX_PORT)
                ),
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
        """
        Test connection to Unraid server and validate version.

        The unraid-api library (>=1.5.0) handles SSL detection automatically:
        - Probes HTTP on http_port to discover SSL/TLS mode (No/Yes/Strict)
        - Follows redirects to HTTPS or myunraid.net endpoints
        - Raises UnraidConnectionError for unreachable non-default ports
        - Falls back to HTTPS on https_port for default port 80

        Connection strategy:
        1. Let the library probe and auto-detect via http_port
        2. If SSL cert error, retry with verify_ssl=False (self-signed certs)
        """
        host = user_input[CONF_HOST].strip()
        api_key = user_input[CONF_API_KEY].strip()
        port = user_input.get(CONF_PORT, DEFAULT_PORT)

        # Reset SSL state to default
        self._use_ssl = True

        session = async_get_clientsession(self.hass, verify_ssl=True)

        # Let the library's HTTP probe discover the SSL/TLS mode.
        # Pass the user's port as http_port; library defaults https_port=443.
        api_client = UnraidClient(
            host=host,
            api_key=api_key,
            http_port=port,
            verify_ssl=True,
            session=session,
        )

        try:
            await self._validate_connection(api_client, host)
        except CannotConnectError as err:
            error_str = str(err).lower()
            if "ssl" in error_str or "certificate" in error_str:
                # SSL cert error - retry with verify_ssl=False
                # (handles self-signed certificates)
                _LOGGER.debug(
                    "SSL verification failed, retrying with verify_ssl=False: %s", err
                )
                await api_client.close()
                session = async_get_clientsession(self.hass, verify_ssl=False)
                api_client = UnraidClient(
                    host=host,
                    api_key=api_key,
                    http_port=port,
                    verify_ssl=False,
                    session=session,
                )
                try:
                    await self._validate_connection(api_client, host)
                    # Success with SSL verification disabled
                    self._use_ssl = False
                    _LOGGER.info(
                        "Connected to %s with self-signed cert (SSL verify disabled)",
                        host,
                    )
                finally:
                    await api_client.close()
            else:
                raise
        finally:
            await api_client.close()

    async def _validate_connection(self, api_client: UnraidClient, host: str) -> None:
        """Validate connection, version, and fetch server info."""
        try:
            # Test connection
            await api_client.test_connection()

            # Check version compatibility using library method
            # Raises UnraidVersionError if server version is below minimum
            await api_client.check_compatibility()

            # Get server UUID and hostname for unique identification
            await self._fetch_server_info(api_client, host)

        except (InvalidAuthError, CannotConnectError, UnsupportedVersionError):
            raise
        except UnraidVersionError as err:
            msg = str(err)
            raise UnsupportedVersionError(msg) from err
        except UnraidAuthenticationError as err:
            msg = "Invalid API key or insufficient permissions"
            raise InvalidAuthError(msg) from err
        except UnraidSSLError as err:
            msg = f"SSL certificate error for {host}: {err}"
            raise CannotConnectError(msg) from err
        except (UnraidConnectionError, UnraidTimeoutError) as err:
            msg = f"Cannot connect to {host} - {err}"
            raise CannotConnectError(msg) from err
        except aiohttp.ClientResponseError as err:
            self._handle_http_error(err, host)
        except aiohttp.ClientConnectorError as err:
            msg = f"Cannot connect to {host} - {err}"
            raise CannotConnectError(msg) from err
        except aiohttp.ClientError as err:
            msg = f"Connection error: {err}"
            raise CannotConnectError(msg) from err
        except Exception as err:  # noqa: BLE001
            self._handle_generic_error(err)

    async def _fetch_server_info(self, api_client: UnraidClient, host: str) -> None:
        """
        Fetch server UUID and hostname for unique identification.

        Some systems (common AMI-based mini PCs) report a placeholder SMBIOS UUID
        that is not truly unique. When detected, the UUID is combined with the
        hostname to allow multiple servers to be configured.
        """
        # Use library's typed get_server_info() method
        server_info = await api_client.get_server_info()

        uuid = server_info.uuid
        hostname = server_info.hostname or host

        if uuid and uuid.lower() in PLACEHOLDER_UUIDS:
            _LOGGER.warning(
                "Detected placeholder SMBIOS UUID %s on %s; "
                "combining with hostname for unique identification",
                uuid,
                hostname,
            )
            self._server_uuid = f"{uuid}_{hostname}"
        else:
            self._server_uuid = uuid

        self._server_hostname = hostname

    def _handle_http_error(self, err: aiohttp.ClientResponseError, host: str) -> None:
        """Handle HTTP errors from API client."""
        if err.status in (401, 403):
            msg = "Invalid API key or insufficient permissions"
            raise InvalidAuthError(msg) from err
        msg = f"HTTP error {err.status}: {err.message}"
        raise CannotConnectError(msg) from err

    def _handle_generic_error(self, err: Exception) -> None:
        """Handle generic errors, mapping to appropriate exception types."""
        error_str = str(err).lower()
        if "401" in error_str or "unauthorized" in error_str:
            msg = "Invalid API key or insufficient permissions"
            raise InvalidAuthError(msg) from err
        if "ssl" in error_str or "certificate" in error_str:
            msg = f"SSL error: {err}. Try disabling SSL verification."
            raise CannotConnectError(msg) from err
        _LOGGER.exception("Unexpected error during connection test")
        raise CannotConnectError(f"Unexpected error: {err}") from err

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ) -> ConfigFlowResult:
        """Handle reauth when API key becomes invalid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation - prompt for new API key."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            # Test the new API key with existing connection settings
            test_input = {
                CONF_HOST: reauth_entry.data[CONF_HOST],
                CONF_PORT: reauth_entry.data.get(CONF_PORT, DEFAULT_PORT),
                CONF_API_KEY: user_input[CONF_API_KEY],
            }

            try:
                await self._test_connection(test_input)

                # Clear auth repair issue
                ir.async_delete_issue(self.hass, DOMAIN, REPAIR_AUTH_FAILED)

                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={**reauth_entry.data, **user_input},
                    reason="reauth_successful",
                )

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
            description_placeholders={"host": reauth_entry.data[CONF_HOST]},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            # Validate inputs
            validation_errors = self._validate_inputs(user_input)
            if validation_errors:
                errors.update(validation_errors)
            else:
                try:
                    await self._test_connection(user_input)

                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        data_updates={**user_input, CONF_SSL: self._use_ssl},
                    )

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
                    vol.Required(
                        CONF_PORT,
                        default=reconfigure_entry.data.get(CONF_PORT, DEFAULT_PORT),
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_PORT, max=MAX_PORT)),
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )


class UnraidOptionsFlowHandler(OptionsFlowWithReload):
    """Handle Unraid options flow with automatic reload on changes."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the init step to configure polling and UPS settings."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        # Check if UPS devices are detected
        has_ups = False
        if (
            hasattr(self.config_entry, "runtime_data")
            and self.config_entry.runtime_data
        ):
            system_coordinator = self.config_entry.runtime_data.system_coordinator
            if system_coordinator.data and system_coordinator.data.ups_devices:
                has_ups = True

        # Build schema - UPS options only shown if UPS device is detected
        # Note: Polling intervals are not user-configurable per HA Core guidelines
        # Users can use homeassistant.update_entity service for custom refresh rates
        schema_dict: dict[vol.Marker, Any] = {}

        # UPS options only shown if UPS is detected
        if has_ups:
            schema_dict[
                vol.Optional(
                    CONF_UPS_CAPACITY_VA,
                    default=options.get(CONF_UPS_CAPACITY_VA, DEFAULT_UPS_CAPACITY_VA),
                )
            ] = vol.All(vol.Coerce(int), vol.Range(min=0, max=100000))
            schema_dict[
                vol.Optional(
                    CONF_UPS_NOMINAL_POWER,
                    default=options.get(
                        CONF_UPS_NOMINAL_POWER, DEFAULT_UPS_NOMINAL_POWER
                    ),
                )
            ] = vol.All(vol.Coerce(int), vol.Range(min=0, max=100000))

        # If no options available (no UPS detected), show informational message
        if not schema_dict:
            return self.async_abort(reason="no_options_available")

        data_schema = vol.Schema(schema_dict)

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
