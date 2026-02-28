/// <reference types="vite/client" />

declare interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_SUPABASE_URL?: string;
  readonly VITE_SUPABASE_ANON_KEY?: string;
  readonly VITE_APP_BASE_URL?: string;
  readonly VITE_GA_ID?: string;
  readonly VITE_HOTJAR_ID?: string;
  readonly VITE_GOOGLE_API_KEY?: string;
  readonly VITE_GOOGLE_CLIENT_ID?: string;
  readonly VITE_GOOGLE_SEARCH_CX?: string;
  readonly DEV?: boolean;
  readonly PROD?: boolean;
}

declare interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Network Information API (draft)
interface NetworkInformation {
  readonly saveData?: boolean;
}

// Battery Status API (draft)
interface BatteryManager {
  readonly level: number;
  readonly charging: boolean;
  addEventListener(type: string, listener: EventListener): void;
  removeEventListener(type: string, listener: EventListener): void;
}

interface Navigator {
  connection?: NetworkInformation;
  getBattery?(): Promise<BatteryManager>;
}

// Google Analytics gtag
interface Window {
  gtag?: (command: string, ...args: unknown[]) => void;
}
