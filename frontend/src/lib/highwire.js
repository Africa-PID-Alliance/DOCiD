// Shared formatting helpers for Google Scholar (Highwire) metadata and JSON-LD.
// Used by the server-rendered DOCiD landing page, sitemap routes, and any
// future SSR surface that emits scholarly metadata.

export const SITE_ORIGIN =
  process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://docid.africapidalliance.org';

export function absolutize(url) {
  if (!url) return null;
  if (/^https?:\/\//i.test(url)) return url;
  const base = SITE_ORIGIN.replace(/\/+$/, '');
  return `${base}${url.startsWith('/') ? '' : '/'}${url}`;
}

// Strip HTML tags and collapse whitespace. document_description is stored as
// HTML markup (`<p>...</p>`); meta tags and JSON-LD need plain text.
export function stripHtml(value) {
  if (!value) return '';
  return String(value)
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/\s+/g, ' ')
    .trim();
}

// Highwire date format: YYYY/MM/DD. Accepts unix seconds (number), ISO string,
// or any value Date() can parse. Returns null when input is missing/invalid.
export function formatHighwireDate(value) {
  if (value === null || value === undefined || value === '') return null;
  let d;
  if (typeof value === 'number') {
    d = new Date(value * 1000);
  } else if (typeof value === 'string') {
    const asNumber = Number(value);
    d = Number.isFinite(asNumber) && /^\d+$/.test(value)
      ? new Date(asNumber * 1000)
      : new Date(value);
  } else if (value instanceof Date) {
    d = value;
  } else {
    return null;
  }
  if (Number.isNaN(d.getTime())) return null;
  const yyyy = d.getUTCFullYear();
  const mm = String(d.getUTCMonth() + 1).padStart(2, '0');
  const dd = String(d.getUTCDate()).padStart(2, '0');
  return `${yyyy}/${mm}/${dd}`;
}

// Scholar prefers "Family, Given" but accepts "Given Family". Backend stores
// family_name and given_name separately on publication_creators.
export function formatAuthorName(creator) {
  if (!creator) return null;
  const family = (creator.family_name || '').trim();
  const given = (creator.given_name || '').trim();
  if (family && given) return `${family}, ${given}`;
  return family || given || (creator.name || '').trim() || null;
}

export function formatAuthors(creators) {
  if (!Array.isArray(creators)) return [];
  return creators.map(formatAuthorName).filter(Boolean);
}

export function canonicalDocidUrl(docid) {
  if (!docid) return null;
  const clean = docid.replace(/%2F/gi, '/').replace(/^\/+|\/+$/g, '');
  return `${SITE_ORIGIN.replace(/\/+$/, '')}/docid/${clean}`;
}

// Return every PDF file attached to the publication, in canonical order:
// 1. files explicitly marked primary (`is_primary` truthy / `kind === 'manuscript'`)
// 2. files whose title matches the publication's document_title
// 3. files whose name hints at being the full text ("manuscript", "paper",
//    "fulltext", "full-text", "preprint", "article", "main")
// 4. remaining PDFs in their original order
// Used by both `pickPdfUrl` (the singular Highwire `citation_pdf_url`) and
// JSON-LD `encoding[]` (which lists every PDF so non-Scholar crawlers and
// discovery tools see supplementary materials too).
export function listPdfs(publication) {
  if (!publication) return [];
  const files = publication.publications_files || [];
  const isPdf = (f) => {
    const type = (f.file_type || '').toLowerCase();
    const name = (f.file_name || f.file_url || '').toLowerCase();
    return type.includes('pdf') || name.endsWith('.pdf');
  };
  const pdfs = files.filter(isPdf);
  if (pdfs.length === 0) return [];

  const docTitle = (publication.document_title || '').trim().toLowerCase();
  const fulltextRe = /\b(manuscript|paper|fulltext|full-text|preprint|article|main)\b/i;

  const score = (f) => {
    if (f.is_primary || (f.kind && String(f.kind).toLowerCase() === 'manuscript')) return 0;
    const title = (f.title || '').trim().toLowerCase();
    if (docTitle && title && title === docTitle) return 1;
    const name = `${f.title || ''} ${f.file_name || ''} ${f.file_url || ''}`;
    if (fulltextRe.test(name)) return 2;
    return 3;
  };

  // Stable sort by score, preserving original order within a bucket.
  return pdfs
    .map((f, i) => ({ f, i, s: score(f) }))
    .sort((a, b) => a.s - b.s || a.i - b.i)
    .map(({ f }) => f);
}

// Pick the canonical full-text PDF for the singular `citation_pdf_url` meta
// tag. Highwire / Google Scholar treat this tag as singular — supplementary
// PDFs go into the JSON-LD encoding[] list and the visible body instead.
export function pickPdfUrl(publication) {
  const pdfs = listPdfs(publication);
  const url = pdfs[0]?.file_url || null;
  return url ? absolutize(url) : null;
}

// Return absolute URLs of every PDF, in canonical order. Used to populate
// JSON-LD `encoding[]` so the supplementary materials are still discoverable
// by non-Scholar crawlers.
export function listPdfUrls(publication) {
  return listPdfs(publication)
    .map((f) => absolutize(f.file_url))
    .filter(Boolean);
}

// Escape `<`, `>`, `&`, ` `, ` ` inside a JSON.stringify result so
// it's safe to embed inside an inline <script type="application/ld+json">.
export function safeJsonLd(value) {
  return JSON.stringify(value)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026')
    .replace(new RegExp('\\u2028', 'g'), '\\u2028')
    .replace(new RegExp('\\u2029', 'g'), '\\u2029');
}

