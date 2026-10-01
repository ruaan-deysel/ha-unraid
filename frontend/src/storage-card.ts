import { html, nothing, type TemplateResult } from "lit";
import {
  STORAGE_CARD_TAG,
  STORAGE_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidStorageCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiAlertCircle,
  mdiCheckCircle,
  mdiHarddisk,
  mdiPause,
  mdiPlay,
  mdiShieldAlert,
  mdiShieldCheck,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

interface DiskItem {
  id: string;
  name: string;
  isParity: boolean;
  isCache: boolean;
  isBoot: boolean;
  usagePct: number;
  temp: string;
  errors: number;
  isSpinning: boolean;
  spinEntityId?: string;
  freeSpace?: string;
  totalSpace?: string;
}

function matchesDiskEntity(targetEntityId: string, diskKey: string): boolean {
  const escaped = diskKey.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(?:^|[._])${escaped}(?:[._]|$)`).test(targetEntityId);
}

export class UnraidStorageCard extends BaseUnraidCard {
  static override editorTag = STORAGE_EDITOR_TAG;

  private getDisks(): DiskItem[] {
    const usageEntities = this.getEntities("disk_usage");
    const tempEntities = this.getEntities("disk_temperature");
    const errorEntities = this.getEntities("disk_error_count");
    const spinEntities = this.getEntities("disk_spin", "switch");

    const diskMap = new Map<string, DiskItem>();

    for (const u of usageEntities) {
      // Derive a disk key from entity_id, e.g. sensor.tower_disk_1_usage -> disk_1
      const parts = u.entity_id.split(".");
      const namePart = (parts[1] || "").replace(/_disk_usage|_usage$/, "");
      const cleanName = (u.attributes.friendly_name as string) || namePart;
      const isParity = cleanName.toLowerCase().includes("parity");
      const isCache = cleanName.toLowerCase().includes("cache") || cleanName.toLowerCase().includes("pool");
      const isBoot = cleanName.toLowerCase().includes("boot") || cleanName.toLowerCase().includes("flash");

      const diskKey = namePart;
      diskMap.set(diskKey, {
        id: diskKey,
        name: cleanName,
        isParity,
        isCache,
        isBoot,
        usagePct: Math.round(Number(u.state) || 0),
        temp: "*",
        errors: 0,
        isSpinning: false,
        freeSpace: u.attributes.free as string | undefined,
        totalSpace: u.attributes.total as string | undefined,
      });
    }

    // Match temps
    for (const t of tempEntities) {
      for (const [key, disk] of diskMap.entries()) {
        if (matchesDiskEntity(t.entity_id, key)) {
          disk.temp = t.state !== "unavailable" && t.state !== "unknown" ? `${t.state}°C` : "*";
          break;
        }
      }
    }

    // Match errors
    for (const e of errorEntities) {
      for (const [key, disk] of diskMap.entries()) {
        if (matchesDiskEntity(e.entity_id, key)) {
          disk.errors = Number(e.state) || 0;
          break;
        }
      }
    }

    // Match spin switches
    for (const s of spinEntities) {
      for (const [key, disk] of diskMap.entries()) {
        if (matchesDiskEntity(s.entity_id, key)) {
          disk.isSpinning = s.state === "on";
          disk.spinEntityId = s.entity_id;
          break;
        }
      }
    }

    return Array.from(diskMap.values()).sort((a, b) => {
      if (a.isParity !== b.isParity) {
        return a.isParity ? -1 : 1;
      }
      if (a.isCache !== b.isCache) {
        return a.isCache ? 1 : -1;
      }
      return a.name.localeCompare(b.name, undefined, { numeric: true });
    });
  }

  protected override render(): TemplateResult {
    const arrayUsage = this.getEntity("array_usage");
    const parityStatus = this.getEntity("parity_status");
    const parityProgress = this.getEntity("parity_progress");
    const paritySwitch = this.getEntity("parity_check", "switch");
    const lastCheckDate = this.getEntity("last_parity_check_date");
    const lastCheckErrors = this.getEntity("last_parity_check_errors");

    const arrayPct = Math.round(Number(arrayUsage?.state) || 0);
    const usedStr = (arrayUsage?.attributes?.capacity_used as string) || "";
    const totalStr = (arrayUsage?.attributes?.capacity_total as string) || "";
    const freeStr = (arrayUsage?.attributes?.capacity_free as string) || "";

    const isChecking = parityProgress && !isNaN(Number(parityProgress.state)) && Number(parityProgress.state) > 0;
    const progressVal = Math.round(Number(parityProgress?.state) || 0);

    const isParityValid = parityStatus?.state?.toLowerCase() === "on" || parityStatus?.state?.toLowerCase() === "ok" || parityStatus?.state === "Valid";

    const disks = this.getDisks();

    const badge = html`
      <span class="badge ${isParityValid ? "badge-online" : "badge-warning"}">
        ${iconTemplate(isParityValid ? mdiShieldCheck : mdiShieldAlert, 13)}
        <span>${isParityValid ? "Parity Valid" : "Parity Check Needed"}</span>
      </span>
    `;

    return html`
      <ha-card>
        ${this.renderHeader(
          this.config.title || "Storage Array & Disks",
          `${usedStr || `${arrayPct}%`} used of ${totalStr || "Array"}${freeStr ? ` (${freeStr} Free)` : ""}`,
          mdiHarddisk,
          badge
        )}

        <!-- Array Capacity Bar -->
        <div style="display: flex; flex-direction: column; gap: 4px;">
          <div style="display: flex; justify-content: space-between; font-size: 0.76rem; font-weight: 600;">
            <span>Array Capacity</span>
            <span>${arrayPct}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${arrayPct}%;"></div>
          </div>
        </div>

        <!-- Parity Check Status & Action Banner -->
        <div class="list-row" style="background: color-mix(in srgb, var(--unraid-text) 5%, transparent);">
          <div class="row-left">
            <div style="color: ${isParityValid ? "var(--unraid-online)" : "var(--unraid-warning)"}">
              ${iconTemplate(isParityValid ? mdiCheckCircle : mdiAlertCircle, 18)}
            </div>
            <div style="display: flex; flex-direction: column; min-width: 0;">
              <span style="font-weight: 600; font-size: 0.78rem;">
                ${isChecking ? `Parity Check In Progress (${progressVal}%)` : `Parity Status: ${isParityValid ? "Valid" : "Check Needed"}`}
              </span>
              <span style="font-size: 0.7rem; color: var(--unraid-subtext);">
                ${lastCheckDate?.state ? `Last check: ${lastCheckDate.state}` : "Parity healthy"}
                ${lastCheckErrors?.state && lastCheckErrors.state !== "0" ? ` • ${lastCheckErrors.state} errors` : ""}
              </span>
            </div>
          </div>
          <div class="row-right">
            ${paritySwitch
              ? html`
                  <button
                    class="btn ${isChecking ? "btn" : "btn-primary"}"
                    @click=${() => this.toggleEntity(paritySwitch.entity_id)}
                  >
                    ${iconTemplate(isChecking ? mdiPause : mdiPlay, 14)}
                    <span>${isChecking ? "Cancel" : "Check Now"}</span>
                  </button>
                `
              : nothing}
          </div>
        </div>

        <!-- Disk Trays List -->
        <div class="item-list">
          ${disks.length > 0
            ? disks.map((disk) => {
                const tempNum = parseFloat(disk.temp);
                const tempColor = !isNaN(tempNum)
                  ? tempNum > 45
                    ? "var(--unraid-error)"
                    : tempNum > 36
                    ? "var(--unraid-warning)"
                    : "var(--unraid-online)"
                  : "var(--unraid-standby)";

                return html`
                  <div class="list-row">
                    <div class="row-left">
                      <!-- Spin status button -->
                      ${disk.spinEntityId
                        ? html`
                            <button
                              class="badge ${disk.isSpinning ? "badge-online" : "badge-standby"}"
                              style="cursor: pointer; border: none;"
                              title="Click to spin ${disk.isSpinning ? "down" : "up"}"
                              @click=${() => this.toggleEntity(disk.spinEntityId!)}
                            >
                              <span class="status-dot ${disk.isSpinning ? "online" : "offline"}"></span>
                              <span>${disk.isSpinning ? "Active" : "Standby"}</span>
                            </button>
                          `
                        : html`
                            <span class="badge ${disk.isSpinning ? "badge-online" : "badge-standby"}">
                              <span>${disk.isSpinning ? "Active" : "Standby"}</span>
                            </span>
                          `}

                      <span style="font-weight: 600; min-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${disk.name}
                      </span>
                    </div>

                    <div class="row-right">
                      <!-- Temperature Chip -->
                      <span class="badge" style="color: ${tempColor}; background: color-mix(in srgb, ${tempColor} 12%, transparent);">
                        ${disk.temp}
                      </span>

                      <!-- Error Counter -->
                      ${disk.errors > 0
                        ? html`
                            <span class="badge badge-error">
                              ${disk.errors} err
                            </span>
                          `
                        : html`
                            <span class="badge badge-online" style="font-size: 0.68rem;">0 err</span>
                          `}

                      <!-- Utilization -->
                      <div style="display: flex; align-items: center; gap: 6px; width: 85px;">
                        <div class="progress-bar" style="height: 4px;">
                          <div
                            class="progress-fill"
                            style="width: ${disk.usagePct}%; background: ${disk.isCache ? "var(--unraid-info)" : "var(--unraid-accent)"};"
                          ></div>
                        </div>
                        <span style="font-size: 0.7rem; font-family: monospace; color: var(--unraid-subtext);">
                          ${disk.usagePct}%
                        </span>
                      </div>
                    </div>
                  </div>
                `;
              })
            : html`<div style="text-align: center; color: var(--unraid-subtext); font-size: 0.8rem; padding: 12px;">No disk devices found</div>`}
        </div>
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: STORAGE_CARD_TAG,
  editorTag: STORAGE_EDITOR_TAG,
  card: UnraidStorageCard,
  editor: UnraidStorageCardEditor,
  name: "Unraid Storage & Disks Card",
  description: "Array capacity, parity checks, and interactive disk tray with spin state controls.",
});
