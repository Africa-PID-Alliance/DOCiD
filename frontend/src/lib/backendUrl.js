/**
 * Single source of truth for the Flask backend API URL.
 * Used by Next.js API proxy routes (server-side only).
 *
 * The analytics blueprint is registered WITHOUT a `/v1` prefix, so its
 * routes live at `/api/publications/<id>/views` — therefore this
 * constant ends in `/api` (no `/v1`). For versioned routes use
 * process.env.NEXT_PUBLIC_API_BASE_URL which ends in `/api/v1`.
 */
function resolveBackendApiUrl() {
  if (process.env.BACKEND_API_URL) {
    return process.env.BACKEND_API_URL.replace(/\/$/, '');
  }
  const versioned = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (versioned) {
    return versioned.replace(/\/$/, '').replace(/\/v\d+$/, '');
  }
  return 'http://localhost:5001/api';
}

export const BACKEND_API_URL = resolveBackendApiUrl();
