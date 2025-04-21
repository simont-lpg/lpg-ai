// Get API base URL from environment variable
const API_BASE_URL = (() => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (!envUrl) {
    console.warn('VITE_API_BASE_URL is not set. Using default development URL.');
    return 'http://localhost:8000';
  }
  return envUrl;
})();

export const config = {
  api: {
    baseUrl: API_BASE_URL,
    endpoints: {
      files: `${API_BASE_URL}/files`,
      documents: `${API_BASE_URL}/documents`,
      ingest: `${API_BASE_URL}/ingest`,
      query: `${API_BASE_URL}/query`,
    },
  },
  // Add other configuration as needed
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
}; 