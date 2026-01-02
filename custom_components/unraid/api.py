"""GraphQL API client for Unraid server."""

from __future__ import annotations

import logging
import ssl
from typing import Any
from urllib.parse import urlparse

import aiohttp

_LOGGER = logging.getLogger(__name__)

# HTTP status codes
HTTP_OK = 200
DEFAULT_HTTP_PORT = 80
DEFAULT_HTTPS_PORT = 443


class UnraidAPIError(Exception):
    """Exception raised for Unraid API errors (GraphQL errors, etc.)."""


class UnraidAPIClient:
    """Client for interacting with Unraid GraphQL API."""

    def __init__(
        self,
        host: str,
        api_key: str,
        http_port: int = 80,
        https_port: int = 443,
        verify_ssl: bool = True,
        timeout: int = 30,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """
        Initialize the API client.

        Args:
            host: Server hostname or IP (with or without http:// or https:// prefix)
            api_key: Unraid API key with ADMIN role
            http_port: HTTP port for redirect discovery (default 80)
            https_port: HTTPS port (default 443)
            verify_ssl: Whether to verify SSL certificates (default True)
            timeout: Request timeout in seconds (default 30s for queries)
            session: Optional aiohttp session (for HA websession injection)

        """
        self.host = host.strip()
        self.http_port = http_port
        self.https_port = https_port
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self._api_key = api_key
        self._session: aiohttp.ClientSession | None = session
        self._owns_session: bool = session is None  # Track if we created the session
        self._resolved_url: str | None = None  # Cached redirect URL

    @property
    def session(self) -> aiohttp.ClientSession | None:
        """Get the aiohttp session."""
        return self._session

    async def __aenter__(self) -> UnraidAPIClient:
        """Async context manager entry."""
        await self._create_session()
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        await self.close()

    async def _create_session(self) -> None:
        """Create aiohttp session with proper SSL configuration."""
        if self._session is not None:
            return

        # Configure SSL context
        ssl_context: ssl.SSLContext | bool | None = None
        if not self.verify_ssl:
            # Disable SSL verification for self-signed certificates
            ssl_context = False
            _LOGGER.warning(
                "SSL verification disabled for %s. "
                "Connection is encrypted but server identity is not verified.",
                self.host,
            )
        else:
            # Use default SSL verification
            ssl_context = True

        # Enable redirect following for POST requests (Unraid redirects HTTP -> HTTPS)
        connector = aiohttp.TCPConnector(ssl=ssl_context, force_close=False)
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)

        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config,
            headers={"x-api-key": self._api_key},
        )

    async def close(self) -> None:
        """Close the aiohttp session if we created it."""
        if self._session is not None and self._owns_session:
            await self._session.close()
            self._session = None

    def _get_base_url(self) -> str:
        """Get the base URL for API requests."""
        # If host already has protocol, use as-is
        if "://" in self.host:
            base_url = self.host.rstrip("/")
        else:
            base_url = f"https://{self.host}"

        # Add port only if non-standard HTTPS port
        if self.https_port != DEFAULT_HTTPS_PORT:
            return f"{base_url}:{self.https_port}"
        return base_url

    async def _discover_redirect_url(self) -> tuple[str | None, bool]:
        """
        Discover the correct URL and SSL mode for the Unraid server.

        Unraid servers have three SSL/TLS modes:
        - No: HTTP only, no redirect
        - Yes: HTTP redirects to HTTPS (self-signed certificate)
        - Strict: HTTP redirects to myunraid.net (valid certificate)

        This method checks for redirects by making an HTTP request.

        Returns:
            Tuple of (redirect_url, use_ssl):
            - (myunraid_url, True) for Strict mode
            - (https_url, True) for Yes mode
            - (None, False) for No mode (HTTP works directly)
            - (None, True) if HTTP check fails (fallback to HTTPS)

        """
        if self._session is None:
            await self._create_session()

        # Session must exist after creation - use conditional for proper error handling
        if self._session is None:
            raise RuntimeError("Failed to create HTTP session")

        # Strip any existing protocol from host
        clean_host = self.host
        if "://" in clean_host:
            clean_host = clean_host.split("://", 1)[1]
        # Remove trailing slashes
        clean_host = clean_host.rstrip("/")

        # Build port suffix for custom HTTP port
        http_port_suffix = (
            "" if self.http_port == DEFAULT_HTTP_PORT else f":{self.http_port}"
        )

        # Try HTTP first to discover redirects and SSL mode
        http_url = f"http://{clean_host}{http_port_suffix}/graphql"
        _LOGGER.debug("Checking for redirect at %s", http_url)

        # Include API key header for authentication
        headers = {"x-api-key": self._api_key}

        try:
            async with self._session.get(
                http_url, headers=headers, allow_redirects=False
            ) as response:
                _LOGGER.debug("HTTP response status: %d", response.status)

                # Check for redirects first (SSL/TLS = Yes or Strict)
                if response.status in (301, 302, 307, 308):
                    redirect_url = response.headers.get("Location")
                    _LOGGER.debug("Redirect location: %s", redirect_url)
                    if redirect_url:
                        # Properly parse URL and validate hostname to prevent
                        # URL substring bypass attacks
                        # (CodeQL py/incomplete-url-substring-sanitization)
                        parsed = urlparse(redirect_url)
                        hostname = parsed.hostname

                        # Check for myunraid.net redirect (Strict mode)
                        if hostname and (
                            hostname == "myunraid.net"
                            or hostname.endswith(".myunraid.net")
                        ):
                            _LOGGER.info(
                                "Discovered myunraid.net redirect (Strict mode): %s",
                                redirect_url,
                            )
                            return (redirect_url, True)

                        # Check for HTTPS redirect (Yes mode - self-signed cert)
                        if parsed.scheme == "https":
                            # Normalize the redirect URL (remove default port)
                            port = parsed.port
                            if port == DEFAULT_HTTPS_PORT:
                                # Rebuild URL without port
                                normalized = f"https://{hostname}{parsed.path}"
                            else:
                                normalized = redirect_url
                            _LOGGER.info(
                                "Discovered HTTPS redirect (Yes mode): %s",
                                normalized,
                            )
                            return (normalized, True)

                # Any non-redirect HTTP response means HTTP endpoint is available
                # This includes 200 (OK), 400 (Bad Request for GET on GraphQL), etc.
                # SSL/TLS is set to "No" - use HTTP directly
                _LOGGER.info(
                    "HTTP endpoint accessible (status %d), SSL/TLS mode is 'No' for %s",
                    response.status,
                    clean_host,
                )
                return (None, False)

        except aiohttp.ClientError as err:
            _LOGGER.debug("HTTP check failed, will try HTTPS: %s", err)

        # Default: HTTP check failed, assume HTTPS is needed
        return (None, True)

    async def _make_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Make a GraphQL request to the Unraid server.

        Args:
            payload: GraphQL query/mutation payload

        Returns:
            Response data dictionary

        Raises:
            aiohttp.ClientError: On network or HTTP errors

        """
        if self._session is None:
            await self._create_session()

        # Session must exist after creation
        if self._session is None:
            raise RuntimeError("Failed to create HTTP session")

        # Use cached URL if available, otherwise discover it
        if self._resolved_url is None:
            # Discover redirect URL and SSL mode
            redirect_url, use_ssl = await self._discover_redirect_url()
            if redirect_url:
                # Use the discovered redirect URL (myunraid.net or HTTPS redirect)
                self._resolved_url = redirect_url
            else:
                # No redirect - build URL based on SSL mode
                # Strip protocol from host if present
                clean_host = self.host
                if "://" in clean_host:
                    clean_host = clean_host.split("://", 1)[1]
                clean_host = clean_host.rstrip("/")

                # Build URL based on discovered SSL mode
                if use_ssl:
                    protocol = "https"
                    port_suffix = (
                        f":{self.https_port}"
                        if self.https_port != DEFAULT_HTTPS_PORT
                        else ""
                    )
                else:
                    protocol = "http"
                    # For HTTP, use http_port
                    port_suffix = (
                        f":{self.http_port}"
                        if self.http_port != DEFAULT_HTTP_PORT
                        else ""
                    )

                self._resolved_url = f"{protocol}://{clean_host}{port_suffix}/graphql"
            _LOGGER.debug("Using URL: %s", self._resolved_url)

        url = self._resolved_url

        # Always include API key header in requests (may be using injected session)
        headers = {"x-api-key": self._api_key}

        try:
            async with self._session.post(
                url, json=payload, headers=headers, allow_redirects=False
            ) as response:
                # If we still get a redirect, follow it
                if response.status in (301, 302, 307, 308):
                    redirect_url = response.headers.get("Location")
                    if redirect_url:
                        # Cache the new URL
                        self._resolved_url = redirect_url
                        async with self._session.post(
                            redirect_url,
                            json=payload,
                            headers=headers,
                            allow_redirects=False,
                        ) as redirect_response:
                            redirect_response.raise_for_status()
                            return await redirect_response.json()
                    raise aiohttp.ClientError(
                        f"Redirect {response.status} without Location header"
                    )

                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            raise err

    async def query(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            Query response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        response = await self._make_request(payload)

        # Extract data first - GraphQL can return partial data with errors
        data = response.get("data", {})

        if "errors" in response:
            errors = response["errors"]
            # Extract error messages for logging
            error_messages = []
            for err in errors:
                if isinstance(err, dict):
                    msg = err.get("message", str(err))
                    # Include path if available for context
                    path = err.get("path")
                    if path:
                        msg = f"{msg} (path: {path})"
                    error_messages.append(msg)
                else:
                    error_messages.append(str(err))

            # Log full details at debug for troubleshooting
            _LOGGER.debug("Full GraphQL error response: %s", errors)

            # If we have data, treat errors as partial failures
            # (e.g., VMs not enabled, no UPS connected)
            # Only raise exception if we have no data at all
            if data:
                # Log at debug level - these are expected for optional features
                # like UPS (no UPS connected), VMs (not enabled), etc.
                _LOGGER.debug(
                    "Some optional features unavailable: %s",
                    "; ".join(error_messages),
                )
            else:
                # Don't log at ERROR - let the caller decide how to handle
                # (e.g., UPS query failure is expected when no UPS configured)
                _LOGGER.debug(
                    "GraphQL query returned no data with %d error(s): %s",
                    len(errors),
                    "; ".join(error_messages),
                )
                raise UnraidAPIError(
                    f"GraphQL query failed: {'; '.join(error_messages)}"
                )

        return data

    async def mutate(
        self, mutation: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute a GraphQL mutation.

        Args:
            mutation: GraphQL mutation string
            variables: Optional mutation variables

        Returns:
            Mutation response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        # Mutations use same logic as queries in GraphQL
        return await self.query(mutation, variables)

    async def test_connection(self) -> bool:
        """
        Test connection to Unraid server.

        Returns:
            True if connection successful

        Raises:
            aiohttp.ClientError: On connection failure

        """
        query_str = "query { online }"
        result = await self.query(query_str)
        return result.get("online", False)

    async def get_version(self) -> dict[str, str]:
        """
        Get Unraid server version information.

        Returns:
            Dictionary with 'unraid' and 'api' version strings

        Raises:
            aiohttp.ClientError: On connection failure

        """
        query_str = """
            query {
                info {
                    versions {
                        core {
                            unraid
                            api
                        }
                    }
                }
            }
        """
        result = await self.query(query_str)
        versions = result.get("info", {}).get("versions", {}).get("core", {})
        return {
            "unraid": versions.get("unraid", "unknown"),
            "api": versions.get("api", "unknown"),
        }

    async def start_container(self, container_id: str) -> dict[str, Any]:
        """
        Start a Docker container.

        Args:
            container_id: Container ID to start

        Returns:
            Mutation response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation StartContainer($id: PrefixedID!) {
                docker {
                    start(id: $id) {
                        id
                        state
                        status
                    }
                }
            }
        """
        return await self.mutate(mutation, {"id": container_id})

    async def stop_container(self, container_id: str) -> dict[str, Any]:
        """
        Stop a Docker container.

        Args:
            container_id: Container ID to stop

        Returns:
            Mutation response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation StopContainer($id: PrefixedID!) {
                docker {
                    stop(id: $id) {
                        id
                        state
                        status
                    }
                }
            }
        """
        return await self.mutate(mutation, {"id": container_id})

    async def start_vm(self, vm_id: str) -> dict[str, Any]:
        """
        Start a virtual machine.

        Args:
            vm_id: VM ID to start

        Returns:
            Mutation response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation StartVM($id: PrefixedID!) {
                vm {
                    start(id: $id)
                }
            }
        """
        return await self.mutate(mutation, {"id": vm_id})

    async def stop_vm(self, vm_id: str) -> dict[str, Any]:
        """
        Stop a virtual machine.

        Args:
            vm_id: VM ID to stop

        Returns:
            Mutation response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation StopVM($id: PrefixedID!) {
                vm {
                    stop(id: $id)
                }
            }
        """
        return await self.mutate(mutation, {"id": vm_id})

    # ========================================================================
    # Array Control Methods
    # ========================================================================

    async def start_array(self) -> dict[str, Any]:
        """
        Start the Unraid array.

        WARNING: This is a potentially destructive operation.

        Returns:
            Mutation response data with array state

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation StartArray {
                array {
                    setState(input: { desiredState: START }) {
                        id
                        state
                    }
                }
            }
        """
        return await self.mutate(mutation)

    async def stop_array(self) -> dict[str, Any]:
        """
        Stop the Unraid array.

        WARNING: This is a destructive operation. All containers and VMs
        using array storage will be affected.

        Returns:
            Mutation response data with array state

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation StopArray {
                array {
                    setState(input: { desiredState: STOP }) {
                        id
                        state
                    }
                }
            }
        """
        return await self.mutate(mutation)

    # ========================================================================
    # Parity Check Control Methods
    # ========================================================================

    async def start_parity_check(self, correct: bool = False) -> dict[str, Any]:
        """
        Start a parity check.

        Args:
            correct: If True, write corrections to parity.
                    If False, only check (read-only).

        Returns:
            Mutation response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation StartParityCheck($correct: Boolean!) {
                parityCheck {
                    start(correct: $correct)
                }
            }
        """
        return await self.mutate(mutation, {"correct": correct})

    async def pause_parity_check(self) -> dict[str, Any]:
        """
        Pause a running parity check.

        Returns:
            Mutation response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation PauseParityCheck {
                parityCheck {
                    pause
                }
            }
        """
        return await self.mutate(mutation)

    async def resume_parity_check(self) -> dict[str, Any]:
        """
        Resume a paused parity check.

        Returns:
            Mutation response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation ResumeParityCheck {
                parityCheck {
                    resume
                }
            }
        """
        return await self.mutate(mutation)

    async def cancel_parity_check(self) -> dict[str, Any]:
        """
        Cancel a running parity check.

        Returns:
            Mutation response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation CancelParityCheck {
                parityCheck {
                    cancel
                }
            }
        """
        return await self.mutate(mutation)

    # ========================================================================
    # Disk Spin Control Methods
    # ========================================================================

    async def spin_up_disk(self, disk_id: str) -> dict[str, Any]:
        """
        Spin up (mount) a disk in the array.

        Args:
            disk_id: Disk ID to spin up (e.g., "disk:1")

        Returns:
            Mutation response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation SpinUpDisk($id: PrefixedID!) {
                array {
                    mountArrayDisk(id: $id) {
                        id
                        isSpinning
                    }
                }
            }
        """
        return await self.mutate(mutation, {"id": disk_id})

    async def spin_down_disk(self, disk_id: str) -> dict[str, Any]:
        """
        Spin down (unmount) a disk in the array.

        Args:
            disk_id: Disk ID to spin down (e.g., "disk:1")

        Returns:
            Mutation response data

        Raises:
            Exception: On GraphQL errors
            aiohttp.ClientError: On network errors

        """
        mutation = """
            mutation SpinDownDisk($id: PrefixedID!) {
                array {
                    unmountArrayDisk(id: $id) {
                        id
                        isSpinning
                    }
                }
            }
        """
        return await self.mutate(mutation, {"id": disk_id})
