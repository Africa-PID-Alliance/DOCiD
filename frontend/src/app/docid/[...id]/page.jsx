// Server Component: emits the Google-Scholar-crawlable landing page for a
// DOCiD record (Highwire `citation_*` meta tags, JSON-LD, visible scholarly
// body) BEFORE any client JS runs. Interactive features (comments, share,
// like, edit, version history) live in the DocIDClient client island.

import { notFound } from 'next/navigation';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';
import {
  buildHighwireMetaOther,
  buildJsonLd,
  canonicalDocidUrl,
  formatAuthorName,
  formatHighwireDate,
  pickPdfUrl,
  safeJsonLd,
  stripHtml,
} from '@/lib/highwire';
import DocIDClient from './DocIDClient';

function joinDocidSegments(params) {
  // Next.js dynamic catch-all `[...id]` gives params.id as an array.
  // The DOCiD has the form `<prefix>/<suffix>` -> two segments.
  const raw = Array.isArray(params?.id) ? params.id.join('/') : params?.id || '';
  return decodeURIComponent(raw);
}

async function fetchPublication(docid) {
  if (!docid) return null;
  const base = getBackendApiV1BaseUrl();
  const url = `${base}/publications/docid?docid=${encodeURIComponent(docid)}`;
  try {
    // Use next.revalidate so the page renders as a (revalidating) static
    // RSC. Dynamic (`cache: 'no-store'`) pages stream metadata via React
    // Flight — Highwire citation tags then land in the head only after
    // client-side hydration, which Google Scholar may not perform.
    const res = await fetch(url, {
      next: { revalidate: 60 },
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error('SSR fetch failed for DOCiD', docid, err);
    return null;
  }
}

// NOTE: `generateMetadata` is intentionally NOT used for Highwire citation_*
// tags. In Next 15.2.6 the metadata API streams its output via React Flight
// (RSC payload) — the <meta> elements are not present in the initial HTML
// response that Google Scholar reads. Instead we emit <meta>, <title>, and
// <link rel="canonical"> as plain JSX children of the Server Component
// below; React 19 hoists them to <head> synchronously because they're not
// inside a Suspense boundary, so they land in the first byte of the HTML.
// We keep a minimal generateMetadata only for the `notFound()` fallback so
// crawl errors don't leak a usable page title.
export async function generateMetadata({ params }) {
  const awaited = typeof params?.then === 'function' ? await params : params;
  const docid = joinDocidSegments(awaited);
  const publication = await fetchPublication(docid);
  if (!publication) {
    return {
      title: 'DOCiD not found',
      robots: { index: false, follow: false },
    };
  }
  // Return only the title here so the browser tab is correct even before
  // streaming completes. Other metadata is emitted as JSX below.
  return { title: publication.document_title || `DOCiD ${docid}` };
}

export default async function DocIDLandingPage({ params }) {
  const awaited = typeof params?.then === 'function' ? await params : params;
  const docid = joinDocidSegments(awaited);
  const publication = await fetchPublication(docid);
  if (!publication) notFound();

  const authors = (publication.publication_creators || [])
    .map(formatAuthorName)
    .filter(Boolean);
  const date = formatHighwireDate(publication.published);
  const abstract = stripHtml(publication.abstract_text || publication.document_description);
  const pdfUrl = pickPdfUrl(publication);
  const canonical = canonicalDocidUrl(publication.document_docid || docid);
  const jsonLd = buildJsonLd(publication);
  // Pre-serialize with Unicode-escape of <, >, &, U+2028, U+2029 so the value
  // is safe to inline inside <script type="application/ld+json">. See
  // safeJsonLd() in src/lib/highwire.js.
  const jsonLdSerialized = jsonLd ? safeJsonLd(jsonLd) : null;

  // Build the Highwire `citation_*` (and DC.*) tag set as a flat list React 19
  // will hoist into <head> when rendered as JSX children of the Server
  // Component. Repeated keys produce one <meta> tag per array element.
  const metaTags = [];
  const metaEntries = buildHighwireMetaOther(publication);
  for (const [name, value] of Object.entries(metaEntries)) {
    if (Array.isArray(value)) {
      for (let i = 0; i < value.length; i += 1) {
        metaTags.push(<meta key={`${name}-${i}`} name={name} content={value[i]} />);
      }
    } else {
      metaTags.push(<meta key={name} name={name} content={value} />);
    }
  }
  const description =
    stripHtml(publication.abstract_text || publication.document_description) ||
    `Scholarly record on the Africa PID Alliance DOCiD platform.`;
  const titleText = publication.document_title || `DOCiD ${docid}`;

  return (
    <>
      {/* Metadata emitted as JSX. React 19 (used by Next 15) auto-hoists
          <title>, <meta>, and <link> elements to <head>. Because these are
          NOT inside a Suspense boundary they land in the initial HTML byte
          — required for Google Scholar, which does not run client JS. */}
      <title>{titleText}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={canonical} />
      <meta property="og:type" content="article" />
      <meta property="og:title" content={titleText} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={canonical} />
      <meta property="og:site_name" content="DOCiD" />
      <meta name="twitter:card" content="summary" />
      <meta name="twitter:title" content={titleText} />
      <meta name="twitter:description" content={description} />
      {metaTags}
      {/*
        Crawl-only scholarly metadata block. Kept in the SSR DOM (so Google
        Scholar / Googlebot read title, authors, date, abstract, and JSON-LD
        without executing JS) but visually hidden so it does not duplicate
        the rich MUI card rendered below by DocIDClient. Uses the standard
        "visually-hidden" pattern (clip-path) — content remains in the
        accessibility tree and source HTML; bots see everything.
      */}
      <article
        itemScope
        itemType="https://schema.org/ScholarlyArticle"
        style={{
          position: 'absolute',
          width: 1,
          height: 1,
          padding: 0,
          margin: -1,
          overflow: 'hidden',
          clip: 'rect(0 0 0 0)',
          whiteSpace: 'nowrap',
          border: 0,
        }}
      >
        <h1 itemProp="name headline" style={{ fontSize: '1.6rem', margin: '0 0 8px' }}>
          {publication.document_title}
        </h1>

        {authors.length > 0 && (
          <p className="authors" style={{ margin: '0 0 4px', color: '#444' }}>
            {authors.map((a, i) => (
              <span key={i} itemProp="author" itemScope itemType="https://schema.org/Person">
                <span itemProp="name">{a}</span>
                {i < authors.length - 1 ? '; ' : ''}
              </span>
            ))}
          </p>
        )}

        {date && (
          <p style={{ margin: '0 0 12px', color: '#666' }}>
            Published:{' '}
            <time itemProp="datePublished" dateTime={date.replace(/\//g, '-')}>
              {date.replace(/\//g, '-')}
            </time>
          </p>
        )}

        {abstract && (
          <section>
            <h2 style={{ fontSize: '1.1rem', margin: '12px 0 6px' }}>Abstract</h2>
            <p itemProp="description" style={{ margin: 0, lineHeight: 1.55 }}>
              {abstract}
            </p>
          </section>
        )}

        <section style={{ marginTop: 12 }}>
          <h2 style={{ fontSize: '1.1rem', margin: '12px 0 6px' }}>Identifiers</h2>
          <ul style={{ margin: 0, paddingLeft: '1.2em' }}>
            <li>
              DOCiD:{' '}
              <a href={canonical} itemProp="identifier" rel="canonical">
                {publication.document_docid || docid}
              </a>
            </li>
            {publication.doi && (
              <li>
                DOI:{' '}
                <a
                  href={`https://doi.org/${publication.doi}`}
                  itemProp="identifier"
                  rel="noopener"
                >
                  {publication.doi}
                </a>
              </li>
            )}
            {publication.openalex_id && (
              <li>
                OpenAlex:{' '}
                <a href={publication.openalex_id} rel="noopener" itemProp="sameAs">
                  {publication.openalex_id}
                </a>
              </li>
            )}
            {publication.handle_url && (
              <li>
                Handle:{' '}
                <a href={publication.handle_url} rel="noopener">
                  {publication.handle_url}
                </a>
              </li>
            )}
          </ul>
        </section>

        {pdfUrl && (
          <p style={{ marginTop: 12 }}>
            <a href={pdfUrl} itemProp="encoding">
              Download full text PDF
            </a>
          </p>
        )}
      </article>

      {jsonLdSerialized && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: jsonLdSerialized }}
        />
      )}

      <DocIDClient initialPublication={publication} docId={docid} />
    </>
  );
}
