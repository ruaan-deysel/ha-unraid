import { html, nothing, type TemplateResult } from "lit";
import {
  UPS_CARD_TAG,
  UPS_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidUpsCardEditor } from "./dashboard-cards-editor";
import {
  mdiFlash,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class UnraidUpsCard extends BaseUnraidCard {
  static override editorTag = UPS_EDITOR_TAG;

  protected override render(): TemplateResult {
    const statusState = this.getEntity("ups_status");
    const batteryState = this.getEntity("ups_battery");
    const loadState = this.getEntity("ups_load");
    const runtimeState = this.getEntity("ups_runtime");
    const powerState = this.getEntity("ups_power");
    const voltageOut = this.getEntity("ups_output_voltage");
    const healthState = this.getEntity("ups_battery_health");

    const hasStatus = Boolean(statusState && statusState.state !== "unavailable" && statusState.state !== "unknown");
    const status = hasStatus && statusState ? statusState.state : (statusState?.state || "Unavailable");
    const isOnline = hasStatus && status.toLowerCase().includes("online");
    const isBattery = hasStatus && (status.toLowerCase().includes("battery") || status.toLowerCase().includes("discharge"));
    const isUnavailable = !hasStatus || status === "Unavailable" || status === "unavailable";

    const hasBattery = Boolean(batteryState && batteryState.state !== "unavailable" && batteryState.state !== "unknown");
    const batteryPct = hasBattery && batteryState ? Math.round(Number(batteryState.state) || 0) : null;

    const hasLoad = Boolean(loadState && loadState.state !== "unavailable" && loadState.state !== "unknown");
    const loadPct = hasLoad && loadState ? Math.round(Number(loadState.state) || 0) : null;

    const hasPower = Boolean(powerState && powerState.state !== "unavailable" && powerState.state !== "unknown");
    const powerW = hasPower && powerState ? `${powerState.state} W` : null;

    const hasRuntime = Boolean(runtimeState && runtimeState.state !== "unavailable" && runtimeState.state !== "unknown");
    const runtimeMin = hasRuntime && runtimeState ? `${runtimeState.state} min` : null;

    const hasVoltage = Boolean(voltageOut && voltageOut.state !== "unavailable" && voltageOut.state !== "unknown");
    const voltageV = hasVoltage && voltageOut ? `${voltageOut.state} V` : null;

    const hasHealth = Boolean(healthState && healthState.state !== "unavailable" && healthState.state !== "unknown");
    const health = hasHealth && healthState ? healthState.state : null;

    const badge = html`
      <span class="badge ${isUnavailable ? "badge-standby" : isOnline ? "badge-online" : isBattery ? "badge-warning" : "badge-error"}">
        ${!isUnavailable ? html`<span class="pulse-dot"></span>` : nothing}
        <span>${isUnavailable ? "Unavailable" : status}</span>
      </span>
    `;

    return html`
      <ha-card>
        ${this.renderHeader(
          this.config.title || "UPS Power & Battery",
          (statusState?.attributes?.model as string) || "Uninterruptible Power Supply",
          mdiFlash,
          badge
        )}

        <!-- Ring Gauges -->
        <div class="rings-grid" style="grid-template-columns: repeat(2, 1fr);">
          <!-- Battery -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${batteryPct ?? 0}; --ring-color: ${batteryPct === null ? "var(--unraid-border)" : batteryPct < 20 ? "var(--unraid-error)" : batteryPct < 50 ? "var(--unraid-warning)" : "var(--unraid-online)"}"
            >
              <span class="ring-content">${batteryPct !== null ? `${batteryPct}%` : "—"}</span>
            </div>
            <span class="ring-label">Battery Level</span>
            <span class="ring-subtext">${runtimeMin ? `${runtimeMin} left` : batteryPct !== null ? "Healthy" : "No Data"}</span>
          </div>

          <!-- Load -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${loadPct ?? 0}; --ring-color: ${loadPct === null ? "var(--unraid-border)" : loadPct > 80 ? "var(--unraid-error)" : loadPct > 50 ? "var(--unraid-warning)" : "var(--unraid-info)"}"
            >
              <span class="ring-content">${loadPct !== null ? `${loadPct}%` : "—"}</span>
            </div>
            <span class="ring-label">UPS Load</span>
            <span class="ring-subtext">${powerW || (loadPct !== null ? `${loadPct}% capacity` : "No Data")}</span>
          </div>
        </div>

        <div class="divider"></div>

        <!-- Power & Electrical Specs -->
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">Runtime Remaining</span>
            <span class="detail-val">${runtimeMin || "—"}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Power Consumption</span>
            <span class="detail-val">${powerW || "—"}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Output Voltage</span>
            <span class="detail-val">${voltageV || "—"}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Battery Health</span>
            <span class="detail-val" style="${health ? "color: var(--unraid-online);" : ""}">${health || "—"}</span>
          </div>
        </div>
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: UPS_CARD_TAG,
  editorTag: UPS_EDITOR_TAG,
  card: UnraidUpsCard,
  editor: UnraidUpsCardEditor,
  name: "Unraid Power & UPS Card",
  description: "Monitor UPS battery level, power draw in Watts, load %, and estimated runtime.",
});
