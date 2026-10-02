import { LitElement, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import { type CardConfig } from "./config";
import { dashboardCardStyles } from "./dashboard-cards-styles";
import {
  fireEvent,
  type DeviceRegistryEntry,
  type HassEntity,
  type HomeAssistant,
} from "./ha-types";
import { iconTemplate } from "./icons";

export abstract class BaseUnraidCard extends LitElement {
  static override styles = dashboardCardStyles;
  static editorTag = "";

  static async getConfigElement(this: {
    editorTag: string;
  }): Promise<HTMLElement> {
    return document.createElement(this.editorTag);
  }

  static override properties = {
    hass: { attribute: false },
    config: { attribute: false },
  };

  declare hass?: HomeAssistant;
  declare config: CardConfig;

  constructor() {
    super();
    this.config = { type: "" };
  }

  override willUpdate(changedProperties: PropertyValues<this>): void {
    super.willUpdate(changedProperties);
    if (changedProperties.has("config")) {
      if (this.config.embedded) {
        this.setAttribute("embedded", "");
      } else {
        this.removeAttribute("embedded");
      }
    }
  }

  setConfig(config: CardConfig): void {
    if (!config || typeof config.type !== "string") {
      throw new Error("Invalid card configuration");
    }
    this.config = { ...config };
    if (this.config.embedded) {
      this.setAttribute("embedded", "");
    } else {
      this.removeAttribute("embedded");
    }
  }

  getCardSize(): number {
    return 4;
  }

  getGridOptions() {
    return { columns: 6, rows: 4, min_columns: 3, min_rows: 3 };
  }

  /** Get all Unraid server devices registered in Home Assistant */
  protected getUnraidDevices(): DeviceRegistryEntry[] {
    if (!this.hass?.devices) return [];
    return Object.values(this.hass.devices).filter((device) =>
      device.identifiers?.some(([domain]) => domain === "unraid")
    );
  }

  /** Resolve the active Unraid device based on config or default */
  protected getActiveDevice(): DeviceRegistryEntry | undefined {
    const devices = this.getUnraidDevices();
    if (devices.length === 0) return undefined;

    if (this.config.server) {
      const match = devices.find(
        (d) =>
          d.id === this.config.server ||
          d.name?.toLowerCase() === this.config.server?.toLowerCase() ||
          d.name_by_user?.toLowerCase() === this.config.server?.toLowerCase()
      );
      if (match) return match;
    }
    return devices[0];
  }

  /**
   * Find an entity by translation key or entity_id suffix.
   */
  protected getEntity(
    translationKey: string,
    domain?: string
  ): HassEntity | undefined {
    if (!this.hass?.states) return undefined;
    const device = this.getActiveDevice();
    const deviceId = device?.id;

    // Check entity registry if available
    if (this.hass.entities && deviceId) {
      for (const ent of Object.values(this.hass.entities)) {
        if (
          ent.device_id === deviceId &&
          ent.translation_key === translationKey &&
          (!domain || ent.entity_id.startsWith(`${domain}.`))
        ) {
          const stateObj = this.hass.states[ent.entity_id];
          if (stateObj) return stateObj;
        }
      }
    }

    // Fallback: search states by naming patterns
    const states = Object.values(this.hass.states);
    return states.find((s) => {
      if (domain && !s.entity_id.startsWith(`${domain}.`)) return false;
      if (this.hass?.entities) {
        const reg = this.hass.entities[s.entity_id];
        if (reg && reg.platform !== "unraid") return false;
      }
      const objectId = s.entity_id.split(".")[1] || "";
      const keyMatch =
        objectId.endsWith(`_${translationKey}`) ||
        objectId === translationKey ||
        (translationKey === "uptime" &&
          (objectId.endsWith("_up_since") || objectId === "up_since")) ||
        (translationKey === "network_interface_ip" &&
          objectId.includes("_network_") &&
          (objectId.endsWith("_ip") || objectId.endsWith("_ip_address"))) ||
        (translationKey === "network_access" &&
          objectId.endsWith("_network_access"));

      if (device?.name) {
        const cleanName = device.name.toLowerCase().replace(/[^a-z0-9]/g, "_");
        return keyMatch && objectId.includes(cleanName);
      }
      return keyMatch;
    });
  }

  /**
   * Get all network interface metrics for active server.
   */
  protected getNetworkInterfaces(): Array<{
    name: string;
    displayName: string;
    ip?: HassEntity;
    speed?: HassEntity;
    rx?: HassEntity;
    tx?: HassEntity;
    link?: HassEntity;
  }> {
    if (!this.hass?.states) return [];
    const device = this.getActiveDevice();
    const cleanName = device?.name
      ? device.name.toLowerCase().replace(/[^a-z0-9]/g, "_")
      : undefined;

    const ifaceMap = new Map<
      string,
      {
        name: string;
        displayName: string;
        ip?: HassEntity;
        speed?: HassEntity;
        rx?: HassEntity;
        tx?: HassEntity;
        link?: HassEntity;
      }
    >();

    for (const [entityId, stateObj] of Object.entries(this.hass.states)) {
      if (cleanName && !entityId.includes(cleanName)) continue;
      const match = entityId.match(
        /_network_([a-zA-Z0-9_-]+)_(inbound(?:_throughput)?|outbound(?:_throughput)?|rx(?:_throughput)?|tx(?:_throughput)?|speed|ip|ip_address|link)$/i
      );
      if (!match || !match[1] || !match[2]) continue;
      const ifaceName = match[1];
      const prop = match[2].toLowerCase();

      if (!ifaceMap.has(ifaceName)) {
        ifaceMap.set(ifaceName, {
          name: ifaceName,
          displayName: ifaceName.toUpperCase(),
        });
      }
      const entry = ifaceMap.get(ifaceName)!;
      if (prop.startsWith("inbound") || prop.startsWith("rx")) entry.rx = stateObj;
      else if (prop.startsWith("outbound") || prop.startsWith("tx")) entry.tx = stateObj;
      else if (prop === "speed") entry.speed = stateObj;
      else if (prop === "ip" || prop === "ip_address") entry.ip = stateObj;
      else if (prop === "link") entry.link = stateObj;
    }

    return Array.from(ifaceMap.values()).sort((a, b) =>
      a.name.localeCompare(b.name, undefined, { numeric: true })
    );
  }

  /**
   * Get boot/flash disk usage entity if present.
   */
  protected getBootDiskEntity(): HassEntity | undefined {
    if (!this.hass?.states) return undefined;
    const device = this.getActiveDevice();
    const cleanName = device?.name
      ? device.name.toLowerCase().replace(/[^a-z0-9]/g, "_")
      : undefined;

    return Object.values(this.hass.states).find((s) => {
      if (!s.entity_id.startsWith("sensor.")) return false;
      if (cleanName && !s.entity_id.includes(cleanName)) return false;
      return (
        (s.entity_id.includes("_disk_flash_") ||
          s.entity_id.includes("_disk_boot_")) &&
        s.entity_id.endsWith("_usage")
      );
    });
  }

  /**
   * Find all entities matching a translation key (e.g. disks, docker containers).
   */
  protected getEntities(
    translationKey: string,
    domain?: string
  ): HassEntity[] {
    if (!this.hass?.states) return [];
    const device = this.getActiveDevice();
    const deviceId = device?.id;

    if (this.hass.entities && deviceId) {
      const matches: HassEntity[] = [];
      for (const ent of Object.values(this.hass.entities)) {
        if (
          ent.device_id === deviceId &&
          ent.translation_key === translationKey &&
          (!domain || ent.entity_id.startsWith(`${domain}.`))
        ) {
          const stateObj = this.hass.states[ent.entity_id];
          if (stateObj) matches.push(stateObj);
        }
      }
      if (matches.length > 0) return matches;
    }

    // Fallback to name pattern
    const cleanName = device?.name
      ? device.name.toLowerCase().replace(/[^a-z0-9]/g, "_")
      : undefined;

    const matchesTranslation = (s: HassEntity) => {
      if (this.hass?.entities) {
        const reg = this.hass.entities[s.entity_id];
        if (reg && reg.platform !== "unraid") return false;
      }
      if (translationKey === "disk_usage") {
        return (
          (s.entity_id.includes("_disk_") ||
            s.entity_id.includes("_cache") ||
            s.entity_id.includes("_parity") ||
            s.entity_id.includes("_boot") ||
            s.entity_id.includes("_flash")) &&
          s.entity_id.endsWith("_usage") &&
          !s.entity_id.includes("_array_usage") &&
          !s.entity_id.includes("_share_")
        );
      }
      if (translationKey === "disk_temperature") {
        return (
          (s.entity_id.includes("_disk_") ||
            s.entity_id.includes("_cache") ||
            s.entity_id.includes("_parity") ||
            s.entity_id.includes("_boot")) &&
          (s.entity_id.endsWith("_temperature") || s.entity_id.includes("_temp"))
        );
      }
      if (translationKey === "disk_spin") {
        return (
          (s.entity_id.includes("_disk_") ||
            s.entity_id.includes("_cache") ||
            s.entity_id.includes("_parity")) &&
          s.entity_id.includes("_spin")
        );
      }
      if (translationKey === "disk_health") {
        return (
          (s.entity_id.includes("_disk_") ||
            s.entity_id.includes("_cache") ||
            s.entity_id.includes("_parity") ||
            s.entity_id.includes("_boot")) &&
          (s.entity_id.endsWith("_health") || s.entity_id.includes("_health_"))
        );
      }
      if (translationKey === "share_usage" || translationKey === "share") {
        return (
          s.entity_id.includes("_share_") &&
          s.entity_id.endsWith("_usage")
        );
      }
      const objectId = s.entity_id.split(".")[1] || "";
      return (
        objectId === translationKey ||
        objectId.endsWith(`_${translationKey}`) ||
        objectId.includes(`_${translationKey}_`) ||
        objectId.startsWith(`${translationKey}_`)
      );
    };

    const states = Object.values(this.hass.states);
    const domainStates = domain
      ? states.filter((s) => s.entity_id.startsWith(`${domain}.`))
      : states;

    if (cleanName) {
      return domainStates.filter(
        (s) => s.entity_id.includes(cleanName) && matchesTranslation(s)
      );
    }

    return domainStates.filter((s) => matchesTranslation(s));
  }

  /**
   * Find an entity by exact or regex pattern
   */
  protected findEntity(pattern: RegExp | string): HassEntity | undefined {
    if (!this.hass?.states) return undefined;
    if (typeof pattern === "string") {
      return this.hass.states[pattern];
    }
    return Object.values(this.hass.states).find((s) =>
      pattern.test(s.entity_id)
    );
  }

  /** Toggle switch service call */
  protected async toggleEntity(entityId: string): Promise<void> {
    if (!this.hass) return;
    const domain = entityId.split(".")[0] || "homeassistant";
    await this.hass.callService(domain, "toggle", { entity_id: entityId });
  }

  /** Press button service call */
  protected async pressButton(entityId: string): Promise<void> {
    if (!this.hass) return;
    await this.hass.callService("button", "press", { entity_id: entityId });
  }

  /** Open more info popup */
  protected openMoreInfo(entityId: string): void {
    fireEvent(this, "hass-more-info", { entityId });
  }

  protected renderHeader(
    title: string,
    subtitle: string,
    iconPath: string,
    badgeContent?: TemplateResult
  ): TemplateResult | typeof nothing {
    if (this.config.embedded || this.config.hide_header) {
      return nothing;
    }
    return html`
      <div class="header">
        <div class="header-main">
          <div class="header-icon">${iconTemplate(iconPath, 22)}</div>
          <div class="header-titles">
            <span class="header-title">${title}</span>
            <span class="header-subtitle">${subtitle}</span>
          </div>
        </div>
        ${badgeContent ? html`<div class="header-actions">${badgeContent}</div>` : ""}
      </div>
    `;
  }
}
