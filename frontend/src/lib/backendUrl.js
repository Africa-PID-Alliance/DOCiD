/**
 * Single source of truth for the Flask backend API URL.
 * Used by Next.js API proxy routes (server-side only).
 */
export const BACKEND_API_URL = process.env.BACKEND_API_URL || 'http://backend:5001/api';
