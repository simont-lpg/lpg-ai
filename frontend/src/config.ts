export function getConfig() {
  return {
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
    isDevelopment: import.meta.env.DEV,
    isProduction: import.meta.env.PROD,
  };
} 