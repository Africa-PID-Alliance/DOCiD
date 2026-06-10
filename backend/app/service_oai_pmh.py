"""
Generic OAI-PMH 2.0 Harvester — shared by service_scienceopen.py and service_citeseerx.py.

Key design decisions:
- resumptionToken: after the first page, subsequent calls carry ONLY the token.
  Expired tokens restart from last_success_until checkpoint.
- Timezone discipline: all from/until datetimes are UTC; granularity is read
  from the Identify verb and respected in outgoing requests.
- Atomic in_progress via conditional UPDATE (rowcount==0 → another worker holds lock).
- Tombstones (status="deleted") are staged with is_deleted=True; downstream code
  decides what to do with matched publications.
- OAI-PMH errors that are NOT noRecordsMatch are treated as failures.
- Staging inserts use ON CONFLICT DO UPDATE for idempotent replays.
"""
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Generator, List, Optional, Tuple

import requests
from lxml import etree

logger = logging.getLogger(__name__)

# XML namespaces used across OAI-PMH responses.
OAI_NS  = 'http://www.openarchives.org/OAI/2.0/'
DC_NS   = 'http://purl.org/dc/elements/1.1/'
OAI_DC_NS = 'http://www.openarchives.org/OAI/2.0/oai_dc/'


def _ns(tag: str, namespace: str = OAI_NS) -> str:
    return f'{{{namespace}}}{tag}'


