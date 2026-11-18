import { NextResponse } from 'next/server';

/**
 * GET /api/publications/publication-type-counts
 *
 * Counts publications (publications_files) per publication type across ALL DOCiDs,
 * using only the existing upstream API endpoints:
 *   - /publications/get-publications          -> list every DOCiD id (paged)
 *   - /publications/get-publication/{id}      -> each DOCiD's publications_files[].publication_type_id
 *
 * There is no aggregate endpoint upstream, so the full scan is slow (~1-2 min for ~3.7k DOCiDs).
 * The result is cached in server memory and refreshed in the background.
 * While the first scan runs, the route returns { status: 'computing', progress } and the
 * client polls. Add ?refresh=1 to force a new scan.
 */

const CACHE_TTL_MS = 30 * 60 * 1000; // serve cached counts for 30 minutes
const LIST_PAGE_SIZE = 100;
const CONCURRENCY = 15;

// Survives hot reloads in dev
const state = globalThis.__docidPubTypeCounts || (globalThis.__docidPubTypeCounts = {
  result: null,      // { counts, total, docids_scanned, failed, computed_at }
  computing: null,   // Promise while a scan is running
  progress: { done: 0, total: 0 },
});

async function getJson(url) {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, cache: 'no-store' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${url}`);
  return res.json();
}

async function listAllPublicationIds(baseUrl) {
  const first = await getJson(`${baseUrl}/publications/get-publications?page=1&page_size=${LIST_PAGE_SIZE}`);
  const ids = (first.data || []).map((p) => p.id);
  const totalPages = first.pagination?.total_pages || 1;
  state.progress.total = first.pagination?.total || ids.length;

  const pages = [];
  for (let p = 2; p <= totalPages; p++) pages.push(p);
  await runPool(pages, 5, async (p) => {
    const data = await getJson(`${baseUrl}/publications/get-publications?page=${p}&page_size=${LIST_PAGE_SIZE}`);
    (data.data || []).forEach((pub) => ids.push(pub.id));
  });
  return [...new Set(ids)];
}

async function runPool(items, limit, worker) {
  let i = 0;
  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (i < items.length) {
      const item = items[i++];
      await worker(item);
    }
  });
  await Promise.all(runners);
}

async function computeCounts() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  state.progress = { done: 0, total: 0 };

  const ids = await listAllPublicationIds(baseUrl);
  state.progress.total = ids.length;

  const counts = {};
  let total = 0;
  let failed = 0;

  await runPool(ids, CONCURRENCY, async (id) => {
    try {
      const pub = await getJson(`${baseUrl}/publications/get-publication/${id}`);
      (pub.publications_files || []).forEach((file) => {
        const typeId = file.publication_type_id;
        if (typeId === null || typeId === undefined) return;
        counts[String(typeId)] = (counts[String(typeId)] || 0) + 1;
        total += 1;
      });
    } catch (e) {
      failed += 1;
    } finally {
      state.progress.done += 1;
    }
  });

  state.result = {
    counts,
    total,
    docids_scanned: ids.length,
    failed,
    computed_at: new Date().toISOString(),
  };
  return state.result;
}

function startScan() {
  if (!state.computing) {
    state.computing = computeCounts()
      .catch((e) => console.error('publication-type-counts scan failed:', e))
      .finally(() => { state.computing = null; });
  }
  return state.computing;
}

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const forceRefresh = searchParams.get('refresh') === '1';

  const isFresh = state.result && Date.now() - new Date(state.result.computed_at).getTime() < CACHE_TTL_MS;

  if (forceRefresh || !isFresh) startScan();

  if (state.result) {
    // Serve cached (possibly slightly stale while a background refresh runs)
    return NextResponse.json({ status: 'ready', refreshing: !!state.computing, ...state.result });
  }

  return NextResponse.json(
    { status: 'computing', progress: state.progress },
    { status: 202 }
  );
}
