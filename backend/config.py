import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    CROSSREF_API_URL = os.getenv('CROSSREF_API_URL')
    CROSSREF_API_KEY = os.getenv('CROSSREF_API_KEY')

    # CrossRef DEPOSIT config (separate from the read-API above).
    # Default points at the CrossRef TEST server so a misconfigured prod can't
    # accidentally mint real DOIs. Flip CROSSREF_DEPOSIT_URL to
    # https://doi.crossref.org/servlet/deposit only after a real member account
    # is provisioned and CROSSREF_DOI_PREFIX is set.
    CROSSREF_DEPOSIT_URL = os.getenv(
        'CROSSREF_DEPOSIT_URL', 'https://test.crossref.org/servlet/deposit'
    )
    CROSSREF_DEPOSIT_LOGIN = os.getenv('CROSSREF_DEPOSIT_LOGIN')
    CROSSREF_DEPOSIT_PASSWORD = os.getenv('CROSSREF_DEPOSIT_PASSWORD')
    CROSSREF_DEPOSITOR_NAME = os.getenv('CROSSREF_DEPOSITOR_NAME', 'Africa PID Alliance')
    CROSSREF_DEPOSITOR_EMAIL = os.getenv('CROSSREF_DEPOSITOR_EMAIL', 'info@africapidalliance.org')
    # No default: missing CROSSREF_DOI_PREFIX makes build_crossref_xml_for_publication
    # return skipped/'missing_prefix' so the system never tries to deposit DOIs we
    # don't own.
    CROSSREF_DOI_PREFIX = os.getenv('CROSSREF_DOI_PREFIX')
    CROSSREF_DEPOSIT_ENABLED = os.getenv('CROSSREF_DEPOSIT_ENABLED', 'false').lower() == 'true'
    # Submission-status download URL (CrossRef polls). For test server it's
    # https://test.crossref.org/servlet/submissionDownload; for prod
    # https://doi.crossref.org/servlet/submissionDownload.
    CROSSREF_SUBMISSION_DOWNLOAD_URL = os.getenv(
        'CROSSREF_SUBMISSION_DOWNLOAD_URL',
        'https://test.crossref.org/servlet/submissionDownload',
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    LC_API_KEY = os.getenv('LC_API_KEY')
    LOCAL_CONTEXTS_API_BASE_URL = os.getenv('LOCAL_CONTEXTS_API_BASE_URL')
    CSTR_CLIENT_ID = os.getenv('CSTR_CLIENT_ID')
    CSTR_SECRET = os.getenv('CSTR_SECRET')
    CSTR_PREFIX = os.getenv('CSTR_PREFIX')
    CSTR_USERNAME = os.getenv('CSTR_USERNAME')
    APPLICATION_BASE_URL = os.getenv('APPLICATION_BASE_URL', 'http://localhost:3000')
    # UPLOADS_BASE_URL controls where stored /uploads/... URLs resolve at read time.
    # Defaults to APPLICATION_BASE_URL so single-host deployments need no config.
    # Override on the dockerized host where the public domain differs from the
    # host that physically holds the upload files (e.g. set to
    # https://docid-core.africapidalliance.org so docker responses point at KENET).
    UPLOADS_BASE_URL = os.getenv('UPLOADS_BASE_URL') or APPLICATION_BASE_URL
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    _raw_uploads_directory = os.getenv('UPLOADS_DIRECTORY', 'uploads')
    UPLOADS_DIRECTORY = (
        _raw_uploads_directory
        if os.path.isabs(_raw_uploads_directory)
        else os.path.abspath(os.path.join(BASE_DIR, _raw_uploads_directory))
    )

    # SciCrunch Configuration
    SCICRUNCH_API_KEY = os.getenv('SCICRUNCH_API_KEY')

    # CORDRA Configuration
    CORDRA_BASE_URL = os.getenv('CORDRA_BASE_URL', 'https://cordra.kenet.or.ke/cordra')
    CORDRA_USERNAME = os.getenv('CORDRA_USERNAME')
    CORDRA_PASSWORD = os.getenv('CORDRA_PASSWORD')

    # RAID Configuration
    RAID_API_URL = os.getenv('RAID_API_URL', 'https://api.demo.raid.org.au/raid/')
    RAID_TOKEN_URL = os.getenv('RAID_TOKEN_URL', 'https://iam.demo.raid.org.au/realms/raid/protocol/openid-connect/token')
    RAID_GRANT_TYPE = os.getenv('RAID_GRANT_TYPE', 'password')
    RAID_CLIENT_ID = os.getenv('RAID_CLIENT_ID')
    RAID_CLIENT_SECRET = os.getenv('RAID_CLIENT_SECRET')
    RAID_USERNAME = os.getenv('RAID_USERNAME')
    RAID_PASSWORD = os.getenv('RAID_PASSWORD')

    # Metadata Enrichment Configuration
    OPENALEX_CONTACT_EMAIL = os.getenv('OPENALEX_CONTACT_EMAIL', 'admin@docid.africapidalliance.org')
    UNPAYWALL_CONTACT_EMAIL = os.getenv('UNPAYWALL_CONTACT_EMAIL', 'admin@docid.africapidalliance.org')
    SEMANTIC_SCHOLAR_API_KEY = os.getenv('SEMANTIC_SCHOLAR_API_KEY', '')
    CORE_API_KEY = os.getenv('CORE_API_KEY', '')
    CORE_API_BASE_URL = os.getenv('CORE_API_BASE_URL', 'https://api.core.ac.uk/v3')
    OPENAIRE_API_BASE_URL = os.getenv('OPENAIRE_API_BASE_URL', 'https://graph.openaire.eu/api')
    OPENCITATIONS_ACCESS_TOKEN = os.getenv('OPENCITATIONS_ACCESS_TOKEN', '')
    LENS_SCHOLAR_API_KEY = os.getenv('LENS_SCHOLAR_API_KEY', '')
    LENS_PATENT_API_KEY = os.getenv('LENS_PATENT_API_KEY', '')
    LENS_API_BASE_URL = os.getenv('LENS_API_BASE_URL', 'https://api.lens.org')
    BASE_API_KEY = os.getenv('BASE_API_KEY', '')
    BASE_API_BASE_URL = os.getenv('BASE_API_BASE_URL', 'https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi')
    WORLDCAT_CLIENT_ID = os.getenv('WORLDCAT_CLIENT_ID', '')
    WORLDCAT_CLIENT_SECRET = os.getenv('WORLDCAT_CLIENT_SECRET', '')
    WORLDCAT_SEARCH_BASE_URL = os.getenv('WORLDCAT_SEARCH_BASE_URL', 'https://americas.discovery.api.oclc.org/worldcat/search/v2')
    WORLDCAT_METADATA_BASE_URL = os.getenv('WORLDCAT_METADATA_BASE_URL', 'https://metadata.api.oclc.org')

    # Canonical list of active enrichment providers.
    # Routes and CLI both read from this list — no per-provider boolean flags needed.
    # Override via ENRICHMENT_SOURCES env var (comma-separated) to add/remove providers.
    ENRICHMENT_SOURCES = [
        s.strip()
        for s in os.getenv('ENRICHMENT_SOURCES', 'openalex,unpaywall').split(',')
        if s.strip()
    ]

    # Per-provider emergency kill switches (take precedence over ENRICHMENT_SOURCES).
    # Set <PROVIDER>_KILL_SWITCH=true to block a provider even if it is in ENRICHMENT_SOURCES.
    OPENALEX_KILL_SWITCH = os.getenv('OPENALEX_KILL_SWITCH', 'false').lower() == 'true'
    SEMANTIC_SCHOLAR_KILL_SWITCH = os.getenv('SEMANTIC_SCHOLAR_KILL_SWITCH', 'false').lower() == 'true'
    CORE_KILL_SWITCH = os.getenv('CORE_KILL_SWITCH', 'false').lower() == 'true'
    OPENAIRE_KILL_SWITCH = os.getenv('OPENAIRE_KILL_SWITCH', 'false').lower() == 'true'
    OPENCITATIONS_KILL_SWITCH = os.getenv('OPENCITATIONS_KILL_SWITCH', 'false').lower() == 'true'
    LENS_ORG_KILL_SWITCH = os.getenv('LENS_ORG_KILL_SWITCH', 'false').lower() == 'true'
    BASE_KILL_SWITCH = os.getenv('BASE_KILL_SWITCH', 'false').lower() == 'true'
    WORLDCAT_KILL_SWITCH = os.getenv('WORLDCAT_KILL_SWITCH', 'false').lower() == 'true'

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours in seconds (default)
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))  # 30 days in seconds (default)
 