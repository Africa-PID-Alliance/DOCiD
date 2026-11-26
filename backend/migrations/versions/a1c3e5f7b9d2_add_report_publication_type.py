"""add Report publication type

A new option in the per-file "Publication Type" dropdown, which lists every
publication_types row.

Inserted by NAME, not id, because environments hold different publication-type
sets (seed_reference_data.py and scripts/seed_db.py seed different lists). An
existing "Report" row is skipped.

Revision ID: a1c3e5f7b9d2
Revises: f7a9b1c3d5e2
Create Date: 2026-11-26 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1c3e5f7b9d2'
down_revision = 'f7a9b1c3d5e2'
branch_labels = None
depends_on = None


PUBLICATION_TYPE_NAME = 'Report'

# Every table with a foreign key to publication_types.
REFERENCING_TABLES = ('publications_files', 'publication_documents')


def upgrade():
    connection = op.get_bind()
    already_present = connection.execute(
        sa.text("SELECT 1 FROM publication_types WHERE publication_type_name = :name"),
        {'name': PUBLICATION_TYPE_NAME},
    ).first()
    if already_present:
        return
    connection.execute(
        sa.text("INSERT INTO publication_types (publication_type_name) VALUES (:name)"),
        {'name': PUBLICATION_TYPE_NAME},
    )


def downgrade():
    connection = op.get_bind()
    row = connection.execute(
        sa.text("SELECT id FROM publication_types WHERE publication_type_name = :name"),
        {'name': PUBLICATION_TYPE_NAME},
    ).first()
    if row is None:
        return
    # Never strand a file or document: only remove the type when nothing uses it.
    for table in REFERENCING_TABLES:
        in_use = connection.execute(
            sa.text(f"SELECT 1 FROM {table} WHERE publication_type_id = :id LIMIT 1"),
            {'id': row[0]},
        ).first()
        if in_use:
            return
    connection.execute(sa.text("DELETE FROM publication_types WHERE id = :id"), {'id': row[0]})
