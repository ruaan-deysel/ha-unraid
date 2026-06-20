"""Tests for the Unraid stale-entity cleanup module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.unraid.cleanup import (
    _is_dynamic_resource_id,
    async_cleanup_stale_entities,
    build_expected_dynamic_unique_ids,
)
from custom_components.unraid.const import DOMAIN
from tests.conftest import make_storage_data, make_system_data

# Fake server UUID used throughout these tests
_UUID = "test-server-uuid"


# =============================================================================
# _is_dynamic_resource_id helpers
# =============================================================================


class TestIsDynamicResourceId:
    """Tests for the _is_dynamic_resource_id helper."""

    # ---- dynamic patterns that MUST return True ----

    def test_container_update_entity(self) -> None:
        """Update platform uses container_update_NAME pattern."""
        assert _is_dynamic_resource_id("container_update_myapp") is True

    def test_container_update_binary_sensor(self) -> None:
        """binary_sensor update uses container_{name}_update."""
        assert _is_dynamic_resource_id("container_myapp_update") is True

    def test_container_switch(self) -> None:
        assert _is_dynamic_resource_id("container_switch_myapp") is True

    def test_container_restart(self) -> None:
        assert _is_dynamic_resource_id("container_restart_myapp") is True

    def test_container_cpu_sensor(self) -> None:
        assert _is_dynamic_resource_id("container_myapp_cpu") is True

    def test_container_memory_sensor(self) -> None:
        assert _is_dynamic_resource_id("container_myapp_memory") is True

    def test_container_memory_pct_sensor(self) -> None:
        assert _is_dynamic_resource_id("container_myapp_memory_pct") is True

    def test_container_update_sensor(self) -> None:
        assert _is_dynamic_resource_id("container_myapp_update") is True

    def test_vm_switch(self) -> None:
        assert _is_dynamic_resource_id("vm_switch_myvm") is True

    def test_vm_force_stop(self) -> None:
        assert _is_dynamic_resource_id("vm_force_stop_myvm") is True

    def test_vm_reboot(self) -> None:
        assert _is_dynamic_resource_id("vm_reboot_myvm") is True

    def test_vm_pause(self) -> None:
        assert _is_dynamic_resource_id("vm_pause_myvm") is True

    def test_vm_resume(self) -> None:
        assert _is_dynamic_resource_id("vm_resume_myvm") is True

    def test_vm_reset(self) -> None:
        assert _is_dynamic_resource_id("vm_reset_myvm") is True

    def test_disk_temp(self) -> None:
        assert _is_dynamic_resource_id("disk_sda_temp") is True

    def test_disk_errors(self) -> None:
        assert _is_dynamic_resource_id("disk_sda_errors") is True

    def test_disk_usage(self) -> None:
        assert _is_dynamic_resource_id("disk_sda_usage") is True

    def test_disk_health(self) -> None:
        assert _is_dynamic_resource_id("disk_health_sda") is True

    def test_disk_spin(self) -> None:
        assert _is_dynamic_resource_id("disk_spin_sda") is True

    def test_share_usage(self) -> None:
        assert _is_dynamic_resource_id("share_media_usage") is True

    def test_ups_battery(self) -> None:
        assert _is_dynamic_resource_id("ups_ups1_battery") is True

    def test_ups_load(self) -> None:
        assert _is_dynamic_resource_id("ups_ups1_load") is True

    def test_ups_connected(self) -> None:
        assert _is_dynamic_resource_id("ups_ups1_connected") is True

    def test_temperature_sensor(self) -> None:
        assert _is_dynamic_resource_id("temp_coretemp_core_0") is True

    def test_network_rx(self) -> None:
        assert _is_dynamic_resource_id("network_eth0_rx") is True

    def test_network_tx(self) -> None:
        assert _is_dynamic_resource_id("network_bond0_tx") is True

    # ---- static patterns that MUST return False ----

    def test_cpu_usage(self) -> None:
        assert _is_dynamic_resource_id("cpu_usage") is False

    def test_ram_usage(self) -> None:
        assert _is_dynamic_resource_id("ram_usage") is False

    def test_array_state(self) -> None:
        assert _is_dynamic_resource_id("array_state") is False

    def test_array_switch(self) -> None:
        assert _is_dynamic_resource_id("array_switch") is False

    def test_parity_status(self) -> None:
        assert _is_dynamic_resource_id("parity_status") is False

    def test_temperature_average_is_static(self) -> None:
        """temperature_average must never be treated as dynamic."""
        assert _is_dynamic_resource_id("temperature_average") is False

    def test_cpu_temp_is_static(self) -> None:
        """cpu_temp (legacy scalar) must not be treated as dynamic."""
        assert _is_dynamic_resource_id("cpu_temp") is False

    def test_container_updates_count_is_static(self) -> None:
        """container_updates_count is a static aggregate sensor."""
        assert _is_dynamic_resource_id("container_updates_count") is False

    def test_network_access_is_static(self) -> None:
        """network_access (infra sensor) must not be treated as dynamic."""
        assert _is_dynamic_resource_id("network_access") is False

    def test_registration_type(self) -> None:
        assert _is_dynamic_resource_id("registration_type") is False

    def test_cloud_connected(self) -> None:
        assert _is_dynamic_resource_id("cloud_connected") is False

    def test_mover_active(self) -> None:
        assert _is_dynamic_resource_id("mover_active") is False

    def test_update_all_containers_is_static(self) -> None:
        assert _is_dynamic_resource_id("update_all_containers") is False

    def test_check_container_updates_is_static(self) -> None:
        assert _is_dynamic_resource_id("check_container_updates") is False

    def test_docker_total_cpu_is_static(self) -> None:
        assert _is_dynamic_resource_id("docker_total_cpu") is False

    def test_unraid_version_is_static(self) -> None:
        assert _is_dynamic_resource_id("unraid_version") is False


# =============================================================================
# build_expected_dynamic_unique_ids
# =============================================================================


class TestBuildExpectedDynamicUniqueIds:
    """Tests for the expected-set builder."""

    def test_empty_data_returns_empty_set(self) -> None:
        sys_data = make_system_data()
        stor_data = make_storage_data()
        result = build_expected_dynamic_unique_ids(_UUID, sys_data, stor_data)
        assert result == frozenset()

    def test_single_container(self) -> None:
        from unraid_api.models import DockerContainer

        container = MagicMock(spec=DockerContainer)
        container.name = "/myapp"
        container.id = "abc123"
        container.is_running = True

        sys_data = make_system_data(containers=[container])
        stor_data = make_storage_data()
        result = build_expected_dynamic_unique_ids(_UUID, sys_data, stor_data)

        assert f"{_UUID}_container_switch_myapp" in result
        assert f"{_UUID}_container_restart_myapp" in result
        assert f"{_UUID}_container_myapp_cpu" in result
        assert f"{_UUID}_container_myapp_memory" in result
        assert f"{_UUID}_container_myapp_memory_pct" in result
        assert f"{_UUID}_container_myapp_update" in result
        # update platform entity (different pattern from binary_sensor)
        assert f"{_UUID}_container_update_myapp" in result

    def test_single_vm(self) -> None:
        from unraid_api.models import VmDomain

        vm = MagicMock(spec=VmDomain)
        vm.name = "windows11"
        vm.id = "vm-1"

        sys_data = make_system_data(vms=[vm])
        stor_data = make_storage_data()
        result = build_expected_dynamic_unique_ids(_UUID, sys_data, stor_data)

        assert f"{_UUID}_vm_switch_windows11" in result
        assert f"{_UUID}_vm_force_stop_windows11" in result
        assert f"{_UUID}_vm_reboot_windows11" in result
        assert f"{_UUID}_vm_pause_windows11" in result
        assert f"{_UUID}_vm_resume_windows11" in result
        assert f"{_UUID}_vm_reset_windows11" in result

    def test_single_ups(self) -> None:
        from unraid_api.models import UPSDevice

        ups = MagicMock(spec=UPSDevice)
        ups.id = "ups1"
        ups.name = "APC"

        sys_data = make_system_data(ups_devices=[ups])
        stor_data = make_storage_data()
        result = build_expected_dynamic_unique_ids(_UUID, sys_data, stor_data)

        for suffix in (
            "battery",
            "load",
            "runtime",
            "power",
            "energy",
            "input_voltage",
            "output_voltage",
            "battery_health",
            "status",
            "connected",
        ):
            assert f"{_UUID}_ups_ups1_{suffix}" in result

    def test_disk_sensor_ids(self) -> None:
        from unraid_api.models import ArrayDisk

        disk = MagicMock(spec=ArrayDisk)
        disk.id = "sdb"

        stor_data = make_storage_data(disks=[disk])
        sys_data = make_system_data()
        result = build_expected_dynamic_unique_ids(_UUID, sys_data, stor_data)

        assert f"{_UUID}_disk_sdb_temp" in result
        assert f"{_UUID}_disk_sdb_errors" in result
        assert f"{_UUID}_disk_sdb_usage" in result
        assert f"{_UUID}_disk_health_sdb" in result
        assert f"{_UUID}_disk_spin_sdb" in result

    def test_parity_disk_ids(self) -> None:
        from unraid_api.models import ArrayDisk

        parity = MagicMock(spec=ArrayDisk)
        parity.id = "sda"

        stor_data = make_storage_data(parities=[parity])
        sys_data = make_system_data()
        result = build_expected_dynamic_unique_ids(_UUID, sys_data, stor_data)

        assert f"{_UUID}_disk_sda_temp" in result
        assert f"{_UUID}_disk_health_sda" in result

    def test_cache_disk_ids(self) -> None:
        from unraid_api.models import ArrayDisk

        cache = MagicMock(spec=ArrayDisk)
        cache.id = "nvme0n1"

        stor_data = make_storage_data(caches=[cache])
        sys_data = make_system_data()
        result = build_expected_dynamic_unique_ids(_UUID, sys_data, stor_data)

        assert f"{_UUID}_disk_nvme0n1_temp" in result

    def test_share_sensor_ids(self) -> None:
        from unraid_api.models import Share

        share = MagicMock(spec=Share)
        share.id = "media"

        stor_data = make_storage_data(shares=[share])
        sys_data = make_system_data()
        result = build_expected_dynamic_unique_ids(_UUID, sys_data, stor_data)

        assert f"{_UUID}_share_media_usage" in result

    def test_disk_with_none_id_skipped(self) -> None:
        from unraid_api.models import ArrayDisk

        disk = MagicMock(spec=ArrayDisk)
        disk.id = None

        stor_data = make_storage_data(disks=[disk])
        sys_data = make_system_data()
        result = build_expected_dynamic_unique_ids(_UUID, sys_data, stor_data)
        # No disk_* entries should be added for a disk with id=None
        assert not any("disk_" in uid for uid in result)

    def test_network_interface_ids(self) -> None:
        iface = MagicMock()
        iface.name = "eth0"

        sys_data = make_system_data()
        sys_data.network_metrics = [iface]  # type: ignore[assignment]
        stor_data = make_storage_data()
        result = build_expected_dynamic_unique_ids(_UUID, sys_data, stor_data)

        assert f"{_UUID}_network_eth0_rx" in result
        assert f"{_UUID}_network_eth0_tx" in result


# =============================================================================
# async_cleanup_stale_entities
# =============================================================================


_SENTINEL = object()


class TestAsyncCleanupStaleEntities:
    """Integration-level tests for the full cleanup function."""

    def _make_system_coordinator(
        self,
        *,
        last_update_success: bool = True,
        data_override: object = _SENTINEL,
    ) -> MagicMock:
        coord = MagicMock()
        coord.last_update_success = last_update_success
        coord.data = make_system_data() if data_override is _SENTINEL else data_override
        return coord

    def _make_storage_coordinator(
        self,
        *,
        last_update_success: bool = True,
        data_override: object = _SENTINEL,
    ) -> MagicMock:
        coord = MagicMock()
        coord.last_update_success = last_update_success
        coord.data = (
            make_storage_data() if data_override is _SENTINEL else data_override
        )
        return coord

    def _make_entity_entry(self, unique_id: str, entity_id: str) -> MagicMock:
        entry = MagicMock()
        entry.unique_id = unique_id
        entry.entity_id = entity_id
        return entry

    async def test_skips_cleanup_when_system_update_failed(
        self, hass: HomeAssistant
    ) -> None:
        """No entities should be pruned when the system coordinator update failed."""
        sys_coord = self._make_system_coordinator(last_update_success=False)
        stor_coord = self._make_storage_coordinator()

        with patch("custom_components.unraid.cleanup.er.async_get") as mock_reg:
            async_cleanup_stale_entities(hass, "entry1", _UUID, sys_coord, stor_coord)
            # The entity registry should never be queried
            mock_reg.assert_not_called()

    async def test_skips_cleanup_when_storage_update_failed(
        self, hass: HomeAssistant
    ) -> None:
        """No entities should be pruned when the storage coordinator update failed."""
        sys_coord = self._make_system_coordinator()
        stor_coord = self._make_storage_coordinator(last_update_success=False)

        with patch("custom_components.unraid.cleanup.er.async_get") as mock_reg:
            async_cleanup_stale_entities(hass, "entry1", _UUID, sys_coord, stor_coord)
            mock_reg.assert_not_called()

    async def test_skips_cleanup_when_coordinator_data_none(
        self, hass: HomeAssistant
    ) -> None:
        """No cleanup when coordinator data is None."""
        sys_coord = self._make_system_coordinator(data_override=None)
        stor_coord = self._make_storage_coordinator()

        with patch("custom_components.unraid.cleanup.er.async_get") as mock_reg:
            async_cleanup_stale_entities(hass, "entry1", _UUID, sys_coord, stor_coord)
            mock_reg.assert_not_called()

    async def test_skips_cleanup_when_coordinator_data_wrong_type(
        self, hass: HomeAssistant
    ) -> None:
        """No cleanup when coordinator data is an unexpected type (e.g. mock dict)."""
        sys_coord = self._make_system_coordinator(data_override={})
        stor_coord = self._make_storage_coordinator()

        with patch("custom_components.unraid.cleanup.er.async_get") as mock_reg:
            async_cleanup_stale_entities(hass, "entry1", _UUID, sys_coord, stor_coord)
            mock_reg.assert_not_called()

    async def test_removes_orphaned_container_entity(self, hass: HomeAssistant) -> None:
        """Entities for a deleted container should be removed."""
        # System data has NO containers
        sys_coord = self._make_system_coordinator(data_override=make_system_data())
        stor_coord = self._make_storage_coordinator()

        orphan_switch = self._make_entity_entry(
            f"{_UUID}_container_switch_oldapp",
            "switch.server_oldapp",
        )
        orphan_cpu = self._make_entity_entry(
            f"{_UUID}_container_oldapp_cpu",
            "sensor.server_oldapp_cpu",
        )
        static_entity = self._make_entity_entry(
            f"{_UUID}_cpu_usage",
            "sensor.server_cpu",
        )

        mock_reg = MagicMock()
        mock_reg.async_entries_for_config_entry.return_value = [
            orphan_switch,
            orphan_cpu,
            static_entity,
        ]
        mock_dev_reg = MagicMock()
        mock_dev_reg.async_entries_for_config_entry.return_value = []

        with (
            patch(
                "custom_components.unraid.cleanup.er.async_get", return_value=mock_reg
            ),
            patch(
                "custom_components.unraid.cleanup.er.async_entries_for_config_entry",
                return_value=[orphan_switch, orphan_cpu, static_entity],
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_get",
                return_value=mock_dev_reg,
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_entries_for_config_entry",
                return_value=[],
            ),
        ):
            async_cleanup_stale_entities(hass, "entry1", _UUID, sys_coord, stor_coord)

        # Orphaned container entities removed; static entity untouched
        removed_ids = {call[0][0] for call in mock_reg.async_remove.call_args_list}
        assert "switch.server_oldapp" in removed_ids
        assert "sensor.server_oldapp_cpu" in removed_ids
        assert "sensor.server_cpu" not in removed_ids

    async def test_does_not_remove_existing_container_entity(
        self, hass: HomeAssistant
    ) -> None:
        """Entities for a live container must be preserved."""
        from unraid_api.models import DockerContainer

        container = MagicMock(spec=DockerContainer)
        container.name = "/liveapp"
        container.id = "abc"
        container.is_running = True

        sys_data = make_system_data(containers=[container])
        sys_coord = self._make_system_coordinator(data_override=sys_data)
        stor_coord = self._make_storage_coordinator()

        live_switch = self._make_entity_entry(
            f"{_UUID}_container_switch_liveapp",
            "switch.server_liveapp",
        )

        mock_reg = MagicMock()
        mock_dev_reg = MagicMock()
        mock_dev_reg.async_entries_for_config_entry.return_value = []

        with (
            patch(
                "custom_components.unraid.cleanup.er.async_get", return_value=mock_reg
            ),
            patch(
                "custom_components.unraid.cleanup.er.async_entries_for_config_entry",
                return_value=[live_switch],
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_get",
                return_value=mock_dev_reg,
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_entries_for_config_entry",
                return_value=[],
            ),
        ):
            async_cleanup_stale_entities(hass, "entry1", _UUID, sys_coord, stor_coord)

        mock_reg.async_remove.assert_not_called()

    async def test_removes_orphaned_disk_entities(self, hass: HomeAssistant) -> None:
        """Entities for a removed disk should be pruned."""
        # Storage data has no disks
        sys_coord = self._make_system_coordinator()
        stor_coord = self._make_storage_coordinator(
            data_override=make_storage_data(disks=[])
        )

        orphan_temp = self._make_entity_entry(
            f"{_UUID}_disk_sdb_temp",
            "sensor.server_disk_sdb_temp",
        )
        orphan_health = self._make_entity_entry(
            f"{_UUID}_disk_health_sdb",
            "binary_sensor.server_disk_sdb_health",
        )

        mock_reg = MagicMock()
        mock_dev_reg = MagicMock()
        mock_dev_reg.async_entries_for_config_entry.return_value = []

        with (
            patch(
                "custom_components.unraid.cleanup.er.async_get", return_value=mock_reg
            ),
            patch(
                "custom_components.unraid.cleanup.er.async_entries_for_config_entry",
                return_value=[orphan_temp, orphan_health],
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_get",
                return_value=mock_dev_reg,
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_entries_for_config_entry",
                return_value=[],
            ),
        ):
            async_cleanup_stale_entities(hass, "entry1", _UUID, sys_coord, stor_coord)

        removed_ids = {call[0][0] for call in mock_reg.async_remove.call_args_list}
        assert "sensor.server_disk_sdb_temp" in removed_ids
        assert "binary_sensor.server_disk_sdb_health" in removed_ids

    async def test_removes_orphaned_share_entity(self, hass: HomeAssistant) -> None:
        """Entities for a deleted share should be pruned."""
        sys_coord = self._make_system_coordinator()
        stor_coord = self._make_storage_coordinator(
            data_override=make_storage_data(shares=[])
        )

        orphan_share = self._make_entity_entry(
            f"{_UUID}_share_movies_usage",
            "sensor.server_share_movies_usage",
        )

        mock_reg = MagicMock()
        mock_dev_reg = MagicMock()
        mock_dev_reg.async_entries_for_config_entry.return_value = []

        with (
            patch(
                "custom_components.unraid.cleanup.er.async_get", return_value=mock_reg
            ),
            patch(
                "custom_components.unraid.cleanup.er.async_entries_for_config_entry",
                return_value=[orphan_share],
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_get",
                return_value=mock_dev_reg,
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_entries_for_config_entry",
                return_value=[],
            ),
        ):
            async_cleanup_stale_entities(hass, "entry1", _UUID, sys_coord, stor_coord)

        mock_reg.async_remove.assert_called_once_with(
            "sensor.server_share_movies_usage"
        )

    async def test_static_entities_never_removed(self, hass: HomeAssistant) -> None:
        """Static entities (cpu_usage, array_state, etc.) must never be pruned."""
        sys_coord = self._make_system_coordinator()
        stor_coord = self._make_storage_coordinator()

        static_entities = [
            self._make_entity_entry(f"{_UUID}_{rid}", f"sensor.x_{rid}")
            for rid in (
                "cpu_usage",
                "ram_usage",
                "array_state",
                "temperature_average",
                "network_access",
                "container_updates_count",
                "docker_total_cpu",
                "parity_status",
                "registration_type",
                "mover_active",
                "update_all_containers",
            )
        ]

        mock_reg = MagicMock()
        mock_dev_reg = MagicMock()
        mock_dev_reg.async_entries_for_config_entry.return_value = []

        with (
            patch(
                "custom_components.unraid.cleanup.er.async_get", return_value=mock_reg
            ),
            patch(
                "custom_components.unraid.cleanup.er.async_entries_for_config_entry",
                return_value=static_entities,
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_get",
                return_value=mock_dev_reg,
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_entries_for_config_entry",
                return_value=[],
            ),
        ):
            async_cleanup_stale_entities(hass, "entry1", _UUID, sys_coord, stor_coord)

        mock_reg.async_remove.assert_not_called()

    async def test_entities_from_different_server_ignored(
        self, hass: HomeAssistant
    ) -> None:
        """Entities whose unique_id prefix doesn't match server_uuid are untouched."""
        sys_coord = self._make_system_coordinator()
        stor_coord = self._make_storage_coordinator()

        foreign_entity = self._make_entity_entry(
            "other-uuid_container_switch_foo",
            "switch.other_server_foo",
        )

        mock_reg = MagicMock()
        mock_dev_reg = MagicMock()
        mock_dev_reg.async_entries_for_config_entry.return_value = []

        with (
            patch(
                "custom_components.unraid.cleanup.er.async_get", return_value=mock_reg
            ),
            patch(
                "custom_components.unraid.cleanup.er.async_entries_for_config_entry",
                return_value=[foreign_entity],
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_get",
                return_value=mock_dev_reg,
            ),
            patch(
                "custom_components.unraid.cleanup.dr.async_entries_for_config_entry",
                return_value=[],
            ),
        ):
            async_cleanup_stale_entities(hass, "entry1", _UUID, sys_coord, stor_coord)

        mock_reg.async_remove.assert_not_called()


# =============================================================================
# async_remove_config_entry_device (in __init__.py)
# =============================================================================


class TestAsyncRemoveConfigEntryDevice:
    """Tests for the async_remove_config_entry_device function."""

    async def test_main_server_device_cannot_be_removed(
        self, hass: HomeAssistant
    ) -> None:
        """The Unraid server device must not be removable via the UI."""
        from custom_components.unraid import async_remove_config_entry_device

        entry = MagicMock()
        entry.runtime_data.server_info = {"uuid": _UUID}

        device = MagicMock()
        device.identifiers = {(DOMAIN, _UUID)}

        result = await async_remove_config_entry_device(hass, entry, device)
        assert result is False

    async def test_other_device_can_be_removed(self, hass: HomeAssistant) -> None:
        """Any non-server device can be removed from the UI."""
        from custom_components.unraid import async_remove_config_entry_device

        entry = MagicMock()
        entry.runtime_data.server_info = {"uuid": _UUID}

        device = MagicMock()
        device.identifiers = {(DOMAIN, "some-other-device-id")}

        result = await async_remove_config_entry_device(hass, entry, device)
        assert result is True
