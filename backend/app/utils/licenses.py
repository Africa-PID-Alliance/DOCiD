"""
Licences on publication files.

Only a publication file (a work uploaded in the assign form) carries a licence:
a row in the ``licenses`` reference table. It is optional: the depositor may
choose one (never preselected) or leave the file unlicensed. A DOCiD and its
publication documents have none.

Whoever sets a file's licence must confirm they hold the rights
(``rightsDeclaration`` / ``rights_declaration`` = true). Each confirmation is
one ``PublicationAuditTrail`` row with action ``RIGHTS_DECLARED``.
"""

import json
import re

from app import db
from app.models import Licenses

RIGHTS_DECLARATION_VERSION = 'decl-v1'
RIGHTS_DECLARATION_TEXT = (
    "I hold the rights to this work, or have the rights holder's permission, "
    "to share it under the licence I have chosen. I understand that a Creative "
    "Commons licence cannot be withdrawn: anyone who receives the work under it "
    "keeps that right."
)
RIGHTS_DECLARATION_REQUIRED_MESSAGE = (
    'The rights declaration must be confirmed (true) to license a publication file: '
    'confirm you hold the rights to share it under the chosen licence'
)
INVALID_LICENSE_MESSAGE = 'license_id must be the id or code of a licence from get-list-licenses'

# The licences DOCiD knows. Selectable ones are offered to depositors; the
# others exist so licences from other sources can still be matched to a row.
# `code` is the SPDX identifier where one exists. Migration d4f6a8c0e2b1 holds a
# frozen copy of this list; add new licences here and in a new migration.
_CC_ELEMENTS = {
    # path: (short label, full name part, allows_commercial, allows_adaptations, share_alike)
    'by': ('BY', 'Attribution', True, True, False),
    'by-sa': ('BY-SA', 'Attribution-ShareAlike', True, True, True),
    'by-nd': ('BY-ND', 'Attribution-NoDerivatives', True, False, False),
    'by-nc': ('BY-NC', 'Attribution-NonCommercial', False, True, False),
    'by-nc-sa': ('BY-NC-SA', 'Attribution-NonCommercial-ShareAlike', False, True, True),
    'by-nc-nd': ('BY-NC-ND', 'Attribution-NonCommercial-NoDerivatives', False, False, False),
}
_CC_VERSION_SUFFIX = {'4.0': 'International', '3.0': 'Unported', '2.5': 'Generic', '2.0': 'Generic'}


def _cc_licence(path, version, selectable, sort_order):
    short, full, commercial, adaptations, share_alike = _CC_ELEMENTS[path]
    return {
        'code': f'CC-{short}-{version}',
        'short_name': f'CC {short} {version}',
        'name': f'Creative Commons {full} {version} {_CC_VERSION_SUFFIX[version]}',
        'url': f'https://creativecommons.org/licenses/{path}/{version}/',
        'requires_attribution': True,
        'allows_commercial': commercial,
        'allows_adaptations': adaptations,
        'share_alike': share_alike,
        'is_selectable': selectable,
        'sort_order': sort_order,
    }


def _build_catalogue():
    rows = [{
        'code': 'CC0-1.0', 'short_name': 'CC0 1.0',
        'name': 'Creative Commons Zero v1.0 Universal (public domain dedication)',
        'url': 'https://creativecommons.org/publicdomain/zero/1.0/',
        'requires_attribution': False, 'allows_commercial': True, 'allows_adaptations': True,
        'share_alike': False, 'is_selectable': True, 'sort_order': 10,
    }]
    # Most to least permissive, as creativecommons.org lists them.
    for position, path in enumerate(['by', 'by-sa', 'by-nd', 'by-nc', 'by-nc-sa', 'by-nc-nd']):
        rows.append(_cc_licence(path, '4.0', True, 20 + position * 10))
    rows.append({
        'code': 'ALL-RIGHTS-RESERVED', 'short_name': 'All rights reserved',
        'name': 'All rights reserved (In Copyright)',
        'url': 'http://rightsstatements.org/vocab/InC/1.0/',
        'requires_attribution': True, 'allows_commercial': False, 'allows_adaptations': False,
        'share_alike': False, 'is_selectable': True, 'sort_order': 90,
    })
    # Not offered to depositors; used to match imported records.
    sort_order = 100
    for version in ('3.0', '2.5', '2.0'):
        for path in _CC_ELEMENTS:
            rows.append(_cc_licence(path, version, False, sort_order))
            sort_order += 1
    rows.extend([
        {'code': 'CC-PDM-1.0', 'short_name': 'Public Domain Mark 1.0', 'name': 'Public Domain Mark 1.0',
         'url': 'https://creativecommons.org/publicdomain/mark/1.0/',
         'requires_attribution': False, 'allows_commercial': True, 'allows_adaptations': True,
         'share_alike': False, 'is_selectable': False, 'sort_order': 200},
        {'code': 'MIT', 'short_name': 'MIT', 'name': 'MIT License',
         'url': 'https://opensource.org/licenses/MIT',
         'requires_attribution': True, 'allows_commercial': True, 'allows_adaptations': True,
         'share_alike': False, 'is_selectable': False, 'sort_order': 210},
        {'code': 'Apache-2.0', 'short_name': 'Apache 2.0', 'name': 'Apache License 2.0',
         'url': 'https://www.apache.org/licenses/LICENSE-2.0',
         'requires_attribution': True, 'allows_commercial': True, 'allows_adaptations': True,
         'share_alike': False, 'is_selectable': False, 'sort_order': 220},
        {'code': 'GPL-3.0', 'short_name': 'GPL 3.0', 'name': 'GNU General Public License v3.0',
         'url': 'https://www.gnu.org/licenses/gpl-3.0.html',
         'requires_attribution': True, 'allows_commercial': True, 'allows_adaptations': True,
         'share_alike': True, 'is_selectable': False, 'sort_order': 230},
    ])
    return rows


