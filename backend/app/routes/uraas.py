"""Related DOCiDs on a DOCiD landing page, from URAAS keyword overlap.

GET /api/v1/publications/<id>/related-docids

The DOCiD publication id is sent to URAAS as its paper id, and the paper ids
URAAS returns are looked up as DOCiD publication ids. This assumes the two
systems share ids.

Each related record comes back with its resource type, its owner and the
names of any creators it shares with the page's record.
Records keep the exact order URAAS returns them in.
"""
import logging
import re
import unicodedata

from flask import Blueprint, jsonify

from app import cache, db
from app.models import PublicationCreators, Publications, ResourceTypes
from app.service_uraas import UraasUnavailable, fetch_related_paper_ids

logger = logging.getLogger(__name__)

uraas_bp = Blueprint('uraas', __name__, url_prefix='/api/v1/publications')

# URAAS allows a partner key 120 requests a minute, so cache its answers.
RELATED_CACHE_SECONDS = 3600
# After a failure, wait this long before asking URAAS again, so page views
# don't each sit through the timeout while the Space is down or asleep.
FAILURE_CACHE_SECONDS = 60
UNAVAILABLE_MESSAGE = 'Related DOCiDs are unavailable right now'

ORCID_PATTERN = re.compile(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]', re.IGNORECASE)


def _related_ids_for(publication_id):
    """Return URAAS's related ids for publication_id, or None if unavailable."""
    cache_key = f'uraas:related:{publication_id}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached.get('ids')

    try:
        ids = fetch_related_paper_ids(publication_id)
    except UraasUnavailable as exc:
        logger.warning('URAAS related lookup for publication %s failed: %s', publication_id, exc)
        cache.set(cache_key, {'ids': None}, timeout=FAILURE_CACHE_SECONDS)
        return None
    cache.set(cache_key, {'ids': ids}, timeout=RELATED_CACHE_SECONDS)
    return ids


def _letters(text):
    """Lowercase ASCII letters only: 'Naudé-Smith' gives 'naudesmith'."""
    decomposed = unicodedata.normalize('NFKD', text or '')
    return ''.join(ch for ch in decomposed if ch.isascii() and ch.isalpha()).lower()


def _orcid(creator):
    """The creator's bare ORCID iD, or None."""
    identifier = creator.identifier or ''
    if (creator.identifier_type or '').lower() != 'orcid' and 'orcid.org' not in identifier.lower():
        return None
    match = ORCID_PATTERN.search(identifier)
    return match.group(0).upper() if match else None


def _name_key(creator):
    """(surname, first initial), or None when the creator has no given name.

    Organisations such as 'Manuscripts Section' are stored with a family name
    only, so they never match by name.
    """
    family = _letters(creator.family_name)
    given = _letters(creator.given_name)
    if not family or not given:
        return None
    return family, given[0]


def _same_person(creator, other):
    """ORCID decides when both creators have one; otherwise surname + initial."""
    orcid, other_orcid = _orcid(creator), _orcid(other)
    if orcid and other_orcid:
        return orcid == other_orcid
    key = _name_key(creator)
    return key is not None and key == _name_key(other)


def _display_name(creator):
    parts = (creator.given_name, creator.family_name)
    return ' '.join(part.strip() for part in parts if part and part.strip())


def _shared_authors(page_creators, other_creators):
    """Names, as written on the page's record, of its creators who also created the other record."""
    names = []
    for creator in page_creators:
        if any(_same_person(creator, other) for other in other_creators):
            name = _display_name(creator)
            if name and name not in names:
                names.append(name)
    return names


def _describe_related(publication_id, related_ids):
    """Live DOCiD records for related_ids, in URAAS's order, as response items."""
    if not related_ids:
        return []

    rows = (
        db.session.query(
            Publications.id,
            Publications.document_title,
            Publications.document_docid,
            Publications.resource_type_id,
            Publications.owner,
            ResourceTypes.resource_type,
        )
        .outerjoin(ResourceTypes, ResourceTypes.id == Publications.resource_type_id)
        .filter(
            Publications.id.in_(related_ids),
            Publications.deleted_at.is_(None),
            Publications.document_docid.isnot(None),
        )
        .all()
    )
    rows_by_id = {row.id: row for row in rows}
    found_ids = [rid for rid in related_ids if rid in rows_by_id]
    if not found_ids:
        return []

    # One query for the page's creators and every related record's creators.
    creators = (
        db.session.query(
            PublicationCreators.publication_id,
            PublicationCreators.given_name,
            PublicationCreators.family_name,
            PublicationCreators.identifier,
            PublicationCreators.identifier_type,
        )
        .filter(PublicationCreators.publication_id.in_([publication_id] + found_ids))
        .order_by(PublicationCreators.id)
        .all()
    )
    creators_by_publication = {}
    for creator in creators:
        creators_by_publication.setdefault(creator.publication_id, []).append(creator)
    page_creators = creators_by_publication.get(publication_id, [])

    items = []
    for rid in found_ids:
        row = rows_by_id[rid]
        shared = _shared_authors(page_creators, creators_by_publication.get(rid, []))
        items.append({
            'id': row.id,
            'document_title': row.document_title,
            'document_docid': row.document_docid,
            'resource_type_id': row.resource_type_id,
            'resource_type': row.resource_type,
            'owner': row.owner,
            'shared_authors': shared,
        })
    return items


@uraas_bp.route('/<int:publication_id>/related-docids', methods=['GET'])
def get_related_docids(publication_id):
    """
    Related DOCiDs for a publication, from URAAS keyword overlap.
    Each item carries its resource type, owner and the names of the
    creators it shares with this publication (empty when none).
    Items keep the exact order URAAS returns them in.
    ---
    tags:
      - Publications
    parameters:
      - in: path
        name: publication_id
        type: integer
        required: true
    responses:
      200:
        description: Related DOCiD records (may be empty)
      404:
        description: Publication not found or retired
      503:
        description: URAAS is not configured or unreachable
    """
    publication = Publications.query.filter_by(id=publication_id, deleted_at=None).first()
    if publication is None:
        return jsonify({'error': 'Publication not found'}), 404

    related_ids = _related_ids_for(publication_id)
    if related_ids is None:
        return jsonify({'publication_id': publication_id, 'related': [],
                        'error': UNAVAILABLE_MESSAGE}), 503

    related_ids = [rid for rid in related_ids if rid != publication_id]
    return jsonify({'publication_id': publication_id,
                    'related': _describe_related(publication_id, related_ids)})
