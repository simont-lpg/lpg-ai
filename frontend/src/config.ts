export function getConfig() {
  if (!import.meta.env.VITE_API_BASE_URL) {
    throw new Error("VITE_API_BASE_URL is not defined — please set it in your .env file");
  }

  return {
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL,
    isDevelopment: import.meta.env.DEV,
    isProduction: import.meta.env.PROD,
  };
} 