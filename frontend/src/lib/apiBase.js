const INTERNAL_API_BASE = 'http://backend:5001/api/v1';
const INTERNAL_BACKEND_BASE = 'http://backend:5001/api';

export function getBackendApiV1BaseUrl() {
  return process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || INTERNAL_API_BASE;
}

export function getBackendApiBaseUrl() {
  return process.env.BACKEND_API_URL || INTERNAL_BACKEND_BASE;
}
