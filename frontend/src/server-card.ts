import { html, nothing, type TemplateResult } from "lit";
import {
  SERVER_CARD_TAG,
  SERVER_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidServerCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiAlertCircle,
  mdiServer,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class UnraidServerCard extends BaseUnraidCard {
  static override editorTag = SERVER_EDITOR_TAG;

  private formatUptime(secondsOrIso: string | undefined): string {
    if (!secondsOrIso) return "Unknown";
    const date = new Date(secondsOrIso);
    if (!isNaN(date.getTime())) {
      const diffMs = Date.now() - date.getTime();
      const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diffMs / (1000 * 60 * 60)) % 24);
      return days > 0 ? `${days}d ${hours}h` : `${hours}h`;
    }
    const num = Number(secondsOrIso);
    if (!isNaN(num) && num > 0) {
      const days = Math.floor(num / 86400);
      const hours = Math.floor((num % 86400) / 3600);
      return days > 0 ? `${days}d ${hours}h` : `${hours}h`;
    }
    return secondsOrIso;
  }

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName = this.config.title || device?.name_by_user || device?.name || "Unraid Server";

    // Entities
    const cpuState = this.getEntity("cpu_usage");
    const ramState = this.getEntity("ram_usage");
    const arrayUsage = this.getEntity("array_usage");
    const arrayState = this.getEntity("array_state");
    const tempState = this.getEntity("system_temperature") || this.getEntity("temperature_average");
    const powerState = this.getEntity("cpu_power");
    const uptimeState = this.getEntity("uptime");
    const alertsState = this.getEntity("notifications_unread_alert");
    const ipState = this.getEntity("network_interface_ip");

    const cpuPct = Math.round(Number(cpuState?.state) || 0);
    const ramPct = Math.round(Number(ramState?.state) || 0);
    const arrayPct = Math.round(Number(arrayUsage?.state) || 0);

    const isArrayStarted = arrayState?.state?.toLowerCase() === "started" || arrayState?.state === "Normal";
    const alertCount = Number(alertsState?.state) || 0;

    const cpuModel = (cpuState?.attributes?.cpu_model as string) || (device?.model ?? "Multi-Core CPU");
    const ramUsedStr = (ramState?.attributes?.used as string) || "";
    const ramTotalStr = (ramState?.attributes?.total as string) || "";
    const arrayUsedStr = (arrayUsage?.attributes?.capacity_used as string) || "";
    const arrayTotalStr = (arrayUsage?.attributes?.capacity_total as string) || "";

    const badge = html`
      <span class="badge ${isArrayStarted ? "badge-online" : "badge-error"}">
        <span class="pulse-dot"></span>
        <span>Array ${arrayState?.state || (isArrayStarted ? "Started" : "Stopped")}</span>
      </span>
      ${alertCount > 0
        ? html`
            <span class="badge badge-error">
              ${iconTemplate(mdiAlertCircle, 13)}
              <span>${alertCount}</span>
            </span>
          `
        : nothing}
    `;

    return html`
      <ha-card>
        ${this.renderHeader(
          serverName,
          `${device?.model || "Unraid OS"} • Up ${this.formatUptime(uptimeState?.state)}`,
          mdiServer,
          badge
        )}

        <!-- Conic Ring Gauges -->
        <div class="rings-grid">
          <!-- CPU -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${cpuPct}; --ring-color: ${cpuPct > 80 ? "var(--unraid-error)" : cpuPct > 50 ? "var(--unraid-warning)" : "var(--unraid-online)"}"
            >
              <span class="ring-content">${cpuPct}%</span>
            </div>
            <span class="ring-label">CPU Load</span>
            <span class="ring-subtext">
              ${tempState?.state ? `${tempState.state}°C` : ""}${powerState?.state ? ` • ${powerState.state}W` : ""}
            </span>
          </div>

          <!-- RAM -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${ramPct}; --ring-color: ${ramPct > 85 ? "var(--unraid-error)" : "var(--unraid-info)"}"
            >
              <span class="ring-content">${ramPct}%</span>
            </div>
            <span class="ring-label">Memory</span>
            <span class="ring-subtext">${ramUsedStr && ramTotalStr ? `${ramUsedStr} / ${ramTotalStr}` : `${ramPct}% used`}</span>
          </div>

          <!-- Array -->
          <div class="ring-card">
            <div
              class="ring-gauge"
              style="--pct: ${arrayPct}; --ring-color: var(--unraid-accent)"
            >
              <span class="ring-content">${arrayPct}%</span>
            </div>
            <span class="ring-label">Array Storage</span>
            <span class="ring-subtext">${arrayUsedStr && arrayTotalStr ? `${arrayUsedStr} / ${arrayTotalStr}` : `${arrayPct}% used`}</span>
          </div>
        </div>

        ${this.config.show_system_info !== false
          ? html`
              <div class="divider"></div>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">Processor</span>
                  <span class="detail-val" title="${cpuModel}">${cpuModel}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">LAN IP Address</span>
                  <span class="detail-val">${ipState?.state || "Connected"}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">System Health</span>
                  <span class="detail-val" style="color: ${alertCount === 0 ? "var(--unraid-online)" : "var(--unraid-error)"}">
                    ${alertCount === 0 ? "Normal • Healthy" : `${alertCount} Active Alerts`}
                  </span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">OS Version</span>
                  <span class="detail-val">${device?.sw_version || "Unraid OS"}</span>
                </div>
              </div>
            `
          : nothing}
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: SERVER_CARD_TAG,
  editorTag: SERVER_EDITOR_TAG,
  card: UnraidServerCard,
  editor: UnraidServerCardEditor,
  name: "Unraid Server Overview Card",
  description: "Server metrics, CPU/RAM ring gauges, and hardware health.",
});
