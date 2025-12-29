"""GraphQL API client for Unraid server."""

from __future__ import annotations

import logging
import ssl
from typing import Any
from urllib.parse import urlparse

import aiohttp

_LOGGER = logging.getLogger(__name__)


class UnraidAPIClient:
    """Client for interacting with Unraid GraphQL API."""

    def __init__(
        self,
        host: str,
        api_key: str,
        port: int = 443,
        verify_ssl: bool = True,
        timeout: int = 30,
    ) -> None:
        """
        Initialize the API client.

        Args:
            host: Server hostname or IP (with or without http:// or https:// prefix)
            api_key: Unraid API key with ADMIN role
            port: HTTPS port (default 443)
            verify_ssl: Whether to verify SSL certificates (default True)
            timeout: Request timeout in seconds (default 30s for queries)

        """
        self.host = host.strip()
        self.port = port
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self._api_key = api_key
        self._session: aiohttp.ClientSession | None = None
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
        """Close the aiohttp session."""
        if self._session is not None:
            await self._session.close()
            self._session = None

    def _get_base_url(self) -> str:
        """Get the base URL for API requests."""
        # If host already has protocol, use as-is
        if "://" in self.host:
            base_url = self.host.rstrip("/")
        else:
            base_url = f"https://{self.host}"

        # Add port only if non-standard (not 80 or 443)
        if self.port not in (80, 443):
            return f"{base_url}:{self.port}"
        return base_url

    async def _discover_redirect_url(self) -> str | None:
        """
        Discover if the server redirects to a myunraid.net URL.

        Some Unraid servers are configured to redirect all traffic through
        the Unraid cloud relay service (myunraid.net). This method checks
        for such redirects by making an HTTP request and following redirects.

        Returns:
            The redirect URL if found, or None if no redirect is needed.

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

        # Try HTTP first to discover redirects
        # (Unraid often redirects HTTP -> cloud URL)
        http_url = f"http://{clean_host}/graphql"
        _LOGGER.debug("Checking for redirect at %s", http_url)

        try:
            async with self._session.get(http_url, allow_redirects=False) as response:
                _LOGGER.debug("HTTP response status: %d", response.status)
                if response.status in (301, 302, 307, 308):
                    redirect_url = response.headers.get("Location")
                    _LOGGER.debug("Redirect location: %s", redirect_url)
                    if redirect_url:
                        # Properly parse URL and validate hostname to prevent
                        # URL substring bypass attacks
                        # (CodeQL py/incomplete-url-substring-sanitization)
                        parsed = urlparse(redirect_url)
                        hostname = parsed.hostname
                        if hostname and (
                            hostname == "myunraid.net"
                            or hostname.endswith(".myunraid.net")
                        ):
                            _LOGGER.info(
                                "Discovered myunraid.net redirect URL: %s", redirect_url
                            )
                            return redirect_url
        except aiohttp.ClientError as err:
            _LOGGER.debug("HTTP check failed (expected): %s", err)

        return None

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
            # Try to discover redirect URL first
            redirect_url = await self._discover_redirect_url()
            if redirect_url:
                self._resolved_url = redirect_url
            else:
                # No redirect, use direct URL
                self._resolved_url = f"{self._get_base_url()}/graphql"
            _LOGGER.debug("Using URL: %s", self._resolved_url)

        url = self._resolved_url

        try:
            async with self._session.post(
                url, json=payload, allow_redirects=False
            ) as response:
                # If we still get a redirect, follow it
                if response.status in (301, 302, 307, 308):
                    redirect_url = response.headers.get("Location")
                    if redirect_url:
                        # Cache the new URL
                        self._resolved_url = redirect_url
                        async with self._session.post(
                            redirect_url, json=payload, allow_redirects=False
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

            # Log at warning level so users can see what's wrong
            _LOGGER.warning(
                "GraphQL query failed with %d error(s): %s",
                len(errors),
                "; ".join(error_messages),
            )
            # Also log full details at debug for troubleshooting
            _LOGGER.debug("Full GraphQL error response: %s", errors)

            raise Exception(f"GraphQL query failed: {'; '.join(error_messages)}")

        return response.get("data", {})

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
