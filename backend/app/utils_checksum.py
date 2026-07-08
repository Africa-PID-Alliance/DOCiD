"""Checksum utilities for research-object integrity.

Generates and compares SHA-256 fingerprints over stored file *bytes only*
(never metadata — DOCiD metadata is intentionally mutable). Used at upload
time, by the backfill script, and by the public verification endpoint.

See docs/checksum-integrity-implementation-plan.md for the full design.
"""

import hashlib
import os
from datetime import datetime
from urllib.parse import urlparse, unquote

from config import Config

# Read files in 1 MiB chunks so large uploads never load fully into memory.
_CHUNK_SIZE = 1024 * 1024

DEFAULT_ALGORITHM = 'SHA-256'

# checksum_status vocabulary (kept in sync with the model columns / plan)
STATUS_PENDING = 'pending'                          # row exists, not yet hashed
STATUS_VERIFIED = 'verified'                         # hash computed & stored
STATUS_EXTERNAL = 'external_not_supported'           # bytes live off-platform
STATUS_MISSING = 'missing_bytes'                     # local file not found
STATUS_FAILED = 'failed'                             # hashing raised an error


def compute_file_checksum(path):
    """Stream a file from disk and return (sha256_hex, size_bytes).

    Raises FileNotFoundError / OSError if the path cannot be read — callers
    decide whether that maps to STATUS_MISSING or STATUS_FAILED.
    """
    hasher = hashlib.sha256()
    size = 0
    with open(path, 'rb') as handle:
        while True:
            chunk = handle.read(_CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
            size += len(chunk)
    return hasher.hexdigest(), size


def _local_upload_hosts():
    """Netlocs (lowercased) that serve THIS deployment's /uploads directory."""
    hosts = set()
    for base in (Config.UPLOADS_BASE_URL, Config.APPLICATION_BASE_URL):
        if base:
            netloc = urlparse(base).netloc.lower()
            if netloc:
                hosts.add(netloc)
    return hosts


def local_path_for_url(file_url):
    """Resolve a stored file_url to an on-disk path under UPLOADS_DIRECTORY.

    Returns the absolute path for locally-hosted /uploads/... files, or None
    for external URLs (video links, DataCite/DSpace/Figshare targets, etc.)
    that DOCiD does not host and therefore cannot hash.

    Guards against path traversal: any '..' segment yields None.
    """
    if not file_url:
        return None

    parsed = urlparse(file_url)
    url_path = parsed.path or file_url

    if '/uploads/' not in url_path:
        return None

    # A netloc that isn't one of our own upload hosts means the bytes live
    # elsewhere (an imported record pointing at another site's /uploads/...).
    # Relative URLs (no netloc) are always local.
    if parsed.netloc and parsed.netloc.lower() not in _local_upload_hosts():
        return None

    relative = unquote(url_path.split('/uploads/', 1)[1])
    if not relative or '..' in relative.split('/'):
        return None

    uploads_dir = os.path.abspath(Config.UPLOADS_DIRECTORY)
    candidate = os.path.abspath(os.path.join(uploads_dir, relative))

    # Ensure the resolved path stays inside the uploads directory.
    if candidate != uploads_dir and not candidate.startswith(uploads_dir + os.sep):
        return None

    return candidate


def checksum_for_stored_file(file_url, local_path=None):
    """Compute the checksum for a stored file, classifying the outcome.

    Pass ``local_path`` directly when it is already known (upload time). Otherwise
    the path is resolved from ``file_url`` (backfill of existing rows).

    Returns a dict: {checksum, checksum_algorithm, file_size, checksum_status,
    checksum_error}. ``checksum`` is None unless status is verified.
    """
    result = {
        'checksum': None,
        'checksum_algorithm': DEFAULT_ALGORITHM,
        'file_size': None,
        'checksum_status': None,
        'checksum_error': None,
    }

    if local_path is None:
        local_path = local_path_for_url(file_url)

    if local_path is None:
        result['checksum_status'] = STATUS_EXTERNAL
        return result

    if not os.path.exists(local_path):
        result['checksum_status'] = STATUS_MISSING
        result['checksum_error'] = f'local file not found: {os.path.basename(local_path)}'
        return result

    try:
        digest, size = compute_file_checksum(local_path)
    except OSError as exc:
        result['checksum_status'] = STATUS_FAILED
        result['checksum_error'] = str(exc)
        return result

    result['checksum'] = digest
    result['file_size'] = size
    result['checksum_status'] = STATUS_VERIFIED
    return result


def checksum_fields_for_upload(local_path, file_url=None):
    """Build model kwargs (checksum columns) for a freshly-saved upload.

    Safe to call unconditionally at upload time: on any error it records a status
    instead of raising, so a hashing hiccup never blocks a publication from saving.
    Timestamps use datetime.utcnow() for consistency with the rest of the models.
    """
    try:
        computed = checksum_for_stored_file(file_url, local_path=local_path)
    except Exception as exc:  # never let checksumming break an upload
        computed = {
            'checksum': None,
            'checksum_algorithm': DEFAULT_ALGORITHM,
            'file_size': None,
            'checksum_status': STATUS_FAILED,
            'checksum_error': str(exc),
        }

    now = datetime.utcnow()
    return {
        'checksum': computed['checksum'],
        'checksum_algorithm': computed['checksum_algorithm'],
        'file_size': computed['file_size'],
        'checksum_status': computed['checksum_status'],
        'checksum_error': computed['checksum_error'],
        'checksum_generated_at': now if computed['checksum'] else None,
        'checksum_last_checked_at': now,
    }


def external_checksum_fields():
    """Checksum kwargs for an external (non-hosted) object, e.g. a video URL."""
    return {
        'checksum': None,
        'checksum_algorithm': DEFAULT_ALGORITHM,
        'file_size': None,
        'checksum_status': STATUS_EXTERNAL,
        'checksum_error': None,
        'checksum_generated_at': None,
        'checksum_last_checked_at': datetime.utcnow(),
    }
