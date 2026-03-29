# Crawling and indexing workflows

## Full crawl / recrawl

1. In **Admin → Crawl**, select a **crawl configuration** (defines base URL, allowed hosts, depth, PDF policy, etc.).
2. Start **Full recrawl** (or sync jobs depending on product naming in UI). This creates a **CrawlJob** of type `full_recrawl` (or `sync_changed` for refresh-all-active-sources).
3. The **worker** runs the crawl engine: BFS from the seed URL, normalizes URLs, deduplicates by canonical URL, obeys `max_depth` / `max_pages`, optional robots.txt.
4. For each fetched HTML page: **extract** text, snapshot, **extract** hash; if bytes changed, re-index. For PDFs: fetch binary, extract text with page markers.
5. **Indexing** chunks the text, requests **embeddings** from OpenAI, writes `document_chunks` (replacing prior chunks for that extraction snapshot when content changed).

## Single page update (HTML)

**Intent:** Refresh one HTML URL without a full site crawl.

1. **Admin → Crawl** (or incremental API): **Refresh page** with the full URL and a crawl config id.
2. Backend queues `CrawlJob` with `job_type=incremental_url` and `workflow=refresh_page` (seed URL = that page).
3. Worker fetches **one** URL (and may follow policy for discovery-only links depending on implementation), extracts, updates the source row, then indexes if the extraction hash changed.

## Single PDF update

**Intent:** Re-fetch and re-index one PDF URL.

1. Use **Refresh PDF** (not “Refresh page”) with the `.pdf` URL (or `Content-Type: application/pdf`).
2. Backend queues `incremental_pdf` / `workflow=refresh_pdf`.
3. Worker downloads the PDF, re-runs PDF extraction, then indexing **skips embedding** if `extraction_hash` is unchanged (same bytes).

## Adding a new source

**Intent:** Add a **single** URL as a crawlable source without crawling the whole site first.

1. **Add source** (incremental UI) with the full URL and crawl config.
2. Job type `add_source`: fetches that URL and registers linked URLs as **discovered** (or per product rules) for later crawls.
3. Use **full recrawl** or **single-page** incremental updates to materialize and index additional pages as needed.

## Indexing and “unchanged hash” skip

- Each extracted document has an **`extraction_hash`** (content fingerprint).
- **Indexing** compares `indexed_extraction_hash` to `extraction_hash`. If equal and `force` is false, the indexer **skips** re-embedding (idempotent no-op).
- **Force** re-index (admin or API) recomputes embeddings even when the hash matches.

## Operational dependencies

- **OpenAI API key** must be set for embeddings and chat; worker **must** run for background jobs.
- Celery **worker** and **Redis** must be up for any crawl/index job to leave `queued` state.
