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
  listPdfs,
  safeHref,
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
    // `no-store` is required so a soft-delete in Flask shows the tombstone
    // immediately on next page load. The 60s revalidate cache would otherwise
    // keep serving the pre-deletion HTML (with full metadata) to crawlers.
    // Trade-off accepted: this route is low-volume relative to the API.
    const res = await fetch(url, {
      cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error('SSR fetch failed for DOCiD', docid, err);
    return null;
  }
}

// All `<head>` metadata is emitted via generateMetadata(). With Next 15.4's
// `htmlLimitedBots` regex (see next.config.js), this output renders into the
// initial HTML <head> as blocking content for crawlers (Googlebot, Scholar,
// Bingbot, social bots) and as streamed RSC for real browsers. JSON-LD is
// the only metadata that can't go through this API — it stays as an inline
// <script> in the JSX body below.
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

  // Retired DOCiDs: emit a tombstone <head> so handles still resolve to a
  // 200 page but the record ages out of Scholar/Bing and isn't preserved in
  // their cache snapshots. No Highwire citation_*, no JSON-LD, no OG image,
  // no old description.
  if (publication.deleted) {
    const canonical = canonicalDocidUrl(publication.document_docid || docid);
    return {
      title: 'DOCiD [retired]',
      description: 'This DOCiD has been retired by the original creator.',
      alternates: { canonical },
      robots: { index: false, follow: false, noarchive: true, nosnippet: true },
      openGraph: {
        type: 'article',
        url: canonical,
        title: 'DOCiD [retired]',
        siteName: 'DOCiD',
      },
      twitter: {
        card: 'summary',
        title: 'DOCiD [retired]',
      },
    };
  }

  const title = publication.document_title || `DOCiD ${docid}`;
  const description =
    stripHtml(publication.abstract_text || publication.document_description) ||
    `Scholarly record on the Africa PID Alliance DOCiD platform.`;
  const canonical = canonicalDocidUrl(publication.document_docid || docid);

  return {
    title,
    description,
    alternates: { canonical },
    openGraph: {
      type: 'article',
      url: canonical,
      title,
      description,
      siteName: 'DOCiD',
    },
    twitter: {
      card: 'summary',
      title,
      description,
    },
    other: buildHighwireMetaOther(publication),
  };
}

export default async function DocIDLandingPage({ params }) {
  const awaited = typeof params?.then === 'function' ? await params : params;
  const docid = joinDocidSegments(awaited);
  const publication = await fetchPublication(docid);
  if (!publication) notFound();

  // Tombstone branch — render a minimal "retired" panel so the handle keeps
  // resolving without leaking the old metadata. No client island, no Highwire
  // block, no JSON-LD.
  if (publication.deleted) {
    const canonical = canonicalDocidUrl(publication.document_docid || docid);
    const deletedAt = publication.deleted_at
      ? new Date(publication.deleted_at).toLocaleDateString(undefined, {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        })
      : null;
    return (
      <main
        style={{
          maxWidth: 720,
          margin: '64px auto',
          padding: '32px 24px',
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          color: '#333',
        }}
      >
        <div
          style={{
            border: '1px solid #ddd',
            borderRadius: 8,
            padding: '32px 28px',
            background: '#fafafa',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 14, color: '#888', letterSpacing: 1, marginBottom: 12 }}>
            DOCiD · RETIRED
          </div>
          <h1 style={{ fontSize: '1.4rem', margin: '0 0 12px', color: '#444' }}>
            This DOCiD has been retired
          </h1>
          <p style={{ margin: '0 0 16px', lineHeight: 1.6 }}>
            This Digital Object Container Identifier has been retired by the original creator. The
            handle continues to resolve to this page so existing citations don&apos;t break.
          </p>
          {publication.deletion_reason && (
            <p style={{ margin: '0 0 16px', fontStyle: 'italic', color: '#666' }}>
              Reason: {publication.deletion_reason}
            </p>
          )}
          <p style={{ margin: '16px 0 0', fontSize: 14, color: '#666' }}>
            <strong>Identifier:</strong>{' '}
            <a href={canonical} rel="canonical" style={{ color: '#0066cc' }}>
              {publication.document_docid || docid}
            </a>
          </p>
          {deletedAt && (
            <p style={{ margin: '4px 0 0', fontSize: 14, color: '#666' }}>
              <strong>Retired on:</strong> {deletedAt}
            </p>
          )}
        </div>
      </main>
    );
  }

  const authors = (publication.publication_creators || [])
    .map(formatAuthorName)
    .filter(Boolean);
  const date = formatHighwireDate(publication.published);
  const abstract = stripHtml(publication.abstract_text || publication.document_description);
  const pdfUrl = pickPdfUrl(publication);
  const allPdfs = listPdfs(publication); // for the supplementary list below
  const canonical = canonicalDocidUrl(publication.document_docid || docid);
  const jsonLd = buildJsonLd(publication);
  // Pre-serialize with Unicode-escape of <, >, &, U+2028, U+2029 so the value
  // is safe to inline inside <script type="application/ld+json">. See
  // safeJsonLd() in src/lib/highwire.js.
  const jsonLdSerialized = jsonLd ? safeJsonLd(jsonLd) : null;

  return (
    <>
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
            {publication.openalex_id && safeHref(publication.openalex_id) && (
              <li>
                OpenAlex:{' '}
                <a href={safeHref(publication.openalex_id)} rel="noopener" itemProp="sameAs">
                  {publication.openalex_id}
                </a>
              </li>
            )}
            {publication.handle_url && safeHref(publication.handle_url) && (
              <li>
                Handle:{' '}
                <a href={safeHref(publication.handle_url)} rel="noopener">
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

        {/* Crawlable anchors for every additional PDF. This lives inside the
            visually-hidden <article>, so it's not user-visible — its sole
            purpose is to give Googlebot a link path to supplementary
            materials. citation_pdf_url remains singular (canonical full
            text); these are extras. */}
        {allPdfs.length > 1 && (
          <section style={{ marginTop: 8 }}>
            <h2 style={{ fontSize: '1.1rem', margin: '12px 0 6px' }}>All PDFs</h2>
            <ul style={{ margin: 0, paddingLeft: '1.2em' }}>
              {allPdfs.map((f, i) => {
                const href = safeHref(f.file_url);
                if (!href) return null;
                return (
                  <li key={f.id ?? f.file_url ?? i}>
                    <a href={href} rel="noopener">
                      {f.title || f.file_name || `PDF ${i + 1}`}
                    </a>
                  </li>
                );
              })}
            </ul>
          </section>
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
