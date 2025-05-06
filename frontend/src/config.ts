const config = {
  apiBaseUrl: import.meta.env.PROD ? '' : '/api',
  isDevelopment: import.meta.env.MODE === 'development',
  isProduction: import.meta.env.PROD,
};

export function getConfig() {
  return config;
} 