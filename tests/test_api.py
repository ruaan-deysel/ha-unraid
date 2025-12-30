"""API client tests for the Unraid integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

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

        # Error message now includes the actual error for user diagnostics
        assert "GraphQL query failed" in str(exc_info.value)
        assert "Field 'invalid' not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_graphql_query_partial_errors_returns_data():
    """
    Test GraphQL query with partial errors still returns data.

    This simulates the case where VMs or UPS aren't available but other data is.
    """
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )

    # Simulate partial failure - some data returned, some errors
    mock_response_data = {
        "data": {
            "info": {"system": {"uuid": "abc123"}},
            "vms": None,  # VMs not available
            "upsDevices": None,  # No UPS
        },
        "errors": [
            {
                "message": "VMs are not available",
                "path": ["vms", "domains"],
            },
            {
                "message": "No UPS data returned from apcaccess",
                "path": ["upsDevices"],
            },
        ],
    }

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data

        # Should NOT raise exception - data is available
        result = await client.query("query { info { system { uuid } } }")

        # Should return the data that was available
        assert result["info"]["system"]["uuid"] == "abc123"


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

    # Mock _discover_redirect_url to return tuple (no redirect, use SSL)
    with patch.object(
        client, "_discover_redirect_url", new_callable=AsyncMock
    ) as mock_discover:
        mock_discover.return_value = (None, True)

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

    # Mock _discover_redirect_url to return tuple (no redirect, use SSL)
    with patch.object(
        client, "_discover_redirect_url", new_callable=AsyncMock
    ) as mock_discover:
        mock_discover.return_value = (None, True)

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


@pytest.mark.asyncio
async def test_get_base_url_with_protocol():
    """Test _get_base_url handles URLs with protocol prefix."""
    client = UnraidAPIClient(
        host="https://myserver.local",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )
    assert client._get_base_url() == "https://myserver.local"


@pytest.mark.asyncio
async def test_get_base_url_without_protocol():
    """Test _get_base_url adds https:// when protocol is missing."""
    client = UnraidAPIClient(
        host="myserver.local",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )
    assert client._get_base_url() == "https://myserver.local"


@pytest.mark.asyncio
async def test_get_base_url_non_standard_port():
    """Test _get_base_url includes non-standard port."""
    client = UnraidAPIClient(
        host="myserver.local",
        api_key="test_key",
        port=8443,
        verify_ssl=True,
    )
    assert client._get_base_url() == "https://myserver.local:8443"


@pytest.mark.asyncio
async def test_get_base_url_strips_trailing_slash():
    """Test _get_base_url strips trailing slash from host."""
    client = UnraidAPIClient(
        host="https://myserver.local/",
        api_key="test_key",
        port=443,
        verify_ssl=True,
    )
    assert client._get_base_url() == "https://myserver.local"


@pytest.mark.asyncio
async def test_injected_session_not_closed():
    """Test that injected sessions are not closed by the client."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_session.closed = False

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
        session=mock_session,
    )

    # Client should use the injected session
    assert client._owns_session is False
    assert client.session is mock_session

    # Close should not close the injected session
    await client.close()
    mock_session.close.assert_not_called()


@pytest.mark.asyncio
async def test_graphql_error_with_path():
    """Test GraphQL error handling includes path information."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
    )

    mock_response_data = {
        "errors": [
            {
                "message": "Cannot query field 'unknown'",
                "path": ["info", "system", "unknown"],
            }
        ]
    }

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data

        with pytest.raises(Exception) as exc_info:
            await client.query("query { info { system { unknown } } }")

        # Error should include path
        assert "path:" in str(exc_info.value)


@pytest.mark.asyncio
async def test_graphql_multiple_errors():
    """Test GraphQL handling with multiple errors."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
    )

    mock_response_data = {
        "errors": [
            {"message": "Error 1"},
            {"message": "Error 2"},
            {"message": "Error 3"},
        ]
    }

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data

        with pytest.raises(Exception) as exc_info:
            await client.query("query { invalid }")

        # All errors should be in the message
        assert "Error 1" in str(exc_info.value)
        assert "Error 2" in str(exc_info.value)
        assert "Error 3" in str(exc_info.value)


@pytest.mark.asyncio
async def test_graphql_error_as_string():
    """Test GraphQL error handling when error is a plain string."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
    )

    mock_response_data = {"errors": ["Simple string error"]}

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data

        with pytest.raises(Exception) as exc_info:
            await client.query("query { invalid }")

        assert "Simple string error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_mutation_with_error():
    """Test mutation error handling."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
    )

    mock_response_data = {"errors": [{"message": "Mutation failed: permission denied"}]}

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data

        with pytest.raises(Exception) as exc_info:
            await client.mutate("mutation { docker { start } }")

        assert "permission denied" in str(exc_info.value)


@pytest.mark.asyncio
async def test_query_empty_data_response():
    """Test query returns empty dict when data key is missing."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
    )

    mock_response_data = {}  # No "data" key

    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data

        result = await client.query("query { online }")

        assert result == {}


