const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  isDevelopment: import.meta.env.MODE === 'development',
  isProduction: import.meta.env.PROD,
};

export function getConfig() {
  return config;
} 