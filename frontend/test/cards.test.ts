import { describe, expect, it } from "vitest";
import "../src/index";
import { UnraidServerCard } from "../src/server-card";
import { UnraidStorageCard, formatDiskName } from "../src/storage-card";
import { UnraidSharesCard, formatShareName } from "../src/shares-card";
import { UnraidDockerCard } from "../src/docker-card";
import { UnraidUpsCard } from "../src/ups-card";
import { UnraidVmCard } from "../src/vm-card";
import { UnraidDashboardCard } from "../src/dashboard-card";
import { UnraidNetworkCard } from "../src/network-card";
import {
  UnraidNetworkCardEditor,
  UnraidServerCardEditor,
  UnraidSharesCardEditor,
} from "../src/dashboard-cards-editor";
import type { HomeAssistant } from "../src/ha-types";

function createMockHass(): HomeAssistant {
  return {
    states: {
      "sensor.cube_cpu_usage": {
        entity_id: "sensor.cube_cpu_usage",
        state: "15",
        attributes: {
          friendly_name: "CUBE CPU Usage",
          cpu_model: "Intel i7-8700K",
          cpu_cores: 6,
          cpu_threads: 12,
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_ram_usage": {
        entity_id: "sensor.cube_ram_usage",
        state: "25",
        attributes: {
          friendly_name: "CUBE RAM Usage",
          used: "8 GiB",
          total: "32 GiB",
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_array_usage": {
        entity_id: "sensor.cube_array_usage",
        state: "10",
        attributes: {
          friendly_name: "CUBE Array Usage",
          capacity_used: "4 TB",
          capacity_total: "40 TB",
          capacity_free: "36 TB",
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_array_state": {
        entity_id: "sensor.cube_array_state",
        state: "Started",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_parity_status": {
        entity_id: "binary_sensor.cube_parity_status",
        state: "on",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_disk_disk1_usage": {
        entity_id: "sensor.cube_disk_disk1_usage",
        state: "12",
        attributes: {
          friendly_name: "Cube Disk disk1 usage",
          status: "DISK_OK",
          num_errors: 0,
          spin_state: "active",
        },
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_disk_disk1_health": {
        entity_id: "binary_sensor.cube_disk_disk1_health",
        state: "off",
        attributes: { status: "DISK_OK" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_disk_disk1_temperature": {
        entity_id: "sensor.cube_disk_disk1_temperature",
        state: "32",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "switch.cube_disk_disk1_spin": {
        entity_id: "switch.cube_disk_disk1_spin",
        state: "on",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_share_appdata_usage": {
        entity_id: "sensor.cube_share_appdata_usage",
        state: "9.7",
        attributes: {
          friendly_name: "Cube Share appdata usage",
          used: "46.6 GB",
          total: "480.6 GB",
          free: "434.0 GB",
          color: "yellow-on",
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_share_media_usage": {
        entity_id: "sensor.cube_share_media_usage",
        state: "45.0",
        attributes: {
          friendly_name: "Cube Share media usage",
          used: "18.0 TB",
          total: "40.0 TB",
          free: "22.0 TB",
          color: "green-on",
        },
        last_changed: "",
        last_updated: "",
      },
      "switch.cube_docker_container_plex": {
        entity_id: "switch.cube_docker_container_plex",
        state: "on",
        attributes: { friendly_name: "plex" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_ups_battery": {
        entity_id: "sensor.cube_ups_battery",
        state: "100",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_ups_load": {
        entity_id: "sensor.cube_ups_load",
        state: "15",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "switch.cube_virtual_machine_ha": {
        entity_id: "switch.cube_virtual_machine_ha",
        state: "on",
        attributes: { friendly_name: "Home Assistant" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_disk_flash_usage": {
        entity_id: "sensor.cube_disk_flash_usage",
        state: "8",
        attributes: {
          friendly_name: "Cube Disk flash usage",
          status: "DISK_OK",
          num_errors: 0,
          device: "sdb",
          fs_size: "31.4 GB",
          fs_used: "2.68 GB",
          fs_free: "28.7 GB",
        },
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_disk_flash_health": {
        entity_id: "binary_sensor.cube_disk_flash_health",
        state: "off",
        attributes: { status: "DISK_OK" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_network_eth0_ip_address": {
        entity_id: "sensor.cube_network_eth0_ip_address",
        state: "192.168.20.21",
        attributes: {
          friendly_name: "Cube Network eth0 IP",
          mac_address: "00:11:22:33:44:55",
          mtu: 1500,
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_network_eth0_speed": {
        entity_id: "sensor.cube_network_eth0_speed",
        state: "1000",
        attributes: { unit_of_measurement: "Mbps" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_network_eth0_rx_throughput": {
        entity_id: "sensor.cube_network_eth0_rx_throughput",
        state: "12.4",
        attributes: { total_received: "1.2 GB" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_network_eth0_tx_throughput": {
        entity_id: "sensor.cube_network_eth0_tx_throughput",
        state: "5.8",
        attributes: { total_sent: "650 MB" },
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_network_eth0_link": {
        entity_id: "binary_sensor.cube_network_eth0_link",
        state: "on",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_network_access": {
        entity_id: "sensor.cube_network_access",
        state: "http://192.168.20.21",
        attributes: {
          LAN_IPv4_ipv4: "http://192.168.20.21",
          FQDN_LAN_ipv4: "https://cube.myunraid.net",
        },
        last_changed: "",
        last_updated: "",
      },
    },
    devices: {
      dev_1: {
        id: "dev_1",
        name: "CUBE",
        identifiers: [["unraid", "uuid-1234"]],
        model: "Fractal Node 304",
        sw_version: "6.12.10",
      },
    },
    entities: {},
    callService: async () => Promise.resolve(),
  };
}

describe("Unraid Custom Cards", () => {
  it("registers all cards in window.customCards", () => {
    expect(window.customCards).toBeDefined();
    const tags = window.customCards?.map((c) => c.type);
    expect(tags).toContain("unraid-server-card");
    expect(tags).toContain("unraid-storage-card");
    expect(tags).toContain("unraid-shares-card");
    expect(tags).toContain("unraid-docker-card");
    expect(tags).toContain("unraid-ups-card");
    expect(tags).toContain("unraid-vm-card");
    expect(tags).toContain("unraid-network-card");
    expect(tags).toContain("unraid-dashboard-card");
  });

  it("formats disk and share names cleanly", () => {
    expect(formatDiskName("Cube Disk disk1 usage", "disk1")).toBe("Disk 1");
    expect(formatDiskName("Tower Disk cache usage", "cache")).toBe("Cache");
    expect(formatDiskName("Cube Disk parity health", "parity")).toBe("Parity");
    expect(formatDiskName("Cube Disk flash usage", "flash")).toBe("Flash (Boot)");
    expect(formatDiskName("disk_2", "disk_2")).toBe("Disk 2");

    expect(formatShareName("Cube Share appdata usage", "appdata")).toBe("appdata");
    expect(formatShareName("Media Share", "media")).toBe("Media");
  });

  it("renders UnraidServerCard with mock hass data and formats numeric uptime", async () => {
    const card = new UnraidServerCard();
    card.setConfig({ type: "custom:unraid-server-card" });
    const hass = createMockHass();
    hass.states["sensor.cube_uptime"] = {
      entity_id: "sensor.cube_uptime",
      state: "90000",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    card.hass = hass;
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.getCardSize()).toBe(4);
    expect(card.getGridOptions().columns).toBe(6);
    expect(card.shadowRoot?.innerHTML).toContain("CUBE");
    expect(card.shadowRoot?.innerHTML).toContain("CPU Load");
    expect(card.shadowRoot?.innerHTML).toContain("15%");
    expect(card.shadowRoot?.innerHTML).toContain("1d 1h");
    expect(card.shadowRoot?.innerHTML).toContain("192.168.20.21");
    expect(card.shadowRoot?.innerHTML).toContain("Boot Device");
    expect(card.shadowRoot?.innerHTML).toContain("Flash");
    document.body.removeChild(card);
  });

  it("renders UnraidStorageCard with clean disk names and Healthy badge", async () => {
    const card = new UnraidStorageCard();
    card.setConfig({ type: "custom:unraid-storage-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Storage Array &amp; Disks");
    expect(card.shadowRoot?.innerHTML).toContain("Disk 1");
    expect(card.shadowRoot?.innerHTML).toContain("Flash (Boot)");
    expect(card.shadowRoot?.innerHTML).toContain("Healthy");
    expect(card.shadowRoot?.innerHTML).toContain("Active");
    expect(card.shadowRoot?.innerHTML).toContain("32°C");
    document.body.removeChild(card);
  });

  it("renders UnraidSharesCard and handles protection states", async () => {
    const card = new UnraidSharesCard();
    card.setConfig({ type: "custom:unraid-shares-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("User Shares");
    expect(card.shadowRoot?.innerHTML).toContain("appdata");
    expect(card.shadowRoot?.innerHTML).toContain("media");
    expect(card.shadowRoot?.innerHTML).toContain("Protected");
    expect(card.shadowRoot?.innerHTML).toContain("46.6 GB");
    expect(card.shadowRoot?.innerHTML).toContain("480.6 GB");
    document.body.removeChild(card);
  });

  it("renders UnraidDockerCard and container list excluding autostart switches", async () => {
    const card = new UnraidDockerCard();
    card.setConfig({ type: "custom:unraid-docker-card", view_mode: "list" });
    const hass = createMockHass();
    hass.states["switch.cube_docker_container_autostart_plex"] = {
      entity_id: "switch.cube_docker_container_autostart_plex",
      state: "on",
      attributes: { friendly_name: "plex Autostart" },
      last_changed: "",
      last_updated: "",
    };
    card.hass = hass;
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Docker Containers");
    expect(card.shadowRoot?.innerHTML).toContain("plex");
    expect(card.shadowRoot?.innerHTML).not.toContain("plex Autostart");
    document.body.removeChild(card);
  });

  it("renders UnraidUpsCard with battery and load", async () => {
    const card = new UnraidUpsCard();
    card.setConfig({ type: "custom:unraid-ups-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("UPS Power &amp; Battery");
    expect(card.shadowRoot?.innerHTML).toContain("100%");
    document.body.removeChild(card);
  });

  it("renders UnraidVmCard with virtual machines", async () => {
    const card = new UnraidVmCard();
    card.setConfig({ type: "custom:unraid-vm-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Virtual Machines");
    expect(card.shadowRoot?.innerHTML).toContain("Home Assistant");
    document.body.removeChild(card);
  });

  it("renders UnraidDashboardCard with tabs", async () => {
    const card = new UnraidDashboardCard();
    card.setConfig({ type: "custom:unraid-dashboard-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Unified Unraid Control Center");
    expect(card.shadowRoot?.innerHTML).toContain("Shares");
    document.body.removeChild(card);
  });

  it("renders UnraidServerCardEditor and updates config", async () => {
    const editor = new UnraidServerCardEditor();
    editor.setConfig({ type: "custom:unraid-server-card", title: "My Tower" });
    editor.hass = createMockHass();
    document.body.appendChild(editor);
    await editor.updateComplete;

    expect(editor.shadowRoot?.innerHTML).toContain("Unraid Server");
    expect(editor.shadowRoot?.innerHTML).toContain("Custom Title");
    document.body.removeChild(editor);
  });

  it("renders UnraidSharesCardEditor", async () => {
    const editor = new UnraidSharesCardEditor();
    editor.setConfig({ type: "custom:unraid-shares-card", title: "My Shares" });
    editor.hass = createMockHass();
    document.body.appendChild(editor);
    await editor.updateComplete;

    expect(editor.shadowRoot?.innerHTML).toContain("Unraid Server");
    expect(editor.shadowRoot?.innerHTML).toContain("Custom Title");
    document.body.removeChild(editor);
  });

  it("renders UnraidServerCard with ISO timestamp uptime", async () => {
    const card = new UnraidServerCard();
    card.setConfig({ type: "custom:unraid-server-card" });
    const hass = createMockHass();
    const threeHoursAgo = new Date(Date.now() - 3 * 3600 * 1000 - 15 * 60 * 1000).toISOString();
    hass.states["sensor.cube_up_since"] = {
      entity_id: "sensor.cube_up_since",
      state: threeHoursAgo,
      attributes: { friendly_name: "Cube Up since" },
      last_changed: "",
      last_updated: "",
    };
    card.hass = hass;
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("3h 15m");
    document.body.removeChild(card);
  });

  it("renders UnraidNetworkCard with interface list and traffic metrics", async () => {
    const card = new UnraidNetworkCard();
    card.setConfig({ type: "custom:unraid-network-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Network");
    expect(card.shadowRoot?.innerHTML).toContain("eth0");
    expect(card.shadowRoot?.innerHTML).toContain("192.168.20.21");
    expect(card.shadowRoot?.innerHTML).toContain("1 Gbps");
    expect(card.shadowRoot?.innerHTML).toContain("12.40 MB/s");
    expect(card.shadowRoot?.innerHTML).toContain("5.80 MB/s");
    expect(card.shadowRoot?.innerHTML).toContain("1 Connected");
    document.body.removeChild(card);
  });

  it("handles shares with missing color attribute and clamps usage percentage", async () => {
    const card = new UnraidSharesCard();
    card.setConfig({ type: "custom:unraid-shares-card" });
    const hass = createMockHass();
    // Add a share with missing color and >100% usage
    hass.states["sensor.cube_share_unprotected_usage"] = {
      entity_id: "sensor.cube_share_unprotected_usage",
      state: "105.0",
      attributes: {
        friendly_name: "Cube Share unprotected usage",
        used: "10.5 TB",
        total: "10.0 TB",
        free: "0 TB",
      },
      last_changed: "",
      last_updated: "",
    };
    card.hass = hass;
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("unprotected");
    expect(card.shadowRoot?.innerHTML).toContain("Unprotected");
    // Verify width is clamped to 100%
    expect(card.shadowRoot?.innerHTML).toContain("width: 100%");
    document.body.removeChild(card);
  });

  it("filters placeholder IP states from connected count and formats small data rates", async () => {
    const card = new UnraidNetworkCard();
    card.setConfig({ type: "custom:unraid-network-card" });
    const hass = createMockHass();
    // Add an unavailable interface
    hass.states["sensor.cube_network_eth1_ip_address"] = {
      entity_id: "sensor.cube_network_eth1_ip_address",
      state: "unavailable",
      attributes: { friendly_name: "Cube Network eth1 IP" },
      last_changed: "",
      last_updated: "",
    };
    hass.states["binary_sensor.cube_network_eth1_link"] = {
      entity_id: "binary_sensor.cube_network_eth1_link",
      state: "off",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    hass.states["sensor.cube_network_eth1_rx_throughput"] = {
      entity_id: "sensor.cube_network_eth1_rx_throughput",
      state: "0.05", // 0.05 MB/s = 50.0 kB/s
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    card.hass = hass;
    document.body.appendChild(card);
    await card.updateComplete;

    // eth0 is connected, eth1 is unavailable/off -> still 1 connected
    expect(card.shadowRoot?.innerHTML).toContain("1 Connected");
    expect(card.shadowRoot?.innerHTML).toContain("50.0 kB/s");
    expect(card.shadowRoot?.innerHTML).not.toContain("unavailable");
    document.body.removeChild(card);
  });

  it("renders UnraidNetworkCardEditor", async () => {
    const editor = new UnraidNetworkCardEditor();
    editor.setConfig({ type: "custom:unraid-network-card", title: "My Network" });
    editor.hass = createMockHass();
    document.body.appendChild(editor);
    await editor.updateComplete;

    expect(editor.shadowRoot?.innerHTML).toContain("Unraid Server");
    expect(editor.shadowRoot?.innerHTML).toContain("Custom Title");
    document.body.removeChild(editor);
  });
});