// Resource type id -> Highwire "type" subset selector.
// Numeric ids come from backend resource_types table; the labels are also
// accepted in case the API returns the joined name instead of the id.
export function resourceCategory(publication) {
  const rt = publication?.resource_type;
  const label = (typeof rt === 'string' ? rt : rt?.resource_type || '').toLowerCase();
  if (!label) return 'generic';
  if (label.includes('journal') || label.includes('article')) return 'journal';
  if (label.includes('conference') || label.includes('proceeding')) return 'conference';
  if (label.includes('thesis') || label.includes('dissertation')) return 'thesis';
  if (label.includes('report')) return 'report';
  return 'generic';
}

// Build the `metadata.other` block consumed by Next.js generateMetadata().
// Values that are arrays produce repeated <meta> tags in Next 15 (verified
// against frontend/node_modules/next/dist/lib/metadata/resolve-metadata.js).
export function buildHighwireMetaOther(publication) {
  if (!publication) return {};

  const title = publication.document_title || '';
  const authors = formatAuthors(publication.publication_creators);
  const date = formatHighwireDate(publication.published);
  const doi = publication.doi || null;
  const pdfUrl = pickPdfUrl(publication);
  const category = resourceCategory(publication);
  const journal = publication.journal_title || null;
  const issn = publication.issn || null;
  const volume = publication.volume || null;
  const issue = publication.issue || null;
  const firstPage = publication.first_page || null;
  const lastPage = publication.last_page || null;
  const conference = publication.conference_title || null;
  const dissertationInstitution = publication.dissertation_institution || null;
  const techReportInstitution = publication.technical_report_institution || null;
  const techReportNumber = publication.technical_report_number || null;
  const abstract = stripHtml(publication.abstract_text || publication.document_description) || null;
  const docid = publication.document_docid || null;

  const other = {};
  const set = (k, v) => {
    if (v === null || v === undefined || v === '') return;
    if (Array.isArray(v)) {
      if (v.length === 0) return;
      other[k] = v;
    } else {
      other[k] = v;
    }
  };

  set('citation_title', title);
  set('citation_author', authors);
  set('citation_publication_date', date);
  set('citation_doi', doi);
  set('citation_pdf_url', pdfUrl);

  if (category === 'journal') {
    set('citation_journal_title', journal);
    set('citation_issn', issn);
    set('citation_volume', volume);
    set('citation_issue', issue);
    set('citation_firstpage', firstPage);
    set('citation_lastpage', lastPage);
  } else if (category === 'conference') {
    set('citation_conference_title', conference);
    set('citation_firstpage', firstPage);
    set('citation_lastpage', lastPage);
  } else if (category === 'thesis') {
    set('citation_dissertation_institution', dissertationInstitution);
  } else if (category === 'report') {
    set('citation_technical_report_institution', techReportInstitution);
    set('citation_technical_report_number', techReportNumber);
  }

  // Dublin Core mirror (secondary support)
  set('DC.title', title);
  set('DC.creator', authors);
  set('DC.issued', date ? date.replace(/\//g, '-') : null);
  const dcIdentifiers = [];
  if (docid) dcIdentifiers.push(docid);
  if (doi) dcIdentifiers.push(doi);
  set('DC.identifier', dcIdentifiers);
  set('DC.publisher', 'Africa PID Alliance');
  set('DC.description', abstract);

  return other;
}

// Build a schema.org/ScholarlyArticle JSON-LD document for inline embedding.
export function buildJsonLd(publication) {
  if (!publication) return null;

  const canonical = canonicalDocidUrl(publication.document_docid);
  const authors = (publication.publication_creators || [])
    .map((c) => {
      const name = formatAuthorName(c);
      if (!name) return null;
      const node = { '@type': 'Person', name };
      if (c.identifier) node.identifier = c.identifier;
      return node;
    })
    .filter(Boolean);

  const identifiers = [];
  if (publication.document_docid) identifiers.push(publication.document_docid);
  if (publication.doi) identifiers.push(publication.doi);
  if (publication.openalex_id) identifiers.push(publication.openalex_id);

  const datePublished = (() => {
    const v = publication.published;
    if (!v) return null;
    if (typeof v === 'number') return new Date(v * 1000).toISOString().slice(0, 10);
    const asNum = Number(v);
    if (Number.isFinite(asNum) && /^\d+$/.test(String(v))) {
      return new Date(asNum * 1000).toISOString().slice(0, 10);
    }
    const d = new Date(v);
    return Number.isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10);
  })();

  const doc = {
    '@context': 'https://schema.org',
    '@type': 'ScholarlyArticle',
    '@id': canonical,
    url: canonical,
    name: publication.document_title || '',
    headline: publication.document_title || '',
    identifier: identifiers,
    author: authors,
    datePublished,
    description: stripHtml(publication.abstract_text || publication.document_description) || '',
    publisher: {
      '@type': 'Organization',
      name: 'Africa PID Alliance',
    },
  };

  // List every attached PDF in schema.org `encoding[]`. The first entry is
  // the canonical full text (same URL as the singular citation_pdf_url meta
  // tag); subsequent entries are supplementary materials. Single object vs.
  // array per schema.org spec — a single MediaObject when only one PDF.
  const pdfUrls = listPdfUrls(publication);
  if (pdfUrls.length === 1) {
    doc.encoding = {
      '@type': 'MediaObject',
      contentUrl: pdfUrls[0],
      encodingFormat: 'application/pdf',
    };
  } else if (pdfUrls.length > 1) {
    doc.encoding = pdfUrls.map((url) => ({
      '@type': 'MediaObject',
      contentUrl: url,
      encodingFormat: 'application/pdf',
    }));
  }

  return doc;
}
