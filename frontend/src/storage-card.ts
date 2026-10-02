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
  mdiUsbFlashDrive,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export type DiskHealthLevel = "healthy" | "warning" | "error";

export interface DiskItem {
  id: string;
  name: string;
  isParity: boolean;
  isCache: boolean;
  isBoot: boolean;
  usagePct: number;
  temp: string;
  tempNum?: number;
  errors: number;
  health: DiskHealthLevel;
  statusText?: string;
  isSpinning: boolean;
  spinEntityId?: string;
  freeSpace?: string;
  totalSpace?: string;
}

export function formatDiskName(rawName: string, id: string): string {
  const name = rawName.trim();
  const match = name.match(/^(?:.*?\s+)?(?:Disk\s+)?([a-zA-Z0-9_-]+)(?:\s+(?:usage|health|temperature|temp|spin|errors))?$/i);
  if (match && match[1]) {
    const token = match[1];
    const diskNum = token.match(/^disk[_\s]?(\d+)$/i);
    if (diskNum) return `Disk ${diskNum[1]}`;
    if (/^\d+$/.test(token)) return `Disk ${token}`;
    if (token.toLowerCase() === "parity") return "Parity";
    const parityNum = token.match(/^parity[_\s]?(\d+)$/i);
    if (parityNum) return `Parity ${parityNum[1]}`;
    if (token.toLowerCase() === "cache") return "Cache";
    if (token.toLowerCase().startsWith("cache_")) return `Cache (${token.slice(6).toUpperCase()})`;
    if (token.toLowerCase() === "boot" || token.toLowerCase() === "flash") return "Flash (Boot)";
    return token.replace(/\b\w/g, (c) => c.toUpperCase());
  }
  return name || id;
}

function extractDiskToken(entityId: string): string {
  const objectId = entityId.split(".")[1] || "";
  const token = objectId
    .replace(/^.*?_disk_/, "")
    .replace(/_usage$|_temperature$|_temp$|_errors$|_health$|_spin$/, "")
    .toLowerCase()
    .replace(/_/g, "");
  const numMatch = token.match(/^(?:disk)?(\d+)$/);
  if (numMatch) return `disk${numMatch[1]}`;
  return token;
}

export class UnraidStorageCard extends BaseUnraidCard {
  static override editorTag = STORAGE_EDITOR_TAG;

