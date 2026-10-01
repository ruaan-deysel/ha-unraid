import { html, nothing, type TemplateResult } from "lit";
import {
  DASHBOARD_CARD_TAG,
  DASHBOARD_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidDashboardCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiDocker,
  mdiFlash,
  mdiHarddisk,
  mdiMonitor,
  mdiServer,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

import "./server-card";
import "./storage-card";
import "./docker-card";
import "./ups-card";
import "./vm-card";

type ActiveTab = "overview" | "storage" | "docker" | "ups" | "vms";

export class UnraidDashboardCard extends BaseUnraidCard {
  static override editorTag = DASHBOARD_EDITOR_TAG;

  static override properties = {
    ...BaseUnraidCard.properties,
    _activeTab: { state: true },
  };

  declare _activeTab: ActiveTab;

  constructor() {
    super();
    this._activeTab = "overview";
  }

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName = this.config.title || device?.name_by_user || device?.name || "Unraid Server";

    return html`
      <ha-card style="gap: 12px;">
        <div class="header">
          <div class="header-main">
            <div class="header-icon">${iconTemplate(mdiServer, 22)}</div>
            <div class="header-titles">
              <span class="header-title">${serverName} Dashboard</span>
              <span class="header-subtitle">Unified Unraid Control Center</span>
            </div>
          </div>
        </div>

        <!-- Tab Strip -->
        <div class="tab-strip">
          <button
            class="tab-btn ${this._activeTab === "overview" ? "active" : ""}"
            @click=${() => (this._activeTab = "overview")}
          >
            ${iconTemplate(mdiServer, 14)} Overview
          </button>
          <button
            class="tab-btn ${this._activeTab === "storage" ? "active" : ""}"
            @click=${() => (this._activeTab = "storage")}
          >
            ${iconTemplate(mdiHarddisk, 14)} Storage & Disks
          </button>
          <button
            class="tab-btn ${this._activeTab === "docker" ? "active" : ""}"
            @click=${() => (this._activeTab = "docker")}
          >
            ${iconTemplate(mdiDocker, 14)} Docker
          </button>
          <button
            class="tab-btn ${this._activeTab === "ups" ? "active" : ""}"
            @click=${() => (this._activeTab = "ups")}
          >
            ${iconTemplate(mdiFlash, 14)} UPS Power
          </button>
          <button
            class="tab-btn ${this._activeTab === "vms" ? "active" : ""}"
            @click=${() => (this._activeTab = "vms")}
          >
            ${iconTemplate(mdiMonitor, 14)} VMs
          </button>
        </div>

        <!-- Tab Contents -->
        <div>
          ${this._activeTab === "overview"
            ? html`<unraid-server-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-server-card", embedded: true }}></unraid-server-card>`
            : nothing}
          ${this._activeTab === "storage"
            ? html`<unraid-storage-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-storage-card", embedded: true }}></unraid-storage-card>`
            : nothing}
          ${this._activeTab === "docker"
            ? html`<unraid-docker-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-docker-card", embedded: true }}></unraid-docker-card>`
            : nothing}
          ${this._activeTab === "ups"
            ? html`<unraid-ups-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-ups-card", embedded: true }}></unraid-ups-card>`
            : nothing}
          ${this._activeTab === "vms"
            ? html`<unraid-vm-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-vm-card", embedded: true }}></unraid-vm-card>`
            : nothing}
        </div>
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: DASHBOARD_CARD_TAG,
  editorTag: DASHBOARD_EDITOR_TAG,
  card: UnraidDashboardCard,
  editor: UnraidDashboardCardEditor,
  name: "Unraid Unified Dashboard Card",
  description: "All-in-one Unraid master card with tabbed overview, storage, docker, UPS, and VM monitoring.",
});