@pytest.mark.asyncio
async def test_client_timeout_configuration():
    """Test that client respects timeout configuration."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
        timeout=60,
    )

    assert client.timeout == 60


# =============================================================================
# Container Control Methods Tests
# =============================================================================


@pytest.mark.asyncio
async def test_start_container():
    """Test start_container method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"docker": {"start": {"id": "ct:1", "state": "RUNNING"}}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.start_container("ct:1")

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "StartContainer" in call_args[0][0]
        assert call_args[0][1]["id"] == "ct:1"
        assert result == mock_response


@pytest.mark.asyncio
async def test_stop_container():
    """Test stop_container method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"docker": {"stop": {"id": "ct:1", "state": "EXITED"}}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.stop_container("ct:1")

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "StopContainer" in call_args[0][0]
        assert call_args[0][1]["id"] == "ct:1"
        assert result == mock_response


# =============================================================================
# VM Control Methods Tests
# =============================================================================


@pytest.mark.asyncio
async def test_start_vm():
    """Test start_vm method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"vm": {"start": True}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.start_vm("vm:1")

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "StartVM" in call_args[0][0]
        assert call_args[0][1]["id"] == "vm:1"
        assert result == mock_response


@pytest.mark.asyncio
async def test_stop_vm():
    """Test stop_vm method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"vm": {"stop": True}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.stop_vm("vm:1")

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "StopVM" in call_args[0][0]
        assert call_args[0][1]["id"] == "vm:1"
        assert result == mock_response


# =============================================================================
# Array Control Methods Tests
# =============================================================================


@pytest.mark.asyncio
async def test_start_array():
    """Test start_array method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"array": {"start": {"state": "STARTED"}}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.start_array()

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "StartArray" in call_args[0][0]
        assert result == mock_response


@pytest.mark.asyncio
async def test_stop_array():
    """Test stop_array method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"array": {"stop": {"state": "STOPPED"}}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.stop_array()

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "StopArray" in call_args[0][0]
        assert result == mock_response


# =============================================================================
# Parity Control Methods Tests
# =============================================================================


@pytest.mark.asyncio
async def test_start_parity_check():
    """Test start_parity_check method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"parityCheck": {"start": True}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.start_parity_check()

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "StartParityCheck" in call_args[0][0]
        assert call_args[0][1]["correct"] is False  # Default value
        assert result == mock_response


@pytest.mark.asyncio
async def test_start_parity_check_with_correct():
    """Test start_parity_check with correct option."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"parityCheck": {"start": True}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.start_parity_check(correct=True)

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert call_args[0][1]["correct"] is True
        assert result == mock_response


@pytest.mark.asyncio
async def test_pause_parity_check():
    """Test pause_parity_check method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"parityCheck": {"pause": True}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.pause_parity_check()

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "PauseParityCheck" in call_args[0][0]
        assert result == mock_response


@pytest.mark.asyncio
async def test_resume_parity_check():
    """Test resume_parity_check method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"parityCheck": {"resume": True}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.resume_parity_check()

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "ResumeParityCheck" in call_args[0][0]
        assert result == mock_response


@pytest.mark.asyncio
async def test_cancel_parity_check():
    """Test cancel_parity_check method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"parityCheck": {"cancel": True}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.cancel_parity_check()

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "CancelParityCheck" in call_args[0][0]
        assert result == mock_response


# =============================================================================
# Disk Control Methods Tests
# =============================================================================


@pytest.mark.asyncio
async def test_spin_up_disk():
    """Test spin_up_disk method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {"array": {"mountArrayDisk": {"id": "disk:1", "isSpinning": True}}}

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.spin_up_disk("disk:1")

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "SpinUpDisk" in call_args[0][0]
        assert call_args[0][1]["id"] == "disk:1"
        assert result == mock_response


@pytest.mark.asyncio
async def test_spin_down_disk():
    """Test spin_down_disk method calls mutate with correct mutation."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = {
        "array": {"unmountArrayDisk": {"id": "disk:1", "isSpinning": False}}
    }

    with patch.object(client, "mutate", new_callable=AsyncMock) as mock_mutate:
        mock_mutate.return_value = mock_response

        result = await client.spin_down_disk("disk:1")

        mock_mutate.assert_called_once()
        call_args = mock_mutate.call_args
        assert "SpinDownDisk" in call_args[0][0]
        assert call_args[0][1]["id"] == "disk:1"
        assert result == mock_response