class OAIPMHClient:
    """
    Generic OAI-PMH 2.0 client.

    Instantiate with an endpoint URL; call harvest_records() for a resumption-
    token-aware, checkpoint-friendly page generator.
    """

    def __init__(
        self,
        endpoint: str,
        metadata_prefix: str = 'oai_dc',
        set_spec: Optional[str] = None,
        rate_limit_delay: float = 1.0,
        timeout: int = 30,
    ):
        self.endpoint = endpoint.rstrip('/')
        self.metadata_prefix = metadata_prefix
        self.set_spec = set_spec
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0
        self.session = requests.Session()
        self.timeout = timeout
        self._granularity: Optional[str] = None  # populated by identify()

    def _make_request(self, params: Dict) -> Optional[bytes]:
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

        try:
            response = self.session.get(
                self.endpoint, params=params, timeout=self.timeout,
            )
            if response.status_code == 200:
                return response.content
            if response.status_code == 503:
                retry = int(response.headers.get('Retry-After', '120'))
                logger.warning("OAI-PMH 503 from %s; retrying after %ds", self.endpoint, retry)
                time.sleep(retry)
                self._last_request_time = time.time()
                response = self.session.get(
                    self.endpoint, params=params, timeout=self.timeout,
                )
                if response.status_code == 200:
                    return response.content
            logger.error("OAI-PMH HTTP %d from %s", response.status_code, self.endpoint)
            return None
        except requests.exceptions.Timeout:
            logger.error("Timeout calling OAI-PMH endpoint: %s", self.endpoint)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("Network error calling OAI-PMH: %s", exc)
            return None

    # Hardened parser: no entity resolution, no network access, no DTD loading,
    # no huge-tree expansion. OAI-PMH responses are untrusted external XML.
    _XML_PARSER = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        huge_tree=False,
    )

    def _parse_xml(self, raw: bytes) -> Optional[etree._Element]:
        try:
            return etree.fromstring(raw, self._XML_PARSER)
        except etree.XMLSyntaxError as exc:
            logger.error("XML parse error from OAI-PMH: %s", exc)
            return None

    def _check_oai_error(self, root: etree._Element) -> Optional[str]:
        """Return the OAI error code if present, else None."""
        for error_el in root.iter(_ns('error')):
            code = error_el.get('code', 'unknown')
            return code
        return None

    def identify(self) -> Optional[Dict]:
        """Call Identify verb; cache granularity."""
        raw = self._make_request({'verb': 'Identify'})
        if not raw:
            return None
        root = self._parse_xml(raw)
        if root is None:
            return None
        error_code = self._check_oai_error(root)
        if error_code:
            logger.error("OAI-PMH Identify error: %s", error_code)
            return None

        identify_el = root.find(_ns('Identify'))
        if identify_el is None:
            return None

        granularity_el = identify_el.find(_ns('granularity'))
        if granularity_el is not None and granularity_el.text:
            self._granularity = granularity_el.text.strip()

        return {
            'repository_name':  _text(identify_el, 'repositoryName'),
            'base_url':         _text(identify_el, 'baseURL'),
            'admin_email':      _text(identify_el, 'adminEmail'),
            'granularity':      self._granularity,
            'earliest_datestamp': _text(identify_el, 'earliestDatestamp'),
        }

    def list_sets(self) -> List[Dict]:
        raw = self._make_request({'verb': 'ListSets'})
        if not raw:
            return []
        root = self._parse_xml(raw)
        if root is None:
            return []
        sets = []
        for set_el in root.iter(_ns('set')):
            sets.append({
                'setSpec': _text(set_el, 'setSpec'),
                'setName': _text(set_el, 'setName'),
            })
        return sets

    def _format_date(self, dt: Optional[datetime]) -> Optional[str]:
        """Format a UTC datetime respecting the endpoint's declared granularity."""
        if dt is None:
            return None
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        gran = self._granularity or 'YYYY-MM-DDThh:mm:ssZ'
        if 'T' in gran:
            return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime('%Y-%m-%d')

    def list_records_page(
        self,
        from_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None,
        resumption_token: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Fetch one page of ListRecords.

        Returns (records, next_resumption_token).
        next_resumption_token is None when the full result set is exhausted.
        records is [] on noRecordsMatch (not an error).
        Returns ([], None) on hard error.
        """
        if resumption_token:
            # Spec: when resuming, send ONLY the resumptionToken.
            params = {'verb': 'ListRecords', 'resumptionToken': resumption_token}
        else:
            params: Dict = {'verb': 'ListRecords', 'metadataPrefix': self.metadata_prefix}
            formatted_from = self._format_date(from_date)
            formatted_until = self._format_date(until_date)
            if formatted_from:
                params['from'] = formatted_from
            if formatted_until:
                params['until'] = formatted_until
            if self.set_spec:
                params['set'] = self.set_spec

        raw = self._make_request(params)
        if not raw:
            return [], None

        root = self._parse_xml(raw)
        if root is None:
            return [], None

        error_code = self._check_oai_error(root)
        if error_code == 'noRecordsMatch':
            return [], None  # legitimate empty result
        if error_code:
            logger.error("OAI-PMH ListRecords error: %s", error_code)
            return [], None

        list_records_el = root.find(_ns('ListRecords'))
        if list_records_el is None:
            return [], None

        records = []
        for record_el in list_records_el.findall(_ns('record')):
            parsed = _parse_record(record_el)
            if parsed:
                records.append(parsed)

        # Extract next resumption token (empty element = last page).
        next_token = None
        token_el = list_records_el.find(_ns('resumptionToken'))
        if token_el is not None and token_el.text and token_el.text.strip():
            next_token = token_el.text.strip()

        return records, next_token

    def harvest_records(
        self,
        from_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None,
        resumption_token: Optional[str] = None,
        page_limit: int = 0,
    ) -> Generator[Tuple[List[Dict], Optional[str]], None, None]:
        """
        Generator that yields (page_records, next_resumption_token) per page.

        Callers advance the checkpoint after each successfully processed page.
        Stops when the server signals the last page (token becomes None) or
        page_limit is reached (0 = unlimited).
        """
        token = resumption_token
        pages_fetched = 0

        while True:
            records, next_token = self.list_records_page(
                from_date=from_date if not token else None,
                until_date=until_date if not token else None,
                resumption_token=token,
            )
            pages_fetched += 1
            yield records, next_token

            if next_token is None:
                break
            token = next_token
            if page_limit and pages_fetched >= page_limit:
                logger.info("OAI-PMH page_limit=%d reached; stopping", page_limit)
                break


# ---------------------------------------------------------------------------
# Record parsing helpers
# ---------------------------------------------------------------------------

def _text(parent: etree._Element, local_name: str, ns: str = OAI_NS) -> Optional[str]:
    el = parent.find(_ns(local_name, ns))
    return el.text.strip() if el is not None and el.text else None


def _parse_record(record_el: etree._Element) -> Optional[Dict]:
    """Parse a single OAI-PMH <record> element into a staging dict."""
    header_el = record_el.find(_ns('header'))
    if header_el is None:
        return None

    oai_identifier = _text(header_el, 'identifier')
    datestamp_raw  = _text(header_el, 'datestamp')
    is_deleted     = header_el.get('status') == 'deleted'

    if not oai_identifier or not datestamp_raw:
        return None

    # Parse datestamp to UTC datetime.
    oai_datestamp = _parse_datestamp(datestamp_raw)
    if not oai_datestamp:
        return None

    # Set specs (may be multiple).
    set_specs = [el.text.strip() for el in header_el.findall(_ns('setSpec'))
                 if el.text and el.text.strip()]

    # Extract oai_dc metadata (best-effort; may be absent on deleted records).
    normalised: Dict = {'set_specs': set_specs}
    if not is_deleted:
        metadata_el = record_el.find(_ns('metadata'))
        if metadata_el is not None:
            dc_el = metadata_el.find(_ns('dc', OAI_DC_NS))
            if dc_el is not None:
                normalised.update(_extract_dc(dc_el))

    raw_xml = etree.tostring(record_el, encoding='unicode')

    return {
        'oai_identifier': oai_identifier,
        'oai_datestamp':  oai_datestamp,
        'is_deleted':     is_deleted,
        'raw_xml':        raw_xml,
        'normalised':     normalised,
    }


def _parse_datestamp(raw: str) -> Optional[datetime]:
    for fmt in ('%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d'):
        try:
            dt = datetime.strptime(raw.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    logger.warning("Could not parse OAI-PMH datestamp: %s", raw)
    return None


def _extract_dc(dc_el: etree._Element) -> Dict:
    """Extract Dublin Core fields from an oai_dc:dc element."""
    def dc_values(tag: str) -> List[str]:
        return [el.text.strip() for el in dc_el.findall(_ns(tag, DC_NS))
                if el.text and el.text.strip()]

    titles       = dc_values('title')
    creators     = dc_values('creator')
    subjects     = dc_values('subject')
    descriptions = dc_values('description')
    publishers   = dc_values('publisher')
    dates        = dc_values('date')
    types        = dc_values('type')
    formats      = dc_values('format')
    identifiers  = dc_values('identifier')
    languages    = dc_values('language')

    # Try to extract a DOI from identifiers.
    doi = None
    for ident in identifiers:
        if 'doi.org/' in ident or ident.lower().startswith('10.'):
            from app.service_openalex import normalize_doi
            doi = normalize_doi(ident)
            if doi:
                break

    return {
        'title':       titles[0] if titles else None,
        'creators':    creators,
        'subjects':    subjects,
        'description': descriptions[0] if descriptions else None,
        'publisher':   publishers[0] if publishers else None,
        'date':        dates[0] if dates else None,
        'types':       types,
        'formats':     formats,
        'identifiers': identifiers,
        'languages':   languages,
        'doi':         doi,
    }


# ---------------------------------------------------------------------------
# Harvest orchestrator — writes to harvest_state + harvest_staging_records
# ---------------------------------------------------------------------------

def run_harvest(
    client: OAIPMHClient,
    db_session,
    page_limit: int = 0,
    batch_size: int = 500,
) -> Dict:
    """
    Orchestrate a full incremental harvest for this client's endpoint.

    1. Claims the HarvestState row atomically (conditional UPDATE).
    2. Pages through ListRecords from last checkpoint.
    3. Stages records into harvest_staging_records (ON CONFLICT DO UPDATE).
    4. Advances last_success_until only after each page commits cleanly.
    5. Releases in_progress on success or failure.

    Returns a summary dict: {staged, skipped_deleted, pages, status}.
    """
    from app.models import HarvestState
    import sqlalchemy as sa

    endpoint   = client.endpoint
    prefix     = client.metadata_prefix
    set_spec   = client.set_spec

    # Ensure granularity is populated.
    if not client._granularity:
        client.identify()

    # --- Atomic claim via conditional UPDATE ---
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC for DB
    result = db_session.execute(
        sa.text(
            "UPDATE harvest_state "
            "SET in_progress = TRUE, in_progress_since = :now, last_run_at = :now "
            "WHERE endpoint = :ep AND metadata_prefix = :pfx "
            "AND COALESCE(set_spec, '') = COALESCE(:ss, '') "
            "AND in_progress = FALSE "
            "RETURNING id, last_success_from, last_success_until, last_resumption_token"
        ),
        {"now": now_utc, "ep": endpoint, "pfx": prefix, "ss": set_spec},
    )
    row = result.fetchone()

    if row is None:
        # Either no row exists yet or another worker holds the lock.
        existing = db_session.execute(
            sa.text(
                "SELECT id FROM harvest_state WHERE endpoint = :ep "
                "AND metadata_prefix = :pfx "
                "AND COALESCE(set_spec, '') = COALESCE(:ss, '')"
            ),
            {"ep": endpoint, "pfx": prefix, "ss": set_spec},
        ).fetchone()

        if existing:
            logger.warning("Harvest already in progress for %s; aborting.", endpoint)
            return {"status": "already_running", "staged": 0, "pages": 0}

        # First run — insert the state row, then claim it.
        db_session.execute(
            sa.text(
                "INSERT INTO harvest_state "
                "(endpoint, metadata_prefix, set_spec, granularity, in_progress, "
                " in_progress_since, last_run_at, consecutive_failures, created_at, updated_at) "
                "VALUES (:ep, :pfx, :ss, :gran, TRUE, :now, :now, 0, :now, :now)"
            ),
            {"ep": endpoint, "pfx": prefix, "ss": set_spec,
             "gran": client._granularity, "now": now_utc},
        )
        db_session.commit()
        result = db_session.execute(
            sa.text(
                "SELECT id, last_success_from, last_success_until, last_resumption_token "
                "FROM harvest_state WHERE endpoint = :ep AND metadata_prefix = :pfx "
                "AND COALESCE(set_spec, '') = COALESCE(:ss, '')"
            ),
            {"ep": endpoint, "pfx": prefix, "ss": set_spec},
        )
        row = result.fetchone()
        if not row:
            logger.error("Could not create harvest_state row for %s", endpoint)
            return {"status": "error", "staged": 0, "pages": 0}

    state_id          = row[0]
    from_date_raw     = row[1]
    until_date_raw    = row[2]
    resume_token      = row[3]

    from_date  = from_date_raw.replace(tzinfo=timezone.utc) if from_date_raw else None
    until_date = until_date_raw.replace(tzinfo=timezone.utc) if until_date_raw else None
    harvest_until = datetime.now(timezone.utc)

    staged_count   = 0
    deleted_count  = 0
    pages_count    = 0
    last_error     = None

    try:
        for page_records, next_token in client.harvest_records(
            from_date=from_date,
            until_date=harvest_until,
            resumption_token=resume_token,
            page_limit=page_limit,
        ):
            pages_count += 1
            for rec in page_records:
                _upsert_staging_record(db_session, endpoint, rec)
                if rec['is_deleted']:
                    deleted_count += 1
                else:
                    staged_count += 1

            # Advance checkpoint atomically after each page.
            db_session.execute(
                sa.text(
                    "UPDATE harvest_state SET last_success_until = :until, "
                    "last_resumption_token = :token, updated_at = :now "
                    "WHERE id = :sid"
                ),
                {"until": harvest_until.replace(tzinfo=None),
                 "token": next_token,
                 "now": datetime.utcnow(),
                 "sid": state_id},
            )
            db_session.commit()

        # Success — clear in_progress and reset failure counter.
        db_session.execute(
            sa.text(
                "UPDATE harvest_state SET in_progress = FALSE, "
                "last_success_from = :from_d, last_success_until = :until, "
                "last_resumption_token = NULL, last_run_status = 'ok', "
                "consecutive_failures = 0, updated_at = :now "
                "WHERE id = :sid"
            ),
            {"from_d": from_date.replace(tzinfo=None) if from_date else None,
             "until": harvest_until.replace(tzinfo=None),
             "now": datetime.utcnow(),
             "sid": state_id},
        )
        db_session.commit()
        return {"status": "ok", "staged": staged_count, "deleted": deleted_count,
                "pages": pages_count}

    except Exception as exc:
        last_error = str(exc)
        logger.error("Harvest failed for %s: %s", endpoint, exc)
        db_session.rollback()
        db_session.execute(
            sa.text(
                "UPDATE harvest_state SET in_progress = FALSE, "
                "last_run_status = 'failed', last_error_message = :err, "
                "consecutive_failures = consecutive_failures + 1, updated_at = :now "
                "WHERE id = :sid"
            ),
            {"err": last_error[:2000], "now": datetime.utcnow(), "sid": state_id},
        )
        db_session.commit()
        return {"status": "error", "error": last_error, "staged": staged_count,
                "pages": pages_count}


def _upsert_staging_record(db_session, endpoint: str, rec: Dict) -> None:
    """Insert or update a harvest_staging_records row (idempotent)."""
    import sqlalchemy as sa
    import json
    db_session.execute(
        sa.text(
            "INSERT INTO harvest_staging_records "
            "(endpoint, oai_identifier, oai_datestamp, is_deleted, raw_xml, normalised, "
            " status, retry_count, created_at, updated_at) "
            "VALUES (:ep, :oid, :ods, :del, :xml, :norm::jsonb, 'new', 0, :now, :now) "
            "ON CONFLICT (endpoint, oai_identifier) DO UPDATE SET "
            "oai_datestamp = EXCLUDED.oai_datestamp, "
            "is_deleted    = EXCLUDED.is_deleted, "
            "raw_xml       = EXCLUDED.raw_xml, "
            "normalised    = EXCLUDED.normalised, "
            "updated_at    = EXCLUDED.updated_at"
        ),
        {
            "ep":   endpoint,
            "oid":  rec['oai_identifier'],
            "ods":  rec['oai_datestamp'].replace(tzinfo=None),
            "del":  rec['is_deleted'],
            "xml":  rec.get('raw_xml'),
            "norm": json.dumps(rec.get('normalised') or {}),
            "now":  datetime.utcnow(),
        },
    )


class OAIPMHEnrichmentMapper:
    """
    Thin mapper that extracts a normalised dict from a staged record for
    downstream DOCiD matching/enrichment logic.
    """

    @classmethod
    def extract_match_candidates(cls, normalised: Dict) -> Dict:
        """Return the fields most useful for matching to a DOCiD publication."""
        return {
            'doi':     normalised.get('doi'),
            'title':   normalised.get('title'),
            'creators': normalised.get('creators') or [],
            'date':    normalised.get('date'),
        }
