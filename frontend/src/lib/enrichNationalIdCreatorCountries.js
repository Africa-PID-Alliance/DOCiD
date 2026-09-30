const NATIONAL_ID_TYPE = 'national_id';

export const isNationalIdCreatorRecord = (creator) =>
  String(creator?.identifier_type || '').trim().toLowerCase() === NATIONAL_ID_TYPE;

export const getCreatorDisplayName = (creator) => {
  const fromParts = [creator?.given_name, creator?.family_name].filter(Boolean).join(' ').trim();
  return fromParts || creator?.creator_name || creator?.family_name || '';
};

export const matchesMaskedNationalId = (maskedValue, fullValue) => {
  const masked = String(maskedValue || '');
  const full = String(fullValue || '');
  if (!masked || !full) return false;
  if (!masked.includes('*')) return masked === full;
  if (masked.length !== full.length) return false;
  for (let index = 0; index < masked.length; index += 1) {
    if (masked[index] !== '*' && masked[index] !== full[index]) return false;
  }
  return true;
};

export const pickNationalIdRegistryMatch = (creator, results = []) => {
  if (!results.length) return null;

  const creatorName = getCreatorDisplayName(creator).trim().toLowerCase();
  const nameMatches = results.filter(
    (result) => String(result?.name || '').trim().toLowerCase() === creatorName
  );
  const candidates = nameMatches.length ? nameMatches : results;

  if (creator?.identifier) {
    const idMatch = candidates.find((result) =>
      matchesMaskedNationalId(creator.identifier, result?.national_id_number)
    );
    if (idMatch) return idMatch;
  }

  return candidates[0] || null;
};

export const mergeCreatorCountries = (creators = [], countryById = {}) =>
  creators.map((creator) =>
    isNationalIdCreatorRecord(creator) && !creator.country && countryById[creator.id]
      ? { ...creator, country: countryById[creator.id] }
      : creator
  );

export async function enrichPublicationNationalIdCountries(publication, {
  fetchImpl = fetch,
  apiBaseUrl,
  authorizationHeader = '',
} = {}) {
  if (!publication?.publication_creators?.length) return publication;

  const needsCountry = publication.publication_creators.some(
    (creator) => isNationalIdCreatorRecord(creator) && !creator.country
  );
  if (!needsCountry) return publication;

  let creators = publication.publication_creators;
  const authHeaders = authorizationHeader
    ? { Authorization: authorizationHeader, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' };

  if (publication.id && authorizationHeader) {
    try {
      const editResponse = await fetchImpl(
        `${apiBaseUrl}/publications/get-publication-for-edit/${publication.id}`,
        { headers: authHeaders, cache: 'no-store' }
      );
      if (editResponse.ok) {
        const editData = await editResponse.json();
        const countryById = Object.fromEntries(
          (editData.publication_creators || [])
            .filter((creator) => isNationalIdCreatorRecord(creator) && creator.country)
            .map((creator) => [creator.id, creator.country])
        );
        creators = mergeCreatorCountries(creators, countryById);
      }
    } catch (error) {
      console.error('Failed to enrich national-ID creator countries from edit payload:', error);
    }
  }

  const stillMissing = creators.filter(
    (creator) => isNationalIdCreatorRecord(creator) && !creator.country
  );

  if (stillMissing.length && authorizationHeader) {
    const enriched = [...creators];
    for (const creator of stillMissing) {
      const searchName = getCreatorDisplayName(creator);
      if (searchName.length < 3) continue;

      try {
        const searchResponse = await fetchImpl(
          `${apiBaseUrl}/national-id/researchers/search?q=${encodeURIComponent(searchName)}&per_page=10`,
          { headers: authHeaders, cache: 'no-store' }
        );
        if (!searchResponse.ok) continue;

        const searchData = await searchResponse.json();
        const match = pickNationalIdRegistryMatch(creator, searchData.results || []);
        if (!match?.country) continue;

        const index = enriched.findIndex((item) => item.id === creator.id);
        if (index >= 0) {
          enriched[index] = { ...enriched[index], country: match.country };
        }
      } catch (error) {
        console.error('Failed to search national-ID registry for creator country:', error);
      }
    }
    creators = enriched;
  }

  return {
    ...publication,
    publication_creators: creators,
  };
}