# =============================================================================
# Internal Method Tests (coverage for _create_session, _discover_redirect_url,
# _make_request)
# =============================================================================


@pytest.mark.asyncio
async def test_create_session_with_ssl_disabled():
    """Test session creation with SSL verification disabled logs warning."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
        verify_ssl=False,
    )

    with patch("custom_components.unraid.api._LOGGER") as mock_logger:
        await client._create_session()

        # Should log a warning about disabled SSL
        mock_logger.warning.assert_called()
        warning_call = str(mock_logger.warning.call_args)
        assert "SSL verification disabled" in warning_call

    await client.close()


@pytest.mark.asyncio
async def test_create_session_does_nothing_if_already_created():
    """Test _create_session is idempotent."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    await client._create_session()
    first_session = client._session

    # Call again - should not create a new session
    await client._create_session()
    second_session = client._session

    assert first_session is second_session

    await client.close()


@pytest.mark.asyncio
async def test_get_base_url_with_protocol_internal():
    """Test _get_base_url when host already has protocol."""
    client = UnraidAPIClient(
        host="https://192.168.1.100",
        api_key="test_key",
    )

    assert client._get_base_url() == "https://192.168.1.100"


@pytest.mark.asyncio
async def test_get_base_url_without_protocol_internal():
    """Test _get_base_url adds https protocol."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    assert client._get_base_url() == "https://192.168.1.100"


@pytest.mark.asyncio
async def test_get_base_url_with_custom_port():
    """Test _get_base_url adds non-standard port."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
        port=8443,
    )

    assert client._get_base_url() == "https://192.168.1.100:8443"


@pytest.mark.asyncio
async def test_get_base_url_with_trailing_slash():
    """Test _get_base_url strips trailing slash."""
    client = UnraidAPIClient(
        host="https://192.168.1.100/",
        api_key="test_key",
    )

    assert client._get_base_url() == "https://192.168.1.100"


@pytest.mark.asyncio
async def test_discover_redirect_url_no_redirect():
    """Test _discover_redirect_url returns (None, False) for HTTP-only mode."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    # Create a proper async context manager mock
    mock_response = MagicMock()
    mock_response.status = 200  # HTTP 200 = SSL/TLS mode "No"

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_response

    mock_session = MagicMock()
    mock_session.get.return_value = mock_cm

    client._session = mock_session

    result = await client._discover_redirect_url()

    # HTTP 200 means SSL/TLS is "No" - use HTTP directly
    assert result == (None, False)


@pytest.mark.asyncio
async def test_discover_redirect_url_http_400_means_http_available():
    """
    Test _discover_redirect_url treats HTTP 400 as HTTP mode available.

    GraphQL endpoints return 400 for GET requests without query params,
    but this still means HTTP is accessible (SSL/TLS mode is 'No').
    """
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = MagicMock()
    mock_response.status = 400  # Bad Request (GraphQL rejects GET without query)

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_response

    mock_session = MagicMock()
    mock_session.get.return_value = mock_cm

    client._session = mock_session

    result = await client._discover_redirect_url()

    # HTTP 400 still means HTTP endpoint is responding - use HTTP
    assert result == (None, False)


@pytest.mark.asyncio
async def test_discover_redirect_url_with_myunraid_redirect():
    """Test _discover_redirect_url detects myunraid.net redirect (Strict mode)."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = MagicMock()
    mock_response.status = 302
    mock_response.headers = {"Location": "https://example.myunraid.net/graphql"}

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_response

    mock_session = MagicMock()
    mock_session.get.return_value = mock_cm

    client._session = mock_session

    result = await client._discover_redirect_url()

    # myunraid.net redirect = SSL/TLS "Strict" mode
    assert result == ("https://example.myunraid.net/graphql", True)


@pytest.mark.asyncio
async def test_discover_redirect_url_https_redirect():
    """Test _discover_redirect_url detects HTTPS redirect (Yes mode - self-signed)."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = MagicMock()
    mock_response.status = 302
    mock_response.headers = {"Location": "https://192.168.1.100:443/graphql"}

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_response

    mock_session = MagicMock()
    mock_session.get.return_value = mock_cm

    client._session = mock_session

    result = await client._discover_redirect_url()

    # HTTPS redirect = SSL/TLS "Yes" mode (self-signed cert)
    # Port 443 should be normalized out
    assert result == ("https://192.168.1.100/graphql", True)


@pytest.mark.asyncio
async def test_discover_redirect_url_handles_client_error():
    """Test _discover_redirect_url handles network errors gracefully."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_cm = AsyncMock()
    mock_cm.__aenter__.side_effect = aiohttp.ClientError("Connection refused")

    mock_session = MagicMock()
    mock_session.get.return_value = mock_cm

    client._session = mock_session

    result = await client._discover_redirect_url()

    # On error, fallback to HTTPS (assume SSL needed)
    assert result == (None, True)


