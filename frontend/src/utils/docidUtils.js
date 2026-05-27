/**
 * Formats a DOCiD identifier for proper use in path segments of internal URLs.
 *
 * As of the Google Scholar canonicalization work, DOCiD landing pages live at
 * the slash-form URL `/docid/<prefix>/<suffix>` (see frontend/src/middleware.js
 * which 301-redirects the legacy `%2F` form to this canonical form). For
 * internal `<Link>` / `router.push` calls into the landing page, pass the
 * DOCiD through unchanged — embed a literal `/` between prefix and suffix.
 *
 * This helper now returns the unencoded value so callers that previously
 * did `/docid/${formatDocIdForUrl(d)}` continue to produce the canonical URL
 * without code changes.
 *
 * @param {string} docid - The DOCiD identifier (e.g. `20.500.14351/<suffix>`)
 * @returns {string} - The DOCiD as-is, suitable for inlining into the slash-form path
 */
export const formatDocIdForUrl = (docid) => {
  if (!docid) return '';
  // Decode any pre-encoded slashes back to literal `/` so URL is canonical.
  return docid.replace(/%2F/gi, '/');
};

/**
 * Formats a DOCiD identifier for display purposes
 * Decodes encoded slashes for better readability
 * 
 * @param {string} docid - The potentially encoded DOCiD identifier
 * @returns {string} - Properly formatted DOCiD for display
 */
export const formatDocIdForDisplay = (docid) => {
  if (!docid) return '';
  
  // Replace encoded slashes with visible slashes for display
  return docid.replace(/%2F/g, '/');
};

/**
 * Creates a properly formatted URL for a DOCiD
 * 
 * @param {string} docid - The DOCiD identifier
 * @returns {string} - Complete URL path to the DOCiD
 */
export const getDocIdUrl = (docid) => {
  if (!docid) return '';
  
  return `/docid/${formatDocIdForUrl(docid)}`;
};
