import { html, nothing, type TemplateResult } from "lit";
import {
  SHARES_CARD_TAG,
  SHARES_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidSharesCardEditor } from "./dashboard-cards-editor";
import { fireEvent } from "./ha-types";
import {
  iconTemplate,
  mdiFolder,
  mdiShieldAlert,
  mdiShieldCheck,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export interface ShareItem {
  id: string;
  name: string;
  entityId: string;
  usagePct: number;
  used: string;
  total: string;
  free: string;
  isProtected: boolean;
  color: string;
  allocator?: string;
}

export function formatShareName(rawName: string, id: string): string {
  let name = rawName.trim();
  const match = name.match(/^(?:.*?\s+)?Share\s+(.+?)(?:\s+usage)?$/i);
  if (match && match[1]) {
    return match[1].trim();
  }
  name = name
    .replace(/\s+usage$/i, "")
    .replace(/_usage$/i, "")
    .replace(/\s+share$/i, "")
    .replace(/_share$/i, "")
    .trim();
  return name || id;
}

export class UnraidSharesCard extends BaseUnraidCard {
  static override editorTag = SHARES_EDITOR_TAG;

  static override properties = {
    ...BaseUnraidCard.properties,
    _searchQuery: { state: true },
  };

  declare _searchQuery: string;

  constructor() {
    super();
    this._searchQuery = "";
  }

  private getShares(): ShareItem[] {
    const shareEntities = this.getEntities("share_usage");
    const shares: ShareItem[] = [];

    for (const u of shareEntities) {
      const parts = u.entity_id.split(".");
      const namePart = (parts[1] || "").replace(/^.*?_share_/, "").replace(/_usage$/, "");
      const cleanName = formatShareName(
        (u.attributes.friendly_name as string) || namePart,
        namePart
      );

      const color = (u.attributes.color as string) || "green-on";
      // In Unraid, "green-on" means protected on parity-backed array, "yellow-on" means pool/unprotected
      const isProtected = color === "green-on";

      shares.push({
        id: namePart,
        name: cleanName,
        entityId: u.entity_id,
        usagePct: Math.round(Number(u.state) || 0),
        used: (u.attributes.used as string) || "",
        total: (u.attributes.total as string) || "",
        free: (u.attributes.free as string) || "",
        isProtected,
        color,
        allocator: u.attributes.allocator as string | undefined,
      });
    }

    return shares.sort((a, b) =>
      a.name.localeCompare(b.name, undefined, { numeric: true })
    );
  }

  private _openMoreInfo(entityId: string): void {
    fireEvent(this, "hass-more-info", { entityId });
  }

  protected override render(): TemplateResult {
    const allShares = this.getShares();
    const filteredShares = this._searchQuery
      ? allShares.filter((s) =>
          s.name.toLowerCase().includes(this._searchQuery.toLowerCase())
        )
      : allShares;

    const protectedCount = allShares.filter((s) => s.isProtected).length;
    const unprotectedCount = allShares.length - protectedCount;

    const badge = html`
      <span class="badge ${unprotectedCount === 0 ? "badge-online" : "badge-warning"}">
        ${iconTemplate(unprotectedCount === 0 ? mdiShieldCheck : mdiShieldAlert, 13)}
        <span>${protectedCount} Protected${unprotectedCount > 0 ? ` • ${unprotectedCount} Unprotected` : ""}</span>
      </span>
    `;

    return html`
      <ha-card>
        ${this.renderHeader(
          this.config.title || "User Shares",
          `${allShares.length} configured shares`,
          mdiFolder,
          badge
        )}

        <!-- Search Bar if more than 4 shares -->
        ${allShares.length > 4
          ? html`
              <div style="margin-bottom: 4px;">
                <input
                  type="text"
                  placeholder="Filter shares..."
                  style="
                    width: 100%;
                    padding: 6px 10px;
                    border-radius: 6px;
                    border: 1px solid var(--unraid-border);
                    background: color-mix(in srgb, var(--unraid-text) 4%, transparent);
                    color: var(--unraid-text);
                    font-size: 0.8rem;
                    box-sizing: border-box;
                  "
                  .value=${this._searchQuery}
                  @input=${(e: Event) =>
                    (this._searchQuery = (e.target as HTMLInputElement).value)}
                />
              </div>
            `
          : nothing}

        <!-- Shares List -->
        <div class="item-list">
          ${filteredShares.length > 0
            ? filteredShares.map((share) => {
                const barColor =
                  share.usagePct > 90
                    ? "var(--unraid-error)"
                    : share.usagePct > 75
                    ? "var(--unraid-warning)"
                    : "var(--unraid-online)";

                return html`
                  <div
                    class="list-row"
                    style="cursor: pointer;"
                    title="Click for details on ${share.name}"
                    @click=${() => this._openMoreInfo(share.entityId)}
                  >
                    <div class="row-left">
                      <!-- Folder Icon -->
                      <div
                        style="color: ${share.isProtected ? "var(--unraid-accent)" : "var(--unraid-warning)"}; display: flex; align-items: center;"
                      >
                        ${iconTemplate(mdiFolder, 18)}
                      </div>

                      <div style="display: flex; flex-direction: column; min-width: 0;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                          <span
                            style="font-weight: 600; font-size: 0.82rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
                          >
                            ${share.name}
                          </span>

                          <!-- Protection Tag -->
                          <span
                            class="badge ${share.isProtected ? "badge-online" : "badge-warning"}"
                            style="font-size: 0.62rem; padding: 1px 6px;"
                            title="${share.isProtected ? "Data protected on parity array" : "Data on pool / unprotected storage"}"
                          >
                            ${share.isProtected ? "Protected" : "Unprotected"}
                          </span>
                        </div>

                        ${share.used && share.total
                          ? html`<span style="font-size: 0.7rem; color: var(--unraid-subtext);">${share.used} / ${share.total}${share.free ? ` • ${share.free} free` : ""}</span>`
                          : nothing}
                      </div>
                    </div>

                    <div class="row-right">
                      <!-- Utilization bar and percentage -->
                      <div style="display: flex; align-items: center; gap: 6px; width: 110px;">
                        <div class="progress-bar" style="height: 6px; flex: 1;">
                          <div
                            class="progress-fill"
                            style="width: ${share.usagePct}%; background: ${barColor};"
                          ></div>
                        </div>
                        <span
                          style="font-size: 0.72rem; font-family: monospace; font-weight: 600; color: var(--unraid-text); min-width: 32px; text-align: right;"
                        >
                          ${share.usagePct}%
                        </span>
                      </div>
                    </div>
                  </div>
                `;
              })
            : html`
                <div style="text-align: center; color: var(--unraid-subtext); font-size: 0.8rem; padding: 16px;">
                  ${allShares.length === 0 ? "No user shares found" : "No shares matching filter"}
                </div>
              `}
        </div>
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: SHARES_CARD_TAG,
  editorTag: SHARES_EDITOR_TAG,
  card: UnraidSharesCard,
  editor: UnraidSharesCardEditor,
  name: "Unraid User Shares Card",
  description: "User share storage utilization, capacity allocation, and parity protection status.",
});
