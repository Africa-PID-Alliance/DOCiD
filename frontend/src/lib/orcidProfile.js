/**
 * ORCID -> DOCiD Individual profile mapping.
 *
 * ORCID is the primary source of truth: any value found here overrides the DOCiD value
 * and is shown read-only. Fields ORCID does not provide stay editable by the user.
 */
import { allCountries } from '@/data/locationData';

const v = (x) => (x && typeof x === 'object' && 'value' in x ? x.value : x) ?? '';
const clean = (s) => (typeof s === 'string' ? s.trim() : s);
const uniq = (arr) => [...new Set(arr.filter(Boolean).map(clean).filter(Boolean))];

export function countryNameFromCode(code) {
  if (!code) return '';
  let name = code;
  try {
    name = new Intl.DisplayNames(['en'], { type: 'region' }).of(code.toUpperCase()) || code;
  } catch { /* keep code */ }
  const lower = name.toLowerCase();
  const exact = allCountries.find((c) => c.toLowerCase() === lower);
  if (exact) return exact;
  const loose = allCountries.find((c) => lower.includes(c.toLowerCase()) || c.toLowerCase().includes(lower));
  return loose || name;
}

const yearOf = (d) => Number(v(d?.year)) || null;

function affiliationSummaries(section, key) {
  return (section?.['affiliation-group'] || [])
    .flatMap((g) => g.summaries || [])
    .map((s) => s[key])
    .filter(Boolean)
    .map((s) => ({
      organization: s.organization?.name || '',
      department: s['department-name'] || '',
      role: s['role-title'] || '',
      startYear: yearOf(s['start-date']),
      endYear: yearOf(s['end-date']),
      city: s.organization?.address?.city || '',
      country: s.organization?.address?.country || '',
    }));
}

const WORK_PREPRINT_TYPES = ['preprint', 'working-paper'];
const WORK_PUBLICATION_TYPES = [
  'journal-article', 'book', 'book-chapter', 'edited-book', 'conference-paper', 'conference-abstract',
  'review', 'book-review', 'dissertation-thesis', 'report', 'magazine-article', 'newspaper-article',
  'encyclopedia-entry', 'dictionary-entry', 'annotation', 'translation', 'conference-proceedings',
];

function formatWork(w) {
  const title = v(w.title?.title) || 'Untitled';
  const year = yearOf(w['publication-date']);
  const doi = (w['external-ids']?.['external-id'] || []).find((e) => e['external-id-type'] === 'doi');
  return {
    title,
    year,
    type: w.type || '',
    journal: v(w['journal-title']) || v(w.title?.subtitle),
    doi: doi?.['external-id-value'] || '',
    url: doi ? `https://doi.org/${doi['external-id-value']}` : v(w.url),
  };
}

/**
 * Turn an ORCID v3.0 record into normalized DOCiD profile values.
 * Every key is either a non-empty value (from ORCID) or empty ('' / []).
 */
export function mapOrcidRecord(record, orcidId) {
  if (!record) return null;
  const person = record.person || {};
  const acts = record['activities-summary'] || {};

  // --- Person ---
  const given = v(person.name?.['given-names']);
  const family = v(person.name?.['family-name']);
  const credit = v(person.name?.['credit-name']);
  const fullName = clean(credit || [given, family].filter(Boolean).join(' '));

  const keywords = uniq((person.keywords?.keyword || []).map((k) => k.content));
  const countryCode = v((person.addresses?.address || [])[0]?.country);
  const emails = uniq((person.emails?.email || []).map((e) => e.email));
  const extIds = person['external-identifiers']?.['external-identifier'] || [];
  const findExt = (re) => {
    const e = extIds.find((x) => re.test(x['external-id-type'] || ''));
    return e ? { value: e['external-id-value'], url: v(e['external-id-url']) } : null;
  };
  const urls = (person['researcher-urls']?.['researcher-url'] || []).map((u) => ({ name: u['url-name'] || '', url: v(u.url) }));
  const scholar = urls.find((u) => /scholar\.google/i.test(u.url));

  // --- Activities ---
  const employments = affiliationSummaries(acts.employments, 'employment-summary');
  const educations = affiliationSummaries(acts.educations, 'education-summary');
  const current = employments.find((e) => !e.endYear) || employments[0] || null;
  const firstYear = Math.min(...employments.map((e) => e.startYear).filter(Boolean));
  const yearsExperience = Number.isFinite(firstYear) ? Math.max(0, new Date().getFullYear() - firstYear) : null;

  const works = (acts.works?.group || [])
    .map((g) => (g['work-summary'] || [])[0])
    .filter(Boolean)
    .map(formatWork)
    .sort((a, b) => (b.year || 0) - (a.year || 0));

  const fundings = (acts.fundings?.group || [])
    .map((g) => (g['funding-summary'] || [])[0])
    .filter(Boolean)
    .map((f) => ({
      title: v(f.title?.title),
      funder: f.organization?.name || '',
      type: f.type || '',
      startYear: yearOf(f['start-date']),
      grantNumber: ((f['external-ids']?.['external-id'] || []).find((e) => e['external-id-type'] === 'grant_number') || {})['external-id-value'] || '',
    }));

  const orcidUrl = `https://orcid.org/${orcidId}`;

  return {
    orcidId,
    orcidUrl,
    lastModified: v(record.history?.['last-modified-date']) || v(person['last-modified-date']) || null,

    // Fields stored in DOCiD user-profile (synced via PUT /api/user-profile/{id})
    basic: {
      full_name: fullName,
      affiliation: current?.organization || '',
      role: current?.role || '',
      country: countryCode ? countryNameFromCode(countryCode) : '',
      orcid_id: orcidId,
    },

    // Display-only sections
    biography: clean(v(person.biography?.content)) || '',
    researchField: keywords.join(', '),
    yearsExperience: yearsExperience !== null ? String(yearsExperience) : '',
    recentPublications: works.filter((w) => WORK_PUBLICATION_TYPES.includes(w.type)).slice(0, 5),
    preprints: works.filter((w) => WORK_PREPRINT_TYPES.includes(w.type)).slice(0, 5),
    otherOutputs: works.filter((w) => !WORK_PUBLICATION_TYPES.includes(w.type) && !WORK_PREPRINT_TYPES.includes(w.type)).slice(0, 5),
    worksCount: works.length,
    funders: uniq(fundings.map((f) => f.funder)),
    grants: fundings.filter((f) => f.title),
    institutionalAffiliations: uniq([...employments, ...educations].map((a) => a.organization)),
    researcherId: findExt(/researcherid/i),
    scopusId: findExt(/scopus/i),
    googleScholar: scholar ? { value: scholar.url, url: scholar.url } : null,
    primaryContact: emails[0] || '',
    publicProfileLink: orcidUrl,
    researcherUrls: urls,
  };
}
