"""
Shared helpers for per-account-category filtering of reference lists (multi-tenant
data hiding). Single source of truth used by both the reference-list endpoints and
the publication write-path guards.

Visibility rule (allowlist, safe-by-default):
- A user whose account_category.is_restricted is True may only use the resource
  types mapped in account_category_resource_types (even if that set is empty).
- A user with no category, or an unrestricted category, or an anonymous caller
  sees the full list (backward compatible).

Built generic (accepts the mapping model) so the same pattern can extend to the
other reference dropdowns (funder types, publication types, etc.) later.
"""

from app.models import AccountCategoryResourceTypes


def resolve_account_category(user):
    """Return the user's AccountCategories row, or None when uncategorized/anonymous."""
    if user is None:
        return None
    return getattr(user, "account_category", None)


def is_account_restricted(user):
    """True only when the user's category exists and is flagged restricted."""
    category = resolve_account_category(user)
    return bool(category and category.is_restricted)


def allowed_resource_type_ids(user):
    """
    Set of resource_type ids the user is allowed to mint, or None meaning
    "no restriction — full list applies".
    """
    category = resolve_account_category(user)
    if not category or not category.is_restricted:
        return None
    rows = AccountCategoryResourceTypes.query.filter_by(
        account_category_id=category.id
    ).all()
    return {row.resource_type_id for row in rows}


def is_resource_type_allowed(user, resource_type_id):
    """
    Whether the given resource_type_id may be minted by this user under the
    account-category rule. Unrestricted users are always allowed.
    """
    allowed_ids = allowed_resource_type_ids(user)
    if allowed_ids is None:
        return True
    try:
        return int(resource_type_id) in allowed_ids
    except (TypeError, ValueError):
        return False


def is_resource_type_allowed_strict(user, resource_type_id):
    """
    Fail-closed variant for authenticated mint/import paths: an unresolvable
    identity (valid JWT whose user no longer exists) must NOT be treated as
    unrestricted. Anonymous callers never reach these paths.
    """
    if user is None:
        return False
    return is_resource_type_allowed(user, resource_type_id)
