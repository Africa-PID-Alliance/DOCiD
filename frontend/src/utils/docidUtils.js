/**
 * Formats a DOCiD identifier for proper use in URLs
 * Ensures all forward slashes are properly encoded as %2F
 * 
 * @param {string} docid - The DOCiD identifier to format
 * @returns {string} - Properly formatted DOCiD for URL use
 */
export const formatDocIdForUrl = (docid) => {
  if (!docid) return '';
  
  // Replace any unencoded forward slashes with %2F
  return docid.replace(/\//g, '%2F');
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
