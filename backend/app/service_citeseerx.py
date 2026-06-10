"""
CiteSeerX OAI-PMH harvester (CS/legacy).
Thin config wrapper over service_oai_pmh.OAIPMHClient.

CAUTION: The CiteSeerX OAI-PMH endpoint at citeseerx.ist.psu.edu has been
unreliable since ~2022. Confirm the endpoint is alive before enabling:
  curl "https://citeseerx.ist.psu.edu/oai2?verb=Identify"
If the endpoint is dead, this module is a no-op (harvest() returns not_found).
Skip entirely unless DOCiD acquires a meaningful CS research user base —
heavy data overlap with Semantic Scholar makes this low-priority.
"""
from app.service_oai_pmh import OAIPMHClient, OAIPMHEnrichmentMapper, run_harvest

CITESEERX_ENDPOINT        = 'https://citeseerx.ist.psu.edu/oai2'
CITESEERX_METADATA_PREFIX = 'oai_dc'
CITESEERX_SET_SPEC        = None


def get_citeseerx_client() -> OAIPMHClient:
    return OAIPMHClient(
        endpoint=CITESEERX_ENDPOINT,
        metadata_prefix=CITESEERX_METADATA_PREFIX,
        set_spec=CITESEERX_SET_SPEC,
    )


def get_mapper() -> OAIPMHEnrichmentMapper:
    return OAIPMHEnrichmentMapper()


def harvest(db_session, page_limit: int = 0) -> dict:
    """Run an incremental CiteSeerX harvest; returns summary dict."""
    client = get_citeseerx_client()
    return run_harvest(client, db_session, page_limit=page_limit)
