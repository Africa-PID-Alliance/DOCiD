"""
ScienceOpen BookMetaHub OAI-PMH harvester.
Thin config wrapper over service_oai_pmh.OAIPMHClient.
Endpoint: https://www.scienceopen.com/oai  (BookMetaHub public OAI-PMH feed)
NOTE: verify endpoint URL against https://about.scienceopen.com/bookmetahub-open-api/
      before first production run — provider may change it without notice.
"""
from app.service_oai_pmh import OAIPMHClient, OAIPMHEnrichmentMapper, run_harvest

SCIENCEOPEN_ENDPOINT      = 'https://www.scienceopen.com/oai'
SCIENCEOPEN_METADATA_PREFIX = 'oai_dc'
SCIENCEOPEN_SET_SPEC      = None  # adjust to a books-specific set if provider offers one


def get_scienceopen_client() -> OAIPMHClient:
    return OAIPMHClient(
        endpoint=SCIENCEOPEN_ENDPOINT,
        metadata_prefix=SCIENCEOPEN_METADATA_PREFIX,
        set_spec=SCIENCEOPEN_SET_SPEC,
    )


def get_mapper() -> OAIPMHEnrichmentMapper:
    return OAIPMHEnrichmentMapper()


def harvest(db_session, page_limit: int = 0) -> dict:
    """Run an incremental ScienceOpen harvest; returns summary dict."""
    client = get_scienceopen_client()
    return run_harvest(client, db_session, page_limit=page_limit)