  private getDisks(): DiskItem[] {
    const usageEntities = this.getEntities("disk_usage");
    const healthEntities = this.getEntities("disk_health", "binary_sensor");
    const tempEntities = this.getEntities("disk_temperature");
    const errorEntities = this.getEntities("disk_error_count");
    const spinEntities = this.getEntities("disk_spin", "switch");

    const diskMap = new Map<string, DiskItem>();

    // 1. Process usage entities (Data and Cache disks)
    for (const u of usageEntities) {
      const diskKey = extractDiskToken(u.entity_id);
      const cleanName = formatDiskName((u.attributes.friendly_name as string) || diskKey, diskKey);
      const isParity = cleanName.toLowerCase().includes("parity");
      const isCache = cleanName.toLowerCase().includes("cache") || cleanName.toLowerCase().includes("pool");
      const isBoot = cleanName.toLowerCase().includes("boot") || cleanName.toLowerCase().includes("flash");

      const attrSpin = u.attributes.spin_state === "active" || u.attributes.spinning === true;
      const attrTemp = u.attributes.temperature_celsius ?? u.attributes.temperature;
      const attrErrors = Number(u.attributes.num_errors ?? 0);
      const attrStatus = (u.attributes.status as string) || "DISK_OK";

      diskMap.set(diskKey, {
        id: diskKey,
        name: cleanName,
        isParity,
        isCache,
        isBoot,
        usagePct: Math.round(Number(u.state) || 0),
        temp: attrTemp !== undefined && attrTemp !== null ? `${attrTemp}°C` : "*",
        tempNum: typeof attrTemp === "number" ? attrTemp : undefined,
        errors: attrErrors,
        health: "healthy",
        statusText: attrStatus,
        isSpinning: attrSpin,
        freeSpace: u.attributes.free as string | undefined,
        totalSpace: u.attributes.total as string | undefined,
      });
    }

    // 2. Add any disks from healthEntities not yet in diskMap (e.g. Parity disk)
    for (const h of healthEntities) {
      const diskKey = extractDiskToken(h.entity_id);
      if (diskMap.has(diskKey)) continue;
      if (diskKey.includes("disabled") || diskKey.includes("missing") || diskKey.includes("invalid")) continue;

      const cleanName = formatDiskName((h.attributes.friendly_name as string) || diskKey, diskKey);
      const isParity = cleanName.toLowerCase().includes("parity");
      const isCache = cleanName.toLowerCase().includes("cache");
      const isBoot = cleanName.toLowerCase().includes("boot");
      const attrSpin = h.attributes.spinning === true || (h.attributes.standby !== undefined ? !h.attributes.standby : false);
      const attrTemp = h.attributes.temperature;
      const attrStatus = (h.attributes.status as string) || "DISK_OK";

      diskMap.set(diskKey, {
        id: diskKey,
        name: cleanName,
        isParity,
        isCache,
        isBoot,
        usagePct: 0,
        temp: attrTemp !== undefined && attrTemp !== null ? `${attrTemp}°C` : "*",
        tempNum: typeof attrTemp === "number" ? attrTemp : undefined,
        errors: 0,
        health: h.state === "on" ? "error" : "healthy",
        statusText: attrStatus,
        isSpinning: attrSpin,
      });
    }

    // 3. Match dedicated temperature entities
    for (const t of tempEntities) {
      const key = extractDiskToken(t.entity_id);
      const disk = diskMap.get(key);
      if (disk && t.state !== "unavailable" && t.state !== "unknown") {
        disk.temp = `${t.state}°C`;
        disk.tempNum = parseFloat(t.state);
      }
    }

    // 4. Match error sensors
    for (const e of errorEntities) {
      const key = extractDiskToken(e.entity_id);
      const disk = diskMap.get(key);
      if (disk) {
        const val = Number(e.state);
        if (!isNaN(val)) disk.errors = val;
      }
    }

    // 5. Match spin switches
    for (const s of spinEntities) {
      const key = extractDiskToken(s.entity_id);
      const disk = diskMap.get(key);
      if (disk) {
        disk.isSpinning = s.state === "on";
        disk.spinEntityId = s.entity_id;
      }
    }

    // 6. Match health binary sensors & resolve health level
    for (const h of healthEntities) {
      const key = extractDiskToken(h.entity_id);
      const disk = diskMap.get(key);
      if (disk) {
        if (h.attributes.status) {
          disk.statusText = h.attributes.status as string;
        }
        if (h.attributes.spinning !== undefined) {
          disk.isSpinning = Boolean(h.attributes.spinning);
        } else if (h.attributes.standby !== undefined) {
          disk.isSpinning = !h.attributes.standby;
        }
        if (h.attributes.temperature !== undefined && disk.temp === "*") {
          disk.temp = `${h.attributes.temperature}°C`;
          disk.tempNum = Number(h.attributes.temperature);
        }
        if (h.state === "on") {
          disk.health = "error";
        }
      }
    }

    // 7. Calculate overall health level
    for (const disk of diskMap.values()) {
      const status = (disk.statusText || "").toUpperCase();
      const hasStatusError = status.includes("ERR") || status.includes("WRONG") || status.includes("INVALID") || status.includes("DSBL") || status.includes("FAIL");

      if (disk.health === "error" || hasStatusError || disk.errors >= 10) {
        disk.health = "error";
      } else if (disk.errors > 0 || (disk.tempNum !== undefined && disk.tempNum > 45)) {
        disk.health = "warning";
      } else {
        disk.health = "healthy";
      }
    }

    return Array.from(diskMap.values()).sort((a, b) => {
      if (a.isParity !== b.isParity) {
        return a.isParity ? -1 : 1;
      }
      if (a.isBoot !== b.isBoot) {
        return a.isBoot ? 1 : -1;
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
        <div style="display: flex; flex-direction: column; gap: 4px;">
          <div style="display: flex; justify-content: space-between; font-size: 0.76rem; font-weight: 600;">
            <span>Array Capacity</span>
            <span>${arrayPct}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${arrayPct}%;"></div>
          </div>
        </div>
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
        <div class="item-list">
          ${disks.length > 0
            ? disks.map((disk) => {
                const tempNum = disk.tempNum ?? parseFloat(disk.temp);
                const hasValidTemp = disk.isSpinning && !isNaN(tempNum) && disk.temp !== "*" && disk.temp !== "unavailable";
                const tempColor = hasValidTemp
                  ? tempNum > 45
                    ? "var(--unraid-error)"
                    : tempNum > 36
                    ? "var(--unraid-warning)"
                    : "var(--unraid-online)"
                  : "var(--unraid-standby)";

                const tempDisplay = hasValidTemp ? `${Math.round(tempNum)}°C` : "--";

                const healthBadge = disk.health === "healthy"
                  ? html`
                      <span class="badge badge-online" style="font-size: 0.68rem; gap: 4px;">
                        ${iconTemplate(mdiCheckCircle, 11)}
                        <span>Healthy</span>
                      </span>
                    `
                  : disk.health === "warning"
                  ? html`
                      <span class="badge badge-warning" style="font-size: 0.68rem; gap: 4px;">
                        ${iconTemplate(mdiAlertCircle, 11)}
                        <span>Warning${disk.errors > 0 ? ` (${disk.errors})` : ""}</span>
                      </span>
                    `
                  : html`
                      <span class="badge badge-error" style="font-size: 0.68rem; gap: 4px;">
                        ${iconTemplate(mdiAlertCircle, 11)}
                        <span>Error${disk.errors > 0 ? ` (${disk.errors})` : ""}</span>
                      </span>
                    `;

                return html`
                  <div class="list-row">
                    <div class="row-left">
                      ${disk.isBoot
                        ? html`
                            <span
                              class="badge badge-online"
                              style="font-size: 0.68rem; gap: 4px; min-width: 60px; justify-content: center;"
                              title="USB Flash Boot Drive"
                            >
                              ${iconTemplate(mdiUsbFlashDrive, 11)}
                              <span>Flash</span>
                            </span>
                          `
                        : disk.spinEntityId
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

                      <span style="font-weight: 600; min-width: 75px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${disk.name}
                      </span>
                    </div>

                    <div class="row-right">
                      <span
                        class="badge"
                        style="color: ${disk.isBoot ? "var(--unraid-text-dim)" : tempColor}; background: color-mix(in srgb, ${disk.isBoot ? "var(--unraid-text-dim)" : tempColor} 12%, transparent); min-width: 44px; justify-content: center;"
                        title="${disk.isBoot ? "USB Flash Drive" : disk.isSpinning ? `Temperature: ${tempDisplay}` : "Disk is in standby"}"
                      >
                        ${disk.isBoot ? "--" : tempDisplay}
                      </span>
                      ${healthBadge}
                      <div style="display: flex; align-items: center; gap: 6px; width: 85px;">
                        ${disk.isParity
                          ? html`
                              <span style="font-size: 0.72rem; color: var(--unraid-online); font-weight: 500; font-family: monospace;">
                                Parity
                              </span>
                            `
                          : html`
                              <div class="progress-bar" style="height: 4px; flex: 1;">
                                <div
                                  class="progress-fill"
                                  style="width: ${disk.usagePct}%; background: ${disk.isBoot ? "var(--unraid-warning)" : disk.isCache ? "var(--unraid-info)" : "var(--unraid-accent)"};"
                                ></div>
                              </div>
                              <span style="font-size: 0.7rem; font-family: monospace; color: var(--unraid-subtext);">
                                ${disk.usagePct}%
                              </span>
                            `}
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
