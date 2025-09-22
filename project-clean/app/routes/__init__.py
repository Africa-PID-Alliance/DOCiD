# app/routes/__init__.py

# This file can be empty or contain package-level imports
from app.routes.auth import auth_bp
from app.routes.datacite import datacite_bp
from app.routes.docid import docid_bp
from app.routes.cordoi import cordoi_bp
from app.routes.crossref import crossref_bp
from app.routes.ror import ror_bp
from app.routes.raid import raid_bp
from app.routes.orcid import orcid_bp
from app.routes.publications import publications_bp
from app.routes.arks  import arks_bp
from app.routes.smtp  import smtp_bp
from app.routes.uploads import uploads_bp
from app.routes.doi import doi_bp
