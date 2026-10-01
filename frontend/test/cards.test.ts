import { describe, expect, it } from "vitest";
import "../src/index";
import { UnraidServerCard } from "../src/server-card";
import { UnraidStorageCard } from "../src/storage-card";
import { UnraidDockerCard } from "../src/docker-card";
import { UnraidUpsCard } from "../src/ups-card";
import { UnraidVmCard } from "../src/vm-card";
import { UnraidDashboardCard } from "../src/dashboard-card";
import { UnraidServerCardEditor } from "../src/dashboard-cards-editor";
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
      "sensor.cube_disk_1_usage": {
        entity_id: "sensor.cube_disk_1_usage",
        state: "12",
        attributes: { friendly_name: "Disk 1" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_disk_1_temperature": {
        entity_id: "sensor.cube_disk_1_temperature",
        state: "32",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "switch.cube_disk_1_spin": {
        entity_id: "switch.cube_disk_1_spin",
        state: "on",
        attributes: {},
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
    expect(tags).toContain("unraid-docker-card");
    expect(tags).toContain("unraid-ups-card");
    expect(tags).toContain("unraid-vm-card");
    expect(tags).toContain("unraid-dashboard-card");
  });

  it("renders UnraidServerCard with mock hass data", async () => {
    const card = new UnraidServerCard();
    card.setConfig({ type: "custom:unraid-server-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.getCardSize()).toBe(4);
    expect(card.getGridOptions().columns).toBe(6);
    expect(card.shadowRoot?.innerHTML).toContain("CUBE");
    expect(card.shadowRoot?.innerHTML).toContain("CPU Load");
    expect(card.shadowRoot?.innerHTML).toContain("15%");
    document.body.removeChild(card);
  });

  it("renders UnraidStorageCard and handles disk spin state", async () => {
    const card = new UnraidStorageCard();
    card.setConfig({ type: "custom:unraid-storage-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Storage Array &amp; Disks");
    expect(card.shadowRoot?.innerHTML).toContain("Disk 1");
    expect(card.shadowRoot?.innerHTML).toContain("Active");
    document.body.removeChild(card);
  });

  it("renders UnraidDockerCard and container list", async () => {
    const card = new UnraidDockerCard();
    card.setConfig({ type: "custom:unraid-docker-card", view_mode: "list" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Docker Containers");
    expect(card.shadowRoot?.innerHTML).toContain("plex");
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
});
