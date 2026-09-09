"""Allow the restricted Publisher category to mint Book

The Publisher account category is is_restricted, so its accounts may only mint
resource types explicitly allowlisted in account_category_resource_types --
until now, Manuscripts alone. Publishers publish monographs, so Book is added
to that allowlist.

Theses are deliberately NOT added: they are university outputs rather than
publisher ones, and a restricted category should stay narrow.

Resolved by NAME on both sides, because resource_types ids differ between
environments (see d5e7b91c2a04).

Revision ID: e6f8c02d3b15
Revises: d5e7b91c2a04
"""
import sqlalchemy as sa
from alembic import op

revision = 'e6f8c02d3b15'
down_revision = 'd5e7b91c2a04'
branch_labels = None
depends_on = None

CATEGORY_NAME = 'Publisher'
RESOURCE_TYPE_NAME = 'Book'


def _resolve_ids(connection):
    """Look up the category and resource type by name; None if either is absent."""
    category_row = connection.execute(
        sa.text("SELECT id FROM account_categories WHERE category_name = :name"),
        {'name': CATEGORY_NAME},
    ).first()
    resource_type_row = connection.execute(
        sa.text("SELECT id FROM resource_types WHERE resource_type = :name"),
        {'name': RESOURCE_TYPE_NAME},
    ).first()
    if not category_row or not resource_type_row:
        return None, None
    return category_row[0], resource_type_row[0]


def upgrade():
    connection = op.get_bind()
    category_id, resource_type_id = _resolve_ids(connection)
    if category_id is None:
        # An environment without the Publisher category or without Book has
        # nothing to allowlist; skip rather than fail the migration chain.
        return

    already_mapped = connection.execute(
        sa.text(
            "SELECT 1 FROM account_category_resource_types "
            "WHERE account_category_id = :category AND resource_type_id = :resource_type"
        ),
        {'category': category_id, 'resource_type': resource_type_id},
    ).first()
    if already_mapped:
        return

    connection.execute(
        sa.text(
            "INSERT INTO account_category_resource_types (account_category_id, resource_type_id) "
            "VALUES (:category, :resource_type)"
        ),
        {'category': category_id, 'resource_type': resource_type_id},
    )


def downgrade():
    connection = op.get_bind()
    category_id, resource_type_id = _resolve_ids(connection)
    if category_id is None:
        return
    connection.execute(
        sa.text(
            "DELETE FROM account_category_resource_types "
            "WHERE account_category_id = :category AND resource_type_id = :resource_type"
        ),
        {'category': category_id, 'resource_type': resource_type_id},
    )
