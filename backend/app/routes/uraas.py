"""Related DOCiDs on a DOCiD landing page, from URAAS keyword overlap.

GET /api/v1/publications/<id>/related-docids

URAAS syncs every docid-demo record into its own database and, given a DOCiD
publication id, returns related records as (DOCiD publication id, DOCiD)
pairs. It only knows docid-demo's ids, so both DOCiDs are checked: if URAAS
holds a different DOCiD for this id (another DOCiD instance, such as
production), nothing is shown, and a related id is shown only when our
record with that id carries the DOCiD URAAS gave.

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
from app.service_uraas import UraasUnavailable, fetch_related_docids

logger = logging.getLogger(__name__)

uraas_bp = Blueprint('uraas', __name__, url_prefix='/api/v1/publications')

# URAAS allows a partner key 120 requests a minute, so cache its answers.
RELATED_CACHE_SECONDS = 3600
# After a failure, wait this long before asking URAAS again, so page views
# don't each sit through the timeout while the Space is down or asleep.
FAILURE_CACHE_SECONDS = 60
UNAVAILABLE_MESSAGE = 'Related DOCiDs are unavailable right now'

ORCID_PATTERN = re.compile(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]', re.IGNORECASE)


def _uraas_answer_for(publication_id):
    """URAAS's answer for publication_id, or None if unavailable.

    The answer is {'page_docid': str or None, 'related': [[id, docid], ...]}.
    """
    # v2: entries cached before URAAS answered in DOCiD ids held its own ids.
    cache_key = f'uraas:related:v2:{publication_id}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached.get('answer')

    try:
        page_docid, related = fetch_related_docids(publication_id)
    except UraasUnavailable as exc:
        logger.warning('URAAS related lookup for publication %s failed: %s', publication_id, exc)
        cache.set(cache_key, {'answer': None}, timeout=FAILURE_CACHE_SECONDS)
        return None
    answer = {'page_docid': page_docid, 'related': [[rid, docid] for rid, docid in related]}
    cache.set(cache_key, {'answer': answer}, timeout=RELATED_CACHE_SECONDS)
    return answer


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


def _describe_related(publication_id, related):
    """Live DOCiD records for URAAS's (id, docid) pairs, in URAAS's order, as response items.

    A pair counts only when our record with that id carries the same DOCiD.
    """
    if not related:
        return []
    expected_docid = {rid: docid for rid, docid in related}
    related_ids = list(expected_docid)

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
    rows_by_id = {row.id: row for row in rows if row.document_docid == expected_docid[row.id]}
    found_ids = [rid for rid, _ in related if rid in rows_by_id]
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

    answer = _uraas_answer_for(publication_id)
    if answer is None:
        return jsonify({'publication_id': publication_id, 'related': [],
                        'error': UNAVAILABLE_MESSAGE}), 503

    if answer['page_docid'] != publication.document_docid:
        # URAAS hasn't ingested this record (no DOCiD, no related), or it knows
        # this id as another record, e.g. on a different DOCiD instance.
        if answer['page_docid'] is not None or answer['related']:
            logger.info('URAAS holds publication %s as %r, not %r; showing no related DOCiDs',
                        publication_id, answer['page_docid'], publication.document_docid)
        return jsonify({'publication_id': publication_id, 'related': []})

    related = [(rid, docid) for rid, docid in answer['related'] if rid != publication_id]
    return jsonify({'publication_id': publication_id,
                    'related': _describe_related(publication_id, related)})
