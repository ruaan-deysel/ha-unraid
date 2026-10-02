import {
  mdiAlertCircle,
  mdiArrowDown,
  mdiArrowUp,
  mdiBattery,
  mdiBatteryAlert,
  mdiBatteryCharging,
  mdiCheckCircle,
  mdiChevronDown,
  mdiChevronUp,
  mdiClockOutline,
  mdiCog,
  mdiCpu64Bit,
  mdiCubeOutline,
  mdiDocker,
  mdiDownload,
  mdiEthernet,
  mdiFlash,
  mdiFolder,
  mdiHarddisk,
  mdiInformation,
  mdiLanConnect,
  mdiMemory,
  mdiMonitor,
  mdiPause,
  mdiPlay,
  mdiPower,
  mdiRestart,
  mdiServer,
  mdiShieldAlert,
  mdiShieldCheck,
  mdiSpeedometer,
  mdiStop,
  mdiUpload,
  mdiUsbFlashDrive,
  mdiViewGrid,
  mdiViewList,
} from "@mdi/js";
import { html, type TemplateResult } from "lit";

export {
  mdiAlertCircle,
  mdiArrowDown,
  mdiArrowUp,
  mdiBattery,
  mdiBatteryAlert,
  mdiBatteryCharging,
  mdiCheckCircle,
  mdiChevronDown,
  mdiChevronUp,
  mdiClockOutline,
  mdiCog,
  mdiCpu64Bit,
  mdiCubeOutline,
  mdiDocker,
  mdiDownload,
  mdiEthernet,
  mdiFlash,
  mdiFolder,
  mdiHarddisk,
  mdiInformation,
  mdiLanConnect,
  mdiMemory,
  mdiMonitor,
  mdiPause,
  mdiPlay,
  mdiPower,
  mdiRestart,
  mdiServer,
  mdiShieldAlert,
  mdiShieldCheck,
  mdiSpeedometer,
  mdiStop,
  mdiUpload,
  mdiUsbFlashDrive,
  mdiViewGrid,
  mdiViewList,
};

export function iconTemplate(
  path: string,
  size = 20,
  className = "icon"
): TemplateResult {
  return html`
    <svg
      class="${className}"
      style="width: ${size}px; height: ${size}px;"
      viewBox="0 0 24 24"
    >
      <path d="${path}" fill="currentColor"></path>
    </svg>
  `;
}