@pytest.mark.asyncio
async def test_discover_redirect_url_creates_session_if_none():
    """Test _discover_redirect_url creates session if needed."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = MagicMock()
    mock_response.status = 200

    with patch.object(client, "_create_session", new_callable=AsyncMock) as mock_create:

        async def create_and_set_session() -> None:
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_session = MagicMock()
            mock_session.get.return_value = mock_cm
            client._session = mock_session

        mock_create.side_effect = create_and_set_session

        await client._discover_redirect_url()

        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_discover_redirect_url_https_redirect_custom_port():
    """Test HTTPS redirect with non-standard port is preserved."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    mock_response = MagicMock()
    mock_response.status = 302
    # Custom port should be preserved
    mock_response.headers = {"Location": "https://192.168.1.100:8443/graphql"}

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_response

    mock_session = MagicMock()
    mock_session.get.return_value = mock_cm

    client._session = mock_session

    result = await client._discover_redirect_url()

    # Custom port should be preserved in URL
    assert result == ("https://192.168.1.100:8443/graphql", True)


@pytest.mark.asyncio
async def test_discover_redirect_url_strips_trailing_slash_from_host():
    """Test that trailing slashes are stripped from host."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100/",  # Trailing slash
        api_key="test_key",
    )

    mock_response = MagicMock()
    mock_response.status = 200

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_response

    mock_session = MagicMock()
    mock_session.get.return_value = mock_cm

    client._session = mock_session

    result = await client._discover_redirect_url()

    # Should return HTTP mode tuple
    assert result == (None, False)
    # Verify the URL used in the request doesn't have double slashes
    call_args = mock_session.get.call_args
    assert call_args[0][0] == "http://192.168.1.100/graphql"


@pytest.mark.asyncio
async def test_make_request_builds_http_url_when_no_ssl():
    """Test _make_request builds correct HTTP URL when SSL is not needed."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
        port=443,
    )

    expected_data = {"data": {"online": True}}

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_data)
    mock_response.raise_for_status = MagicMock()

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_response

    mock_session = MagicMock()
    mock_session.post.return_value = mock_cm

    client._session = mock_session

    # Mock discover to return HTTP-only mode
    with patch.object(
        client, "_discover_redirect_url", new_callable=AsyncMock
    ) as mock_discover:
        mock_discover.return_value = (None, False)  # HTTP mode

        await client._make_request({"query": "query { online }"})

        # Verify HTTP URL was built
        assert client._resolved_url == "http://192.168.1.100/graphql"


@pytest.mark.asyncio
async def test_make_request_success():
    """Test _make_request returns JSON response on success."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    expected_data = {"data": {"online": True}}

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_data)
    mock_response.raise_for_status = MagicMock()

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_response

    mock_session = MagicMock()
    mock_session.post.return_value = mock_cm

    client._session = mock_session
    client._resolved_url = "https://192.168.1.100/graphql"

    result = await client._make_request({"query": "query { online }"})

    assert result == expected_data


@pytest.mark.asyncio
async def test_make_request_follows_redirect():
    """Test _make_request follows redirect response."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    expected_data = {"data": {"online": True}}

    # First response is a redirect
    redirect_response = MagicMock()
    redirect_response.status = 302
    redirect_response.headers = {"Location": "https://newurl.example.com/graphql"}

    # Second response after redirect
    final_response = MagicMock()
    final_response.status = 200
    final_response.json = AsyncMock(return_value=expected_data)
    final_response.raise_for_status = MagicMock()

    # Create context managers
    redirect_cm = AsyncMock()
    redirect_cm.__aenter__.return_value = redirect_response

    final_cm = AsyncMock()
    final_cm.__aenter__.return_value = final_response

    mock_session = MagicMock()
    # First call returns redirect, second returns final response
    mock_session.post.side_effect = [redirect_cm, final_cm]

    client._session = mock_session
    client._resolved_url = "https://192.168.1.100/graphql"

    result = await client._make_request({"query": "query { online }"})

    assert result == expected_data
    # Check that resolved URL was updated
    assert client._resolved_url == "https://newurl.example.com/graphql"


