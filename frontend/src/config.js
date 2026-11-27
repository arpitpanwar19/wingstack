const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL;

if (!configuredApiBaseUrl) {
  throw new Error('VITE_API_BASE_URL must be configured before starting the frontend.');
}

export const API_BASE_URL = configuredApiBaseUrl.replace(/\/$/, '');

const configuredGoogleAuthApiBaseUrl = import.meta.env.VITE_GOOGLE_AUTH_API_BASE_URL;
export const GOOGLE_AUTH_API_BASE_URL = configuredGoogleAuthApiBaseUrl
  ? configuredGoogleAuthApiBaseUrl.replace(/\/$/, '')
  : API_BASE_URL;