"""add Manuscripts and Book resource types

Re-adds the two resource types that d647148 (2026-09-30) removed. Book also
stays a publication type (the per-file "Publication Type"); the two lists are
separate.

The Publisher account category's allowlist is deliberately left unchanged, so
restricted Publisher accounts can't mint these types.

Inserted by NAME, not id, because environments hold different resource-type
sets (see d5e7b91c2a04). A type that already exists, such as a Manuscripts row
that was never deleted, is skipped.

Revision ID: f7a9b1c3d5e2
Revises: d4f6a8c0e2b1
Create Date: 2026-11-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7a9b1c3d5e2'
down_revision = 'd4f6a8c0e2b1'
branch_labels = None
depends_on = None


# Card images already shipped in the frontend bundle (the ones these types used before).
NEW_RESOURCE_TYPES = [
    ('Manuscripts', '/assets/images/research-icon.png'),
    ('Book', '/assets/images/research-icon.png'),
]

# Every table with a foreign key to resource_types.
REFERENCING_TABLES = (
    'publications',
    'publication_drafts',
    'account_category_resource_types',
    'harvest_source_collections',
)


def upgrade():
    connection = op.get_bind()
    for resource_type_name, poster_url in NEW_RESOURCE_TYPES:
        already_present = connection.execute(
            sa.text("SELECT 1 FROM resource_types WHERE resource_type = :name"),
            {'name': resource_type_name},
        ).first()
        if already_present:
            continue
        connection.execute(
            sa.text(
                "INSERT INTO resource_types (resource_type, default_poster_url) "
                "VALUES (:name, :poster)"
            ),
            {'name': resource_type_name, 'poster': poster_url},
        )


def downgrade():
    connection = op.get_bind()
    for resource_type_name, _poster_url in NEW_RESOURCE_TYPES:
        row = connection.execute(
            sa.text("SELECT id FROM resource_types WHERE resource_type = :name"),
            {'name': resource_type_name},
        ).first()
        if row is None:
            continue
        # Never strand anything: only remove a type nothing refers to.
        in_use = any(
            connection.execute(
                sa.text(f"SELECT 1 FROM {table} WHERE resource_type_id = :id LIMIT 1"),
                {'id': row[0]},
            ).first()
            for table in REFERENCING_TABLES
        )
        if in_use:
            continue
        connection.execute(sa.text("DELETE FROM resource_types WHERE id = :id"), {'id': row[0]})
