const config = {
  apiBaseUrl: '/api',
  isDevelopment: import.meta.env.MODE === 'development',
  isProduction: import.meta.env.PROD,
};

export function getConfig() {
  return config;
} 