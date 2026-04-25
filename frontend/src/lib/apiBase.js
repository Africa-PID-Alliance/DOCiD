function getRequiredEnv(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export function getBackendApiV1BaseUrl() {
  return process.env.API_BASE_URL || getRequiredEnv('NEXT_PUBLIC_API_BASE_URL');
}

export function getBackendApiBaseUrl() {
  return getRequiredEnv('BACKEND_API_URL');
}