LICENSE_CATALOGUE = _build_catalogue()


def ensure_license_catalogue():
    """Insert or update every catalogue row by code. Returns how many rows were added."""
    added = 0
    for row in LICENSE_CATALOGUE:
        licence = Licenses.query.filter_by(code=row['code']).first()
        if licence is None:
            db.session.add(Licenses(**row))
            added += 1
        else:
            for field, value in row.items():
                setattr(licence, field, value)
    db.session.flush()
    return added


# --- Matching a source repository's licence to a row ----------------------------

def normalise_license_url(url):
    """
    Reduce the many spellings of a licence URL to one comparable key.

    https://creativecommons.org/licenses/by/4.0/legalcode.en,
    http://creativecommons.org/licenses/by/4.0/deed.fr and
    creativecommons.org/licenses/by/4.0 all become
    "creativecommons.org/licenses/by/4.0". A national port such as
    /licenses/by-nc-sa/2.5/za/ matches the generic licence of that version.
    """
    if not url:
        return ''
    text = str(url).strip().lower()
    text = re.sub(r'^[a-z][a-z0-9+.-]*://', '', text)
    text = re.split(r'[?#]', text, maxsplit=1)[0]
    if text.startswith('www.'):
        text = text[4:]
    text = text.rstrip('/')
    text = re.sub(r'/(legalcode|deed)(\.[a-z_-]+)?$', '', text).rstrip('/')
    text = re.sub(r'\.(html?|txt|php)$', '', text)
    text = text.replace('rightsstatements.org/page/', 'rightsstatements.org/vocab/')
    port = re.match(r'^(creativecommons\.org/licenses/[a-z-]+/\d\.\d)/[a-z]{2}$', text)
    if port:
        text = port.group(1)
    return text


def _normalise_name(text):
    return re.sub(r'[^a-z0-9]', '', str(text or '').lower())


def match_license(url=None, name=None):
    """The licence row a source's URL (preferred) or name refers to, or None."""
    licences = Licenses.query.all()
    url_key = normalise_license_url(url)
    if url_key:
        for licence in licences:
            if normalise_license_url(licence.url) == url_key:
                return licence
    name_key = _normalise_name(name)
    if name_key:
        for licence in licences:
            if name_key in (_normalise_name(licence.code), _normalise_name(licence.short_name)):
                return licence
    return None


# --- API input ----------------------------------------------------------------

def is_blank_input(raw_value):
    """True for a value the frontend sends for 'nothing': None, '', 'undefined', 'null'."""
    return raw_value is None or str(raw_value).strip() in ('', 'undefined', 'null')


def resolve_license_input(raw_value):
    """
    The selectable licence a client chose, by numeric id or by code ("CC-BY-4.0").

    Returns None for a blank value. Raises ValueError for anything that isn't a
    selectable licence: licences kept only for imports can't be chosen.
    """
    if is_blank_input(raw_value):
        return None
    text = str(raw_value).strip()
    if text.isdigit():
        licence = db.session.get(Licenses, int(text))
    else:
        licence = Licenses.query.filter(db.func.lower(Licenses.code) == text.lower()).first()
    if licence is None or not licence.is_selectable:
        raise ValueError(INVALID_LICENSE_MESSAGE)
    return licence


def is_rights_declared(raw_value):
    """True when the client confirmed the rights declaration."""
    return str(raw_value or '').strip().lower() in ('true', '1', 'yes', 'on')


# --- Serialising ---------------------------------------------------------------

def license_summary(licence):
    """What API responses carry for a licence, or None."""
    if licence is None:
        return None
    return {
        'id': licence.id,
        'code': licence.code,
        'short_name': licence.short_name,
        'name': licence.name,
        'url': licence.url,
    }


def license_details(licence):
    """The summary plus what the licence permits, for the licence list."""
    details = license_summary(licence)
    details.update({
        'requires_attribution': licence.requires_attribution,
        'allows_commercial': licence.allows_commercial,
        'allows_adaptations': licence.allows_adaptations,
        'share_alike': licence.share_alike,
    })
    return details


def rights_declaration_record(files):
    """
    The audit-trail value for one rights declaration: the wording's version and
    every file licence it covered, e.g.
    {"declaration": "decl-v1", "files": {"12": "CC-BY-4.0"}}. Keys are file ids,
    or 1-based form positions on /publish and /version.
    """
    return json.dumps({
        'declaration': RIGHTS_DECLARATION_VERSION,
        'files': {str(key): licence.code for key, licence in files.items() if licence is not None},
    }, sort_keys=True)