@pytest.mark.asyncio
async def test_make_request_redirect_without_location():
    """Test _make_request raises error on redirect without Location header."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    redirect_response = MagicMock()
    redirect_response.status = 302
    redirect_response.headers = {}  # No Location header

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = redirect_response

    mock_session = MagicMock()
    mock_session.post.return_value = mock_cm

    client._session = mock_session
    client._resolved_url = "https://192.168.1.100/graphql"

    with pytest.raises(aiohttp.ClientError) as exc_info:
        await client._make_request({"query": "query { online }"})

    assert "Redirect" in str(exc_info.value)
    assert "without Location header" in str(exc_info.value)


@pytest.mark.asyncio
async def test_make_request_creates_session_if_none():
    """Test _make_request creates session if needed."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    expected_data = {"data": {"online": True}}

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_data)
    mock_response.raise_for_status = MagicMock()

    with (
        patch.object(client, "_create_session", new_callable=AsyncMock) as mock_create,
        patch.object(
            client, "_discover_redirect_url", new_callable=AsyncMock
        ) as mock_discover,
    ):
        # Now returns tuple (url, use_ssl)
        mock_discover.return_value = (None, True)

        async def create_and_set_session() -> None:
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_response
            mock_session = MagicMock()
            mock_session.post.return_value = mock_cm
            client._session = mock_session

        mock_create.side_effect = create_and_set_session

        await client._make_request({"query": "query { online }"})

        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_make_request_uses_cached_url():
    """Test _make_request uses cached resolved URL."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    expected_data = {"data": {"online": True}}

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_data)
    mock_response.raise_for_status = MagicMock()

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_response

    mock_session = MagicMock()
    mock_session.post.return_value = mock_cm

    # Pre-set the cached URL
    client._session = mock_session
    client._resolved_url = "https://cached.example.com/graphql"

    with patch.object(
        client, "_discover_redirect_url", new_callable=AsyncMock
    ) as mock_discover:
        await client._make_request({"query": "query { online }"})

        # Should not call discover since URL is cached
        mock_discover.assert_not_called()


@pytest.mark.asyncio
async def test_make_request_discovers_url_on_first_call():
    """Test _make_request discovers URL on first call."""
    from unittest.mock import MagicMock

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    expected_data = {"data": {"online": True}}

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_data)
    mock_response.raise_for_status = MagicMock()

    mock_cm_post = AsyncMock()
    mock_cm_post.__aenter__.return_value = mock_response

    mock_get_response = MagicMock()
    mock_get_response.status = 200

    mock_cm_get = AsyncMock()
    mock_cm_get.__aenter__.return_value = mock_get_response

    mock_session = MagicMock()
    mock_session.post.return_value = mock_cm_post
    mock_session.get.return_value = mock_cm_get

    client._session = mock_session
    # Don't set _resolved_url - it should be discovered

    await client._make_request({"query": "query { online }"})

    # URL should now be set
    assert client._resolved_url is not None


@pytest.mark.asyncio
async def test_close_does_nothing_if_session_not_owned():
    """Test close() doesn't close session if it was injected."""
    mock_session = AsyncMock(spec=aiohttp.ClientSession)

    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
        session=mock_session,  # Injected session
    )

    await client.close()

    # Should NOT close the injected session
    mock_session.close.assert_not_called()


@pytest.mark.asyncio
async def test_close_closes_owned_session():
    """Test close() closes session if we created it."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    # Create a mock session and set it directly
    mock_session = MagicMock()
    mock_session.close = AsyncMock()
    client._session = mock_session
    client._owns_session = True

    await client.close()

    mock_session.close.assert_called_once()
    assert client._session is None


@pytest.mark.asyncio
async def test_discover_redirect_url_raises_if_session_creation_fails():
    """Test _discover_redirect_url raises if session creation fails."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    with patch.object(client, "_create_session", new_callable=AsyncMock) as mock_create:
        # Simulate session creation failing (session remains None)
        mock_create.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            await client._discover_redirect_url()

        assert "Failed to create HTTP session" in str(exc_info.value)


@pytest.mark.asyncio
async def test_make_request_raises_if_session_creation_fails():
    """Test _make_request raises if session creation fails."""
    client = UnraidAPIClient(
        host="192.168.1.100",
        api_key="test_key",
    )

    with patch.object(client, "_create_session", new_callable=AsyncMock) as mock_create:
        # Simulate session creation failing (session remains None)
        mock_create.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            await client._make_request({"query": "query { online }"})

        assert "Failed to create HTTP session" in str(exc_info.value)
