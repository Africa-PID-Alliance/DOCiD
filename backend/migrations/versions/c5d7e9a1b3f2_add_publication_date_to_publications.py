"""add publication_date and publication_date_precision to publications

The work's own publication date, separate from `published` (when the record
was created in DOCiD). Precision is 'year', 'month' or 'day', so a year-only
date such as "2019" is not presented as 1 January. Both columns are nullable
with no default: existing rows stay NULL until the backfill runs.

Revision ID: c5d7e9a1b3f2
Revises: b84d1e0c27f6
Create Date: 2026-11-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5d7e9a1b3f2'
down_revision = 'b84d1e0c27f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('publication_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('publication_date_precision', sa.String(length=5), nullable=True))
        batch_op.create_index(batch_op.f('ix_publications_publication_date'), ['publication_date'], unique=False)


def downgrade():
    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_publications_publication_date'))
        batch_op.drop_column('publication_date_precision')
        batch_op.drop_column('publication_date')
