declare module 'vite-env' {
  interface ImportMetaEnv {
    VITE_API_BASE_URL: string;
    DEV: boolean;
    PROD: boolean;
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
} 