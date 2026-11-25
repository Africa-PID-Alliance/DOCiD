"""
A work's own publication date, kept apart from when its DOCiD record was created.

Repository dates are often only a year ("2019") or a year and month. The date is
stored as a DATE plus a precision ('year', 'month' or 'day') so that "2019" is
never shown as 1 January 2019, and it is always serialised back at the
precision it was given.

``Publications.published`` is a different thing: the time the record was
created in DOCiD. It is returned to clients as ``created_at``.
"""

import re
from datetime import date, datetime

PRECISION_YEAR = 'year'
PRECISION_MONTH = 'month'
PRECISION_DAY = 'day'

# The exact shapes the API accepts: YYYY, YYYY-MM or YYYY-MM-DD.
_STRICT_DATE = re.compile(r'^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$')

# What importers accept: the same shapes, optionally followed by a time part,
# as in "2019-05-14T10:00:00Z" (Figshare) or "2019-05-14 10:00:00" (OJS).
_SOURCE_DATE = re.compile(r'^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?(?:[T ].*)?$')

INVALID_DATE_MESSAGE = 'publicationDate must be YYYY, YYYY-MM or YYYY-MM-DD and not in the future'


def _build(year, month, day):
    """Turn regex groups into (date, precision); raises ValueError for impossible dates."""
    if day is not None:
        return date(int(year), int(month), int(day)), PRECISION_DAY
    if month is not None:
        return date(int(year), int(month), 1), PRECISION_MONTH
    return date(int(year), 1, 1), PRECISION_YEAR


def _is_future(value, precision, today=None):
    """True when the date is after today at the precision it was given."""
    today = today or date.today()
    if precision == PRECISION_YEAR:
        return value.year > today.year
    if precision == PRECISION_MONTH:
        return (value.year, value.month) > (today.year, today.month)
    return value > today


def parse_publication_date_input(raw_value):
    """
    Read a publication date sent by an API client.

    Returns (date, precision), or (None, None) when the value is empty. Raises
    ValueError when it isn't YYYY, YYYY-MM or YYYY-MM-DD, or is in the future.
    """
    text = (raw_value or '').strip()
    if not text or text in ('undefined', 'null'):
        return None, None
    match = _STRICT_DATE.match(text)
    if not match:
        raise ValueError(INVALID_DATE_MESSAGE)
    try:
        value, precision = _build(*match.groups())
    except ValueError:  # an impossible date such as 2019-13 or 2019-02-30
        raise ValueError(INVALID_DATE_MESSAGE) from None
    if _is_future(value, precision):
        raise ValueError(INVALID_DATE_MESSAGE)
    return value, precision


def parse_source_publication_date(raw_value):
    """
    Read a publication date from a source repository (DSpace, Figshare, OJS).

    Lenient: also accepts a trailing time part, and date/datetime objects.
    Returns (date, precision), or (None, None) when the value is missing,
    unreadable or in the future (an embargo or data-entry error, not a real
    publication date).
    """
    if raw_value is None:
        return None, None
    if isinstance(raw_value, datetime):
        value, precision = raw_value.date(), PRECISION_DAY
    elif isinstance(raw_value, date):
        value, precision = raw_value, PRECISION_DAY
    else:
        match = _SOURCE_DATE.match(str(raw_value).strip())
        if not match:
            return None, None
        try:
            value, precision = _build(*match.groups())
        except ValueError:
            return None, None
    if _is_future(value, precision):
        return None, None
    return value, precision


def first_usable_source_date(*raw_values):
    """
    The first value that reads as a publication date, or None.

    Lets a mapper prefer one source field and fall back to the next, e.g.
    dc.date.issued, then dc.date.created when issued is missing or "n.d.".
    """
    for raw_value in raw_values:
        if parse_source_publication_date(raw_value)[0] is not None:
            return raw_value
    return None


def format_publication_date(value, precision):
    """Serialise at the stored precision: "2019", "2019-05" or "2019-05-14"; None when unknown."""
    if value is None:
        return None
    if precision == PRECISION_YEAR:
        return f'{value.year:04d}'
    if precision == PRECISION_MONTH:
        return f'{value.year:04d}-{value.month:02d}'
    return value.isoformat()


def publication_date_of(publication):
    """The publication's own publication date as a string, or None when unknown."""
    return format_publication_date(
        getattr(publication, 'publication_date', None),
        getattr(publication, 'publication_date_precision', None),
    )


def created_at_of(publication):
    """When the record was created in DOCiD, as ISO 8601 UTC with a Z, or None."""
    created = getattr(publication, 'published', None)
    return created.isoformat() + 'Z' if created else None


def apply_source_publication_date(publication, raw_value):
    """
    Save a source repository's publication date on the publication.

    The source wins when it has a readable date; when it has none, an existing
    value is kept rather than cleared. Returns True when a date was set.
    """
    value, precision = parse_source_publication_date(raw_value)
    if value is None:
        return False
    publication.publication_date = value
    publication.publication_date_precision = precision
    return True
