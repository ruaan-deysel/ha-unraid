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
