"""Add checksum / integrity columns to publications_files and publication_documents

Column adds are idempotent (guarded against the DB inspector) so the migration
is safe to re-run and safe across partially-migrated environments.

Revision ID: e8f1a2b3c4d5
Revises: h3c4d5e6f7a8
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
# h3c4d5e6f7a8 is the single current head (d2f4e1a8b6c7 already merged the
# c3e9b2a17d40 / b1d4e7f9a2c5 branches upstream).
revision = 'e8f1a2b3c4d5'
down_revision = 'h3c4d5e6f7a8'
branch_labels = None
depends_on = None


_TABLES = ('publications_files', 'publication_documents')

_COLUMNS = (
    ('checksum', lambda: sa.Column('checksum', sa.String(length=64), nullable=True)),
    ('checksum_algorithm', lambda: sa.Column('checksum_algorithm', sa.String(length=20), nullable=True)),
    ('file_size', lambda: sa.Column('file_size', sa.BigInteger(), nullable=True)),
    ('checksum_status', lambda: sa.Column('checksum_status', sa.String(length=30), nullable=True)),
    ('checksum_error', lambda: sa.Column('checksum_error', sa.Text(), nullable=True)),
    ('checksum_generated_at', lambda: sa.Column('checksum_generated_at', sa.DateTime(), nullable=True)),
    ('checksum_last_checked_at', lambda: sa.Column('checksum_last_checked_at', sa.DateTime(), nullable=True)),
)


def _existing_columns(bind, table):
    """Column names present on `table`, or empty set if the table is absent.

    Uses information_schema directly rather than the SQLAlchemy inspector, which
    raises NoSuchTableError for a missing table instead of returning empty.
    """
    rows = bind.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = :t"
        ),
        {"t": table},
    )
    return {row[0] for row in rows}


def upgrade():
    bind = op.get_bind()
    for table in _TABLES:
        existing = _existing_columns(bind, table)
        for name, column_factory in _COLUMNS:
            if name not in existing:
                op.add_column(table, column_factory())


def downgrade():
    bind = op.get_bind()
    for table in _TABLES:
        existing = _existing_columns(bind, table)
        for name, _ in reversed(_COLUMNS):
            if name in existing:
                op.drop_column(table, name)
