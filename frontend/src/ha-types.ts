export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  last_changed: string;
  last_updated: string;
}

export type HassEntities = Record<string, HassEntity>;

export interface DeviceRegistryEntry {
  id: string;
  name: string;
  name_by_user?: string | null;
  identifiers: [string, string][];
  manufacturer?: string | null;
  model?: string | null;
  sw_version?: string | null;
  hw_version?: string | null;
}

export interface EntityRegistryEntry {
  entity_id: string;
  device_id?: string | null;
  platform?: string;
  translation_key?: string;
  original_name?: string;
  name?: string | null;
}

export interface HomeAssistant {
  states: HassEntities;
  devices?: Record<string, DeviceRegistryEntry>;
  entities?: Record<string, EntityRegistryEntry>;
  callService: (
    domain: string,
    service: string,
    serviceData?: Record<string, unknown>
  ) => Promise<unknown>;
}

export function fireEvent(
  node: HTMLElement | Window,
  type: string,
  detail?: unknown,
  options?: { bubbles?: boolean; cancelable?: boolean; composed?: boolean }
): Event {
  const event = new CustomEvent(type, {
    bubbles: options?.bubbles ?? true,
    cancelable: Boolean(options?.cancelable),
    composed: options?.composed ?? true,
    detail,
  });
  node.dispatchEvent(event);
  return event;
}
