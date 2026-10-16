"""Guard against re-introducing deprecated Home Assistant patterns (#358)."""

from __future__ import annotations

import inspect

import probatio
import pytest
from homeassistant.components.repairs import RepairsFlow
from homeassistant.const import UnitOfInformation, UnitOfRatio
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.unraid import config_flow, repairs, sensor


def _sensor_classes_with(attr: str, value: object) -> list[tuple[type, object]]:
    """
    Return (class, raw value) for sensor classes that set ``_attr_<attr>``.

    Home Assistant's ``CachedProperties`` metaclass turns ``_attr_*`` class
    attributes into properties and stores the raw value as ``__attr_*``.
    """
    found: list[tuple[type, object]] = []
    for _, cls in inspect.getmembers(sensor, inspect.isclass):
        if cls.__module__ != sensor.__name__:
            continue
        raw = cls.__dict__.get(f"__attr_{attr}")
        if raw == value:
            found.append((cls, raw))
    return found


def test_percentage_sensors_use_unit_of_ratio_enum() -> None:
    """Percentage sensors use UnitOfRatio.PERCENTAGE, which still reads "%"."""
    classes = _sensor_classes_with("native_unit_of_measurement", "%")
    assert len(classes) == 13
    for _cls, raw in classes:
        assert raw is UnitOfRatio.PERCENTAGE
    assert UnitOfRatio.PERCENTAGE == "%"


def test_storage_sensors_suggest_gibibytes_enum() -> None:
    """Storage sensors suggest UnitOfInformation.GIBIBYTES, which reads "GiB"."""
    classes = _sensor_classes_with("suggested_unit_of_measurement", "GiB")
    assert len(classes) == 6
    for _cls, raw in classes:
        assert raw is UnitOfInformation.GIBIBYTES
    assert UnitOfInformation.GIBIBYTES == "GiB"


@pytest.mark.parametrize("module", [config_flow, repairs])
def test_schemas_use_probatio(module: object) -> None:
    """Flows build schemas with Probatio, the HA 2026.9+ validation engine."""
    assert module.vol is probatio  # type: ignore[attr-defined]
    assert isinstance(module.vol.Schema({}), probatio.Schema)  # type: ignore[attr-defined]


async def test_repair_flow_steps_return_typed_results(hass: HomeAssistant) -> None:
    """Repair flow steps are annotated with and return RepairsFlowResult."""
    for step in ("async_step_init", "async_step_confirm"):
        hints = inspect.get_annotations(
            getattr(repairs.AuthFailedRepairFlow, step), eval_str=True
        )
        assert hints["return"].__name__ == "RepairsFlowResult"

    flow = repairs.AuthFailedRepairFlow()
    flow.hass = hass
    assert isinstance(flow, RepairsFlow)
    result = await flow.async_step_init()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert isinstance(result["data_schema"], probatio.Schema)


# ---------------------------------------------------------------------------
# Exception paths reformatted for Python 3.14 (PEP 758 ``except A, B:``)
# ---------------------------------------------------------------------------


def test_last_parity_check_date_invalid_string_returns_none() -> None:
    """An unparsable ISO date string is swallowed and yields no value."""
    from unittest.mock import MagicMock

    from unraid_api.models import ParityHistoryEntry

    from custom_components.unraid.coordinator import UnraidStorageCoordinator
    from tests.conftest import make_storage_data

    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(
        parity_history=[ParityHistoryEntry(date="not-a-date", status="OK")]
    )
    entity = sensor.LastParityCheckDateSensor(
        coordinator=coordinator, server_uuid="test-uuid", server_name="tower"
    )

    assert entity.native_value is None


def test_parity_speed_non_numeric_returns_none() -> None:
    """A non-numeric parity speed string yields no value instead of raising."""
    from unittest.mock import MagicMock

    from unraid_api.models import ParityCheck

    from custom_components.unraid.coordinator import UnraidStorageCoordinator
    from tests.conftest import make_storage_data

    coordinator = MagicMock(spec=UnraidStorageCoordinator)
    coordinator.data = make_storage_data(parity_status=ParityCheck(speed="fast"))
    entity = sensor.ParitySpeedSensor(
        coordinator=coordinator, server_uuid="test-uuid", server_name="tower"
    )

    assert entity.native_value is None


