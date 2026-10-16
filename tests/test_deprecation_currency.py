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
