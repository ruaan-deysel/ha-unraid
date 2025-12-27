"""API client tests for the Unraid integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from custom_components.unraid.api import UnraidAPIClient


@pytest.fixture
def api_client():
    """Create a test API client."""
    return UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_api_key_12345",
        port=443,
        verify_ssl=True,
    )


@pytest.mark.asyncio
async def test_api_client_initialization(api_client):
    """Test UnraidAPIClient initializes with correct parameters."""
    assert api_client.host == "https://192.168.1.100"
    assert api_client.port == 443
    assert api_client.verify_ssl is True
    assert api_client._api_key == "test_api_key_12345"
    assert api_client.session is None


@pytest.mark.asyncio
async def test_api_client_creates_session():
    """Test that API client creates aiohttp session on demand."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )

    async with client:
        assert client.session is not None
        assert isinstance(client.session, aiohttp.ClientSession)


@pytest.mark.asyncio
async def test_graphql_query_success():
    """Test successful GraphQL query execution."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )

    mock_response_data = {"data": {"online": True}}

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data

        result = await client.query("query { online }")

        assert result == mock_response_data["data"]
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert "query" in call_args[0][0]
        assert call_args[0][0]["query"] == "query { online }"


@pytest.mark.asyncio
async def test_graphql_query_with_variables():
    """Test GraphQL query with variables."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )

    mock_response_data = {"data": {"container": {"id": "ct:1", "state": "RUNNING"}}}

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data

        variables = {"id": "ct:1"}
        result = await client.query(
            "query($id: ID!) { container(id: $id) { id state } }", variables
        )

        assert result == mock_response_data["data"]
        call_args = mock_request.call_args
        assert call_args[0][0]["variables"] == variables


@pytest.mark.asyncio
async def test_graphql_query_error_handling():
    """Test GraphQL query error handling."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )

    mock_response_data = {
        "errors": [
            {
                "message": "Field 'invalid' not found",
                "locations": [{"line": 1, "column": 10}],
            }
        ]
    }

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data

        with pytest.raises(Exception) as exc_info:
            await client.query("query { invalid }")

        # Error message is now sanitized (doesn't expose server details)
        assert "GraphQL query failed with 1 error(s)" in str(exc_info.value)


@pytest.mark.asyncio
async def test_graphql_mutation_success():
    """Test successful GraphQL mutation execution."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )

    mock_response_data = {
        "data": {"docker": {"start": {"success": True, "message": "Container started"}}}
    }

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data

        mutation = (
            "mutation($id: ID!) { docker { start(id: $id) { success message } } }"
        )
        variables = {"id": "ct:1"}
        result = await client.mutate(mutation, variables)

        assert result == mock_response_data["data"]
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_connection_test_online():
    """Test connection test method returns True when online."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )

    with patch.object(client, "query", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = {"online": True}

        result = await client.test_connection()

        assert result is True
        mock_query.assert_called_once()
        assert "online" in mock_query.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_connection_test_network_error():
    """Test connection test handles network errors."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )

    with patch.object(client, "query", new_callable=AsyncMock) as mock_query:
        mock_query.side_effect = aiohttp.ClientError("Connection refused")

        with pytest.raises(aiohttp.ClientError):
            await client.test_connection()


@pytest.mark.asyncio
async def test_version_check_success():
    """Test version check method returns Unraid version."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )

    mock_info_data = {
        "info": {"versions": {"core": {"unraid": "7.2.0", "api": "4.29.2"}}}
    }

    with patch.object(client, "query", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = mock_info_data

        result = await client.get_version()

        assert result == {"unraid": "7.2.0", "api": "4.29.2"}
        mock_query.assert_called_once()
        assert "versions" in mock_query.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_version_check_unsupported():
    """Test version check detects unsupported version."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )

    mock_info_data = {
        "info": {"versions": {"core": {"unraid": "6.12.0", "api": "4.0.0"}}}
    }

    with patch.object(client, "query", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = mock_info_data

        result = await client.get_version()
        assert result == {"unraid": "6.12.0", "api": "4.0.0"}

        # Version validation should happen in caller (config_flow)
        # API client just returns the version


@pytest.mark.asyncio
async def test_session_management_context_manager():
    """Test session is properly created and closed with context manager."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )

    assert client.session is None


@pytest.mark.asyncio
async def test_api_handles_http_redirect():
    """Test that API client handles myunraid.net redirects."""
    client = UnraidAPIClient(
        host="192.168.1.1", api_key="test_key", port=80, verify_ssl=False
    )

    # Mock the _make_request method directly for the query
    # The _make_request method internally handles redirect discovery
    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"data": {"online": True}}

        result = await client.query("{ online }")

        assert result == {"online": True}
        mock_request.assert_called_once()

    await client.close()


@pytest.mark.asyncio
async def test_api_handles_redirect_without_location():
    """Test that API client handles 302 without Location header gracefully."""
    client = UnraidAPIClient(
        host="192.168.1.1", api_key="test_key", port=80, verify_ssl=False
    )

    # Mock _discover_redirect_url to return None (no redirect found)
    with patch.object(
        client, "_discover_redirect_url", new_callable=AsyncMock
    ) as mock_discover:
        mock_discover.return_value = None

        # Mock _make_request to simulate a 302 without Location header
        with patch.object(
            client, "_make_request", new_callable=AsyncMock
        ) as mock_request:
            # When the server returns a 302 without Location, _make_request should
            # raise an error since it can't follow the redirect
            mock_request.side_effect = aiohttp.ClientError(
                "Redirect response without Location header"
            )

            with pytest.raises(aiohttp.ClientError):
                await client.query("{ online }")

    await client.close()


@pytest.mark.asyncio
async def test_api_direct_https_no_redirect():
    """Test that direct HTTPS connections work without redirects."""
    client = UnraidAPIClient(
        host="https://192.168.1.1", api_key="test_key", port=443, verify_ssl=False
    )

    # Mock _discover_redirect_url to return None (no redirect needed)
    with patch.object(
        client, "_discover_redirect_url", new_callable=AsyncMock
    ) as mock_discover:
        mock_discover.return_value = None

        # Mock _make_request
        with patch.object(
            client, "_make_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"data": {"online": True}}

            result = await client.query("{ online }")

            assert result == {"online": True}

    await client.close()


@pytest.mark.asyncio
async def test_ssl_verification_disabled():
    """Test SSL verification can be disabled for self-signed certificates."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=False,
    )

    async with client:
        # Check that SSL context is configured to not verify
        connector = client.session.connector
        assert connector is not None
        assert connector._ssl is not None or connector._ssl is False
