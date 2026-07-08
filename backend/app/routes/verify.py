"""Public integrity-verification endpoint.

Returns the stored SHA-256 checksums for every object in a DOCiD so that anyone
who has downloaded a file can re-hash their copy and compare. This is a
*view/compare* facility — it does NOT re-read DOCiD's stored bytes (that server-side
tamper check is the job of backfill_checksums.py --recheck). UX copy must not imply
live verification.

Scope: only non-deleted, resolvable publications are exposed. Drafts live in a
separate table (PublicationDrafts) and are never reachable here.
"""
import logging

from flask import Blueprint, jsonify, request

from app import db
from app.models import Publications
from app.utils_checksum import STATUS_VERIFIED

logger = logging.getLogger(__name__)

verify_bp = Blueprint('verify', __name__)


def _object_dto(obj, object_class):
    """Serialize the checksum-relevant fields of a file/document row."""
    return {
        'id': obj.id,
        'object_class': object_class,
        'title': obj.title,
        'file_name': getattr(obj, 'file_name', None),
        'handle_identifier': getattr(obj, 'handle_identifier', None),
        'checksum': obj.checksum,
        'checksum_algorithm': obj.checksum_algorithm,
        'file_size': obj.file_size,
        'checksum_status': obj.checksum_status,
        'checksum_generated_at': obj.checksum_generated_at.isoformat() if obj.checksum_generated_at else None,
        'checksum_last_checked_at': obj.checksum_last_checked_at.isoformat() if obj.checksum_last_checked_at else None,
    }


def _build_verification(document_docid):
    """Return (payload, status_code) for a verification lookup."""
    if not document_docid:
        return {'error': 'identifier is required'}, 400

    publication = Publications.query \
        .options(
            db.joinedload(Publications.publications_files),
            db.joinedload(Publications.publication_documents),
        ) \
        .filter_by(document_docid=document_docid) \
        .first()

    if not publication:
        return {'error': 'No matching DOCiD found'}, 404

    # Soft-deleted / retired records: don't expose file metadata.
    if publication.deleted_at is not None:
        return {'error': 'This DOCiD has been retired', 'docid': document_docid}, 410

    objects = (
        [_object_dto(f, 'file') for f in publication.publications_files]
        + [_object_dto(d, 'document') for d in publication.publication_documents]
    )

    # Only count objects whose checksum is trustworthy. A row can carry a stale
    # checksum with status='failed' (e.g. a --recheck mismatch); those are NOT
    # verifiable and must not be advertised as such.
    verifiable = sum(1 for o in objects if o['checksum_status'] == STATUS_VERIFIED)

    return {
        'docid': publication.document_docid,
        'title': publication.document_title,
        'algorithm': 'SHA-256',
        'object_count': len(objects),
        'verifiable_object_count': verifiable,
        'objects': objects,
        'note': (
            'Compare these stored fingerprints against your downloaded files '
            '(e.g. `shasum -a 256 <file>`). A match confirms the file is identical '
            'to the version registered in DOCiD.'
        ),
    }, 200


@verify_bp.route('/api/v1/verify', methods=['GET'])
def verify_by_query():
    """Verify by ?identifier=<docid> — handles DOCiDs containing slashes safely."""
    document_docid = (request.args.get('identifier') or '').strip()
    payload, status = _build_verification(document_docid)
    return jsonify(payload), status


@verify_bp.route('/api/v1/verify/<path:document_docid>', methods=['GET'])
def verify_by_path(document_docid):
    """Verify by path — <path:...> converter preserves slashes in the DOCiD."""
    payload, status = _build_verification((document_docid or '').strip())
    return jsonify(payload), status
