"""add curator review state to publication_enrichments

Revision ID: b1d4e7f9a2c5
Revises: a9f2c1d4e7b8
Create Date: 2026-05-20 20:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'b1d4e7f9a2c5'
down_revision = 'a9f2c1d4e7b8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('publication_enrichments',
                  sa.Column('review_status', sa.String(length=20), nullable=True))
    op.add_column('publication_enrichments',
                  sa.Column('reviewed_by', sa.Integer(),
                            sa.ForeignKey('user_accounts.user_id', ondelete='SET NULL'),
                            nullable=True))
    op.add_column('publication_enrichments',
                  sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('publication_enrichments',
                  sa.Column('review_note', sa.Text(), nullable=True))
    op.create_index('ix_publication_enrichments_review_status',
                    'publication_enrichments', ['review_status'])

    # Backfill: every existing OpenAlex DOI-match row from Phase 1 is implicitly
    # auto-accepted. Phase 1 only ever matched by DOI (no title fallback), so
    # any status='enriched' row is safe to mark accepted.
    op.execute("""
        UPDATE publication_enrichments
        SET review_status = 'accepted',
            reviewed_at = COALESCE(enriched_at, updated_at, NOW())
        WHERE source_name = 'openalex'
          AND status = 'enriched'
          AND review_status IS NULL
    """)


def downgrade():
    op.drop_index('ix_publication_enrichments_review_status',
                  table_name='publication_enrichments')
    op.drop_column('publication_enrichments', 'review_note')
    op.drop_column('publication_enrichments', 'reviewed_at')
    op.drop_column('publication_enrichments', 'reviewed_by')
    op.drop_column('publication_enrichments', 'review_status')
