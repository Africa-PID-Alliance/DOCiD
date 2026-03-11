/**
 * Single source of truth for the Flask backend API URL.
 * Used by all Next.js API proxy routes (server-side only).
 *
 * Set BACKEND_API_URL in .env.production / .env.local to override.
 * Default: http://127.0.0.1:5001/api
 */
export const BACKEND_API_URL = process.env.BACKEND_API_URL || 'http://127.0.0.1:5001/api';
