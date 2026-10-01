export const SERVER_CARD_TAG = "unraid-server-card";
export const SERVER_EDITOR_TAG = "unraid-server-card-editor";

export const STORAGE_CARD_TAG = "unraid-storage-card";
export const STORAGE_EDITOR_TAG = "unraid-storage-card-editor";

export const DOCKER_CARD_TAG = "unraid-docker-card";
export const DOCKER_EDITOR_TAG = "unraid-docker-card-editor";

export const UPS_CARD_TAG = "unraid-ups-card";
export const UPS_EDITOR_TAG = "unraid-ups-card-editor";

export const VM_CARD_TAG = "unraid-vm-card";
export const VM_EDITOR_TAG = "unraid-vm-card-editor";

export const DASHBOARD_CARD_TAG = "unraid-dashboard-card";
export const DASHBOARD_EDITOR_TAG = "unraid-dashboard-card-editor";

export interface CardConfig {
  type: string;
  server?: string;
  name?: string;
  title?: string;
  view_mode?: "grid" | "list";
  show_system_info?: boolean;
  show_motherboard?: boolean;
  show_user_shares?: boolean;
  embedded?: boolean;
  hide_header?: boolean;
  [key: string]: unknown;
}
