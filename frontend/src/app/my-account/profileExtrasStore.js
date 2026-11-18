/**
 * Storage for profile values that ORCID does not provide and the DOCiD user-profile API
 * has no fields for yet (research field, languages, licensing, etc.).
 *
 * Currently saved in the browser (localStorage, per user). When the API gains fields for
 * these, replace loadProfileExtras / saveProfileExtras with calls to that endpoint —
 * nothing else needs to change.
 */
const key = (userId) => `docid_profile_extras_${userId}`;

export async function loadProfileExtras(userId) {
  if (!userId || typeof window === 'undefined') return {};
  try {
    return JSON.parse(localStorage.getItem(key(userId)) || '{}');
  } catch {
    return {};
  }
}

export async function saveProfileExtras(userId, extras) {
  if (!userId || typeof window === 'undefined') return extras;
  localStorage.setItem(key(userId), JSON.stringify(extras || {}));
  return extras;
}
