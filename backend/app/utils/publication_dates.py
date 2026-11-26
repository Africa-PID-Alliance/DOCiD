"""
A publication file's own publication date.

Only a publication file (a work uploaded in the assign form) carries a
publication date; a DOCiD's own date is when it was created in DOCiD
(``Publications.published``, returned to clients as ``created_at``).

Dates are often only a year ("2019") or a year and month, so the date is stored
as a DATE plus a precision ('year', 'month' or 'day'). "2019" is never shown as
1 January 2019, and it is always serialised back at the precision it was given.
"""

import re
from datetime import date

PRECISION_YEAR = 'year'
PRECISION_MONTH = 'month'
PRECISION_DAY = 'day'

# The exact shapes the API accepts: YYYY, YYYY-MM or YYYY-MM-DD.
_STRICT_DATE = re.compile(r'^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$')

INVALID_DATE_MESSAGE = 'publication_date must be YYYY, YYYY-MM or YYYY-MM-DD and not in the future'


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

    Returns (date, precision), or (None, None) when the value is empty (or the
    frontend's "undefined"/"null"). Raises ValueError when it isn't YYYY,
    YYYY-MM or YYYY-MM-DD, or is in the future.
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


def format_publication_date(value, precision):
    """Serialise at the stored precision: "2019", "2019-05" or "2019-05-14"; None when unknown."""
    if value is None:
        return None
    if precision == PRECISION_YEAR:
        return f'{value.year:04d}'
    if precision == PRECISION_MONTH:
        return f'{value.year:04d}-{value.month:02d}'
    return value.isoformat()


def publication_date_of(publication_file):
    """A publication file's publication date as a string, or None when unknown."""
    return format_publication_date(
        getattr(publication_file, 'publication_date', None),
        getattr(publication_file, 'publication_date_precision', None),
    )


def created_at_of(publication):
    """When a DOCiD was created in DOCiD, as ISO 8601 UTC with a Z, or None."""
    created = getattr(publication, 'published', None)
    return created.isoformat() + 'Z' if created else None
