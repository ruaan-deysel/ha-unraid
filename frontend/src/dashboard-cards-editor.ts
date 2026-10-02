import { LitElement, css, html, type TemplateResult } from "lit";
import { type CardConfig } from "./config";
import { fireEvent, type HomeAssistant } from "./ha-types";

export class UnraidCardEditor extends LitElement {
  static override properties = {
    hass: { attribute: false },
    _config: { state: true },
  };

  declare hass?: HomeAssistant;
  declare _config?: CardConfig;

  static override styles = css`
    .card-config {
      display: flex;
      flex-direction: column;
      gap: 14px;
      padding: 8px 0;
      color: var(--primary-text-color, #fff);
      font-size: 0.9rem;
    }
    .form-row {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    label {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--secondary-text-color, #aaa);
    }
    input[type="text"],
    select {
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid var(--divider-color, rgba(255, 255, 255, 0.15));
      background: var(--card-background-color, #1e1e24);
      color: var(--primary-text-color, #fff);
      font-size: 0.85rem;
    }
    .checkbox-row {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
    }
    .checkbox-row input {
      width: 16px;
      height: 16px;
      accent-color: var(--primary-color, #f25f22);
    }
  `;

  setConfig(config: CardConfig): void {
    this._config = { ...config };
  }

  private _valueChanged(key: string, value: unknown): void {
    if (!this._config) return;
    this._config = { ...this._config, [key]: value };
    fireEvent(this, "config-changed", { config: this._config });
  }

  protected override render(): TemplateResult {
    if (!this._config) return html``;

    const devices = this.hass?.devices
      ? Object.values(this.hass.devices).filter((d) =>
          d.identifiers?.some(([domain]) => domain === "unraid")
        )
      : [];

    return html`
      <div class="card-config">
        <div class="form-row">
          <label for="server">Unraid Server</label>
          ${devices.length > 0
            ? html`
                <select
                  id="server"
                  @change=${(e: Event) =>
                    this._valueChanged(
                      "server",
                      (e.target as HTMLSelectElement).value
                    )}
                >
                  ${(() => {
                    const currentServer =
                      this._config.server || devices[0]?.id || "";
                    return devices.map(
                      (d) => html`
                        <option
                          value=${d.id}
                          ?selected=${d.id === currentServer}
                        >
                          ${d.name_by_user || d.name || d.id}
                        </option>
                      `
                    );
                  })()}
                </select>
              `
            : html`
                <input
                  type="text"
                  id="server"
                  placeholder="Auto-detecting server..."
                  .value=${this._config.server || ""}
                  @input=${(e: Event) =>
                    this._valueChanged(
                      "server",
                      (e.target as HTMLInputElement).value
                    )}
                />
              `}
        </div>
        <div class="form-row">
          <label for="title">Custom Title (optional)</label>
          <input
            type="text"
            id="title"
            placeholder="Leave empty for default"
            .value=${this._config.title || ""}
            @input=${(e: Event) =>
              this._valueChanged(
                "title",
                (e.target as HTMLInputElement).value
              )}
          />
        </div>
        ${this._config.type?.includes("docker")
          ? html`
              <div class="form-row">
                <label for="view_mode">Default View Mode</label>
                <select
                  id="view_mode"
                  .value=${this._config.view_mode || "grid"}
                  @change=${(e: Event) =>
                    this._valueChanged(
                      "view_mode",
                      (e.target as HTMLSelectElement).value
                    )}
                >
                  <option value="grid">Grid View (Icons & Status)</option>
                  <option value="list">List View (Detailed Table)</option>
                </select>
              </div>
            `
          : ""}
        <label class="checkbox-row">
          <input
            type="checkbox"
            .checked=${this._config.show_system_info !== false}
            @change=${(e: Event) =>
              this._valueChanged(
                "show_system_info",
                (e.target as HTMLInputElement).checked
              )}
          />
          <span>Show System Details</span>
        </label>
      </div>
    `;
  }
}

export class UnraidServerCardEditor extends UnraidCardEditor {}
export class UnraidStorageCardEditor extends UnraidCardEditor {}
export class UnraidSharesCardEditor extends UnraidCardEditor {}
export class UnraidNetworkCardEditor extends UnraidCardEditor {}
export class UnraidDockerCardEditor extends UnraidCardEditor {}
export class UnraidUpsCardEditor extends UnraidCardEditor {}
export class UnraidVmCardEditor extends UnraidCardEditor {}
export class UnraidDashboardCardEditor extends UnraidCardEditor {}
