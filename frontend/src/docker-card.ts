import { html, nothing, type PropertyValues, type TemplateResult } from "lit";
import {
  DOCKER_CARD_TAG,
  DOCKER_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidDockerCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiAlertCircle,
  mdiDocker,
  mdiPower,
  mdiRestart,
  mdiViewGrid,
  mdiViewList,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

interface ContainerItem {
  id: string;
  name: string;
  isRunning: boolean;
  switchEntityId: string;
  restartEntityId?: string;
  autostartEntityId?: string;
  cpuPct?: number;
  memoryUsage?: string;
  hasUpdate?: boolean;
  updateEntityId?: string;
}

function extractEntityContainerSlug(entityId: string): string {
  const objectId = entityId.split(".")[1] || "";
  return (
    objectId
      .replace(/^.*?_container_restart_/, "")
      .replace(/^.*?_docker_container_restart_/, "")
      .replace(/^.*?_container_autostart_/, "")
      .replace(/^.*?_docker_container_autostart_/, "")
      .replace(/^.*?_container_update_/, "")
      .replace(/^.*?_docker_container_update_/, "")
      .replace(/^.*?_docker_container_/, "")
      .replace(/^.*?_container_switch_/, "")
      .replace(/^docker_container_/, "")
      .replace(/^container_switch_/, "")
      .replace(/_cpu$/, "")
      .replace(/_memory_usage$/, "")
      .replace(/_memory$/, "")
      .replace(/_docker_container$/, "")
      .replace(/_container_switch$/, "")
      .replace(/^.*?_container_/, "") || objectId
  );
}

export class UnraidDockerCard extends BaseUnraidCard {
  static override editorTag = DOCKER_EDITOR_TAG;

  static override properties = {
    ...BaseUnraidCard.properties,
    _filter: { state: true },
    _viewMode: { state: true },
  };

  declare _filter: "all" | "running" | "stopped" | "updates";
  declare _viewMode: "grid" | "list";

  constructor() {
    super();
    this._filter = "all";
    this._viewMode = "grid";
  }

  override willUpdate(changedProperties: PropertyValues<this>): void {
    super.willUpdate(changedProperties);
    if (changedProperties.has("config") && this.config.view_mode) {
      this._viewMode = this.config.view_mode;
    }
  }

  private handleToggle(entityId: string, isRunning: boolean, name: string): void {
    if (isRunning) {
      if (!confirm(`Are you sure you want to stop container "${name}"?`)) {
        return;
      }
    }
    this.toggleEntity(entityId);
  }

  private getContainers(): ContainerItem[] {
    const switches = this.getEntities("docker_container", "switch");
    const restarts = this.getEntities("docker_container_restart", "button");
    const autostarts = this.getEntities("docker_container_autostart", "switch");
    const cpus = this.getEntities("container_cpu");
    const mems = this.getEntities("container_memory_usage");
    const updates = this.getEntities("docker_container_update", "update");

    const list: ContainerItem[] = [];

    for (const sw of switches) {
      const slug = extractEntityContainerSlug(sw.entity_id);
      const cleanName = (sw.attributes.friendly_name as string) || slug;
      const isRunning = sw.state === "on";

      const restart = restarts.find(
        (r) => extractEntityContainerSlug(r.entity_id) === slug
      );
      const autostart = autostarts.find(
        (a) => extractEntityContainerSlug(a.entity_id) === slug
      );
      const cpu = cpus.find(
        (c) => extractEntityContainerSlug(c.entity_id) === slug
      );
      const mem = mems.find(
        (m) => extractEntityContainerSlug(m.entity_id) === slug
      );
      const update = updates.find(
        (u) => extractEntityContainerSlug(u.entity_id) === slug
      );

      list.push({
        id: slug,
        name: cleanName,
        isRunning,
        switchEntityId: sw.entity_id,
        restartEntityId: restart?.entity_id,
        autostartEntityId: autostart?.entity_id,
        cpuPct: cpu?.state ? parseFloat(cpu.state) : undefined,
        memoryUsage:
          mem?.state && mem.state !== "unavailable"
            ? `${mem.state} ${mem.attributes.unit_of_measurement || "B"}`
            : undefined,
        hasUpdate: update?.state === "on",
        updateEntityId: update?.entity_id,
      });
    }

    return list.sort((a, b) => {
      if (a.isRunning && !b.isRunning) return -1;
      if (!a.isRunning && b.isRunning) return 1;
      return a.name.localeCompare(b.name);
    });
  }

  protected override render(): TemplateResult {
    const containers = this.getContainers();
    const runningCount = containers.filter((c) => c.isRunning).length;
    const stoppedCount = containers.length - runningCount;
    const updateCount = containers.filter((c) => c.hasUpdate).length;

    const checkUpdatesBtn = this.getEntity("check_container_updates", "button");

    const filtered = containers.filter((c) => {
      if (this._filter === "running") return c.isRunning;
      if (this._filter === "stopped") return !c.isRunning;
      if (this._filter === "updates") return c.hasUpdate;
      return true;
    });

    const badge = html`
      <span class="badge ${runningCount > 0 ? "badge-online" : "badge-standby"}">
        ${runningCount} Running
      </span>
      ${updateCount > 0
        ? html`
            <span class="badge badge-warning">
              ${iconTemplate(mdiAlertCircle, 12)}
              <span>${updateCount} Updates</span>
            </span>
          `
        : nothing}
    `;

    return html`
      <ha-card>
        ${this.renderHeader(
          this.config.title || "Docker Containers",
          `${runningCount} running • ${stoppedCount} stopped`,
          mdiDocker,
          badge
        )}

        <!-- Top Controls & Filter Bar -->
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
          <div style="display: flex; gap: 4px; overflow-x: auto;">
            <button
              class="tab-btn ${this._filter === "all" ? "active" : ""}"
              @click=${() => (this._filter = "all")}
            >
              All (${containers.length})
            </button>
            <button
              class="tab-btn ${this._filter === "running" ? "active" : ""}"
              @click=${() => (this._filter = "running")}
            >
              Running (${runningCount})
            </button>
            <button
              class="tab-btn ${this._filter === "stopped" ? "active" : ""}"
              @click=${() => (this._filter = "stopped")}
            >
              Stopped (${stoppedCount})
            </button>
            ${updateCount > 0
              ? html`
                  <button
                    class="tab-btn ${this._filter === "updates" ? "active" : ""}"
                    style="color: var(--unraid-warning);"
                    @click=${() => (this._filter = "updates")}
                  >
                    Updates (${updateCount})
                  </button>
                `
              : nothing}
          </div>

          <div style="display: flex; align-items: center; gap: 6px;">
            ${checkUpdatesBtn
              ? html`
                  <button
                    class="btn"
                    title="Check for updates"
                    @click=${() => this.pressButton(checkUpdatesBtn.entity_id)}
                  >
                    Check Updates
                  </button>
                `
              : nothing}
            <button
              class="btn-icon"
              title="Toggle View Mode"
              @click=${() =>
                (this._viewMode = this._viewMode === "grid" ? "list" : "grid")}
            >
              ${iconTemplate(this._viewMode === "grid" ? mdiViewList : mdiViewGrid, 18)}
            </button>
          </div>
        </div>

        <!-- Containers Display (Grid or List View) -->
        ${this._viewMode === "grid"
          ? html`
              <div class="container-grid">
                ${filtered.map(
                  (c) => html`
                    <div
                      class="container-tile"
                      @click=${() => this.openMoreInfo(c.switchEntityId)}
                    >
                      <div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
                        <span class="status-dot ${c.isRunning ? "online" : "offline"}"></span>
                        <span class="tile-name" title="${c.name}">${c.name}</span>
                      </div>
                      <div style="display: flex; align-items: center; gap: 4px;">
                        ${c.hasUpdate
                          ? html`<span style="color: var(--unraid-warning);">${iconTemplate(mdiAlertCircle, 14)}</span>`
                          : nothing}
                        ${c.restartEntityId
                          ? html`
                              <button
                                class="btn-icon"
                                style="padding: 2px;"
                                title="Restart ${c.name}"
                                @click=${(e: Event) => {
                                  e.stopPropagation();
                                  this.pressButton(c.restartEntityId!);
                                }}
                              >
                                ${iconTemplate(mdiRestart, 14)}
                              </button>
                            `
                          : nothing}
                        <button
                          class="btn-icon"
                          style="padding: 2px; color: ${c.isRunning ? "var(--unraid-online)" : "var(--unraid-subtext)"};"
                          title="${c.isRunning ? "Stop" : "Start"} ${c.name}"
                          @click=${(e: Event) => {
                            e.stopPropagation();
                            this.handleToggle(c.switchEntityId, c.isRunning, c.name);
                          }}
                        >
                          ${iconTemplate(mdiPower, 14)}
                        </button>
                      </div>
                    </div>
                  `
                )}
              </div>
            `
          : html`
              <div class="item-list">
                ${filtered.map(
                  (c) => html`
                    <div class="list-row">
                      <div class="row-left">
                        <span class="status-dot ${c.isRunning ? "online" : "offline"}"></span>
                        <span style="font-weight: 600; min-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                          ${c.name}
                        </span>
                        ${c.cpuPct !== undefined
                          ? html`<span style="font-size: 0.72rem; color: var(--unraid-subtext);">${c.cpuPct}% CPU</span>`
                          : nothing}
                        ${c.memoryUsage
                          ? html`<span style="font-size: 0.72rem; color: var(--unraid-subtext);">${c.memoryUsage}</span>`
                          : nothing}
                      </div>
                      <div class="row-right">
                        ${c.hasUpdate
                          ? html`
                              <span class="badge badge-warning">Update Available</span>
                            `
                          : nothing}
                        ${c.restartEntityId
                          ? html`
                              <button
                                class="btn"
                                style="padding: 3px 8px;"
                                @click=${() => this.pressButton(c.restartEntityId!)}
                              >
                                ${iconTemplate(mdiRestart, 13)}
                                <span>Restart</span>
                              </button>
                            `
                          : nothing}
                        <button
                          class="btn ${c.isRunning ? "btn" : "btn-primary"}"
                          style="padding: 3px 8px;"
                          @click=${() => this.handleToggle(c.switchEntityId, c.isRunning, c.name)}
                        >
                          ${iconTemplate(mdiPower, 13)}
                          <span>${c.isRunning ? "Stop" : "Start"}</span>
                        </button>
                      </div>
                    </div>
                  `
                )}
              </div>
            `}
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: DOCKER_CARD_TAG,
  editorTag: DOCKER_EDITOR_TAG,
  card: UnraidDockerCard,
  editor: UnraidDockerCardEditor,
  name: "Unraid Docker Containers Card",
  description: "Monitor, start, stop, restart, and update Docker containers in grid or list view.",
});
