"""
Provider registry for DOCiD external enrichment services.
Maps source_name -> module + status. Routes and CLI call get_service() instead
of importing provider modules directly so deferred providers return clean 501s.
"""
import importlib
import logging
from flask import current_app

logger = logging.getLogger(__name__)

# Canonical registry. status values: 'available' | 'not_implemented'
REGISTRY = {
    'openalex':         {'module': 'app.service_openalex',         'status': 'available'},
    'unpaywall':        {'module': 'app.service_unpaywall',        'status': 'available'},
    'semantic_scholar': {'module': 'app.service_semantic_scholar', 'status': 'available'},
    'core':             {'module': 'app.service_core',             'status': 'available'},
    'openaire':         {'module': 'app.service_openaire',         'status': 'available'},
    'opencitations':    {'module': 'app.service_opencitations',    'status': 'available'},
    'lens_org':         {'module': 'app.service_lens',             'status': 'not_implemented',
                         'reason': 'Lens.org API keys not yet acquired; see meeting-notes/lens-org/NOTES.md'},
    'base':             {'module': None,                           'status': 'not_implemented',
                         'reason': 'BASE API key not yet acquired; see meeting-notes/base/NOTES.md'},
    'worldcat':         {'module': None,                           'status': 'not_implemented',
                         'reason': 'OCLC contract pending; see meeting-notes/worldcat/NOTES.md'},
    'scienceopen':      {'module': 'app.service_scienceopen',      'status': 'not_implemented',
                         'reason': 'OAI-PMH harvester not yet built (Wave 3)'},
    'citeseerx':        {'module': 'app.service_citeseerx',        'status': 'not_implemented',
                         'reason': 'OAI-PMH harvester not yet built (Wave 3)'},
}


class ProviderNotImplementedError(Exception):
    """Raised when a route requests a provider that has no service module yet."""
    pass


def get_service(source_name: str):
    """Return the imported service module for source_name, or raise."""
    entry = REGISTRY.get(source_name)
    if entry is None:
        raise KeyError(f"Unknown enrichment provider: {source_name!r}")
    if entry['status'] == 'not_implemented':
        raise ProviderNotImplementedError(entry.get('reason', source_name))
    return importlib.import_module(entry['module'])


def enrichment_enabled(source_name: str) -> bool:
    """
    Return True if source_name is in ENRICHMENT_SOURCES config and its
    kill switch is not set. Use this in routes before calling get_service().
    """
    try:
        sources = current_app.config.get('ENRICHMENT_SOURCES', [])
        kill_switch_key = f"{source_name.upper()}_KILL_SWITCH"
        kill_switch = current_app.config.get(kill_switch_key, False)
        return source_name in sources and not kill_switch
    except RuntimeError:
        # Outside app context (e.g. tests) — default to enabled
        return True


def list_available_providers() -> list:
    """Return names of all providers with status='available'."""
    return [name for name, entry in REGISTRY.items() if entry['status'] == 'available']