@pytest.mark.parametrize(
    "error_cls",
    [
        config_flow.InvalidAuthError,
        config_flow.CannotConnectError,
        config_flow.UnsupportedVersionError,
    ],
)
async def test_validate_connection_reraises_flow_errors(
    hass: HomeAssistant, error_cls: type[Exception]
) -> None:
    """Flow-level errors raised while fetching server info pass through as-is."""
    from unittest.mock import AsyncMock

    flow = config_flow.ConfigFlow()
    flow.hass = hass
    api_client = AsyncMock()
    error = error_cls("boom")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(flow, "_fetch_server_info", AsyncMock(side_effect=error))
        with pytest.raises(error_cls) as excinfo:
            await flow._validate_connection(api_client, "unraid.local")

    assert excinfo.value is error


# ---------------------------------------------------------------------------
# Every form the flows show is built with a Probatio schema
# ---------------------------------------------------------------------------


async def test_user_form_schema_is_probatio(hass: HomeAssistant) -> None:
    """The user step form is built from a Probatio schema."""
    from homeassistant import config_entries

    from custom_components.unraid.const import DOMAIN

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert isinstance(result["data_schema"], probatio.Schema)


@pytest.mark.parametrize(
    ("source", "step_id"),
    [("reauth", "reauth_confirm"), ("reconfigure", "reconfigure")],
)
async def test_entry_forms_schema_is_probatio(
    hass: HomeAssistant, source: str, step_id: str
) -> None:
    """The reauth and reconfigure forms are built from Probatio schemas."""
    from unittest.mock import patch

    from homeassistant.const import CONF_API_KEY, CONF_HOST
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.unraid.const import DOMAIN

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "old-key"},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.unraid.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source, "entry_id": entry.entry_id},
            data=dict(entry.data) if source == "reauth" else None,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == step_id
    assert isinstance(result["data_schema"], probatio.Schema)


async def test_options_form_schema_is_probatio(hass: HomeAssistant) -> None:
    """The options form is built from a Probatio schema."""
    from unittest.mock import patch

    from homeassistant.const import CONF_API_KEY, CONF_HOST
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.unraid.const import DOMAIN

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="tower",
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "key"},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.unraid.async_setup_entry", return_value=True):
        assert await hass.config_entries.async_setup(entry.entry_id)
        result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert isinstance(result["data_schema"], probatio.Schema)


async def test_repair_flow_submit_returns_typed_create_entry(
    hass: HomeAssistant,
) -> None:
    """Submitting the repair form yields a CREATE_ENTRY RepairsFlowResult."""
    from unittest.mock import patch

    from homeassistant.const import CONF_API_KEY, CONF_HOST
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.unraid.const import DOMAIN

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "unraid.local", CONF_API_KEY: "key"},
        unique_id="test-uuid",
    )
    entry.add_to_hass(hass)

    flow = repairs.AuthFailedRepairFlow()
    flow.hass = hass
    with patch.object(
        hass.config_entries.flow, "async_init", return_value={"flow_id": "x"}
    ) as mock_init:
        result = await flow.async_step_confirm(user_input={})
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {}
    mock_init.assert_called_once()
    assert mock_init.call_args.kwargs["context"]["entry_id"] == entry.entry_id


async def test_ups_energy_invalid_restored_state_is_ignored(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """A non-numeric restored UPS energy state logs a warning and starts at 0."""
    import logging
    from unittest.mock import MagicMock, patch

    from unraid_api.models import UPSDevice, UPSPower

    from custom_components.unraid.coordinator import UnraidSystemCoordinator
    from tests.conftest import make_system_data

    ups = UPSDevice(id="ups:1", name="APC", power=UPSPower(loadPercentage=50.0))
    coordinator = MagicMock(spec=UnraidSystemCoordinator)
    coordinator.data = make_system_data(ups_devices=[ups])
    coordinator.config_entry = MagicMock(entry_id="entry")
    entity = sensor.UPSEnergySensor(
        coordinator=coordinator,
        server_uuid="test-uuid",
        server_name="tower",
        ups=ups,
        ups_nominal_power=1000,
    )
    entity.hass = hass
    entity.entity_id = "sensor.test_ups_energy"
    last_state = MagicMock(state="not_a_number")

    with (
        patch.object(entity, "async_get_last_state", return_value=last_state),
        caplog.at_level(logging.WARNING),
    ):
        await entity.async_added_to_hass()

    assert entity._total_energy_kwh == 0.0
    assert "Could not restore UPS energy value" in caplog.text
