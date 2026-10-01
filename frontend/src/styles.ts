import { css } from "lit";

export const themeTokens = css`
  :host {
    --unraid-primary: var(--primary-color, #f25f22);
    --unraid-accent: #f25f22;
    --unraid-online: var(--success-color, #2ecc71);
    --unraid-warning: var(--warning-color, #f39c12);
    --unraid-error: var(--error-color, #e74c3c);
    --unraid-standby: var(--disabled-text-color, #7f8c8d);
    --unraid-info: var(--info-color, #3498db);
    --unraid-card-bg: var(--ha-card-background, var(--card-background-color, #1c1c20));
    --unraid-border: var(--ha-card-border-color, var(--divider-color, rgba(255, 255, 255, 0.08)));
    --unraid-radius: var(--ha-card-border-radius, 12px);
    --unraid-text: var(--primary-text-color, #e1e1e6);
    --unraid-subtext: var(--secondary-text-color, #8a8a93);
  }
`;
