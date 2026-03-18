"""add enrichment tables and publication metadata columns

Revision ID: 633ee4b7df07
Revises: 1ab46a1e1952
Create Date: 2026-03-18 19:13:24.840234

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '633ee4b7df07'
down_revision = '1ab46a1e1952'
branch_labels = None
depends_on = None


def upgrade():
    # Create enrichment_runs table
    op.create_table('enrichment_runs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('run_type', sa.String(length=50), nullable=False),
    sa.Column('source_name', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('publications_processed', sa.Integer(), nullable=True),
    sa.Column('publications_enriched', sa.Integer(), nullable=True),
    sa.Column('publications_skipped', sa.Integer(), nullable=True),
    sa.Column('publications_failed', sa.Integer(), nullable=True),
    sa.Column('error_summary', sa.Text(), nullable=True),
    sa.Column('last_processed_publication_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('enrichment_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_enrichment_runs_run_type'), ['run_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_enrichment_runs_source_name'), ['source_name'], unique=False)

    # Create publication_enrichments table
    op.create_table('publication_enrichments',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('publication_id', sa.Integer(), nullable=False),
    sa.Column('source_name', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('enriched_at', sa.DateTime(), nullable=True),
    sa.Column('raw_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['publication_id'], ['publications.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('publication_id', 'source_name', name='uq_publication_source_enrichment')
    )
    with op.batch_alter_table('publication_enrichments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_publication_enrichments_publication_id'), ['publication_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_publication_enrichments_source_name'), ['source_name'], unique=False)

    # Add enrichment columns to publications
    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('citation_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('influential_citation_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('open_access_status', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('open_access_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('openalex_topics', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        batch_op.add_column(sa.Column('openalex_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('semantic_scholar_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('abstract_text', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('openaire_id', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.drop_column('openaire_id')
        batch_op.drop_column('abstract_text')
        batch_op.drop_column('semantic_scholar_id')
        batch_op.drop_column('openalex_id')
        batch_op.drop_column('openalex_topics')
        batch_op.drop_column('open_access_url')
        batch_op.drop_column('open_access_status')
        batch_op.drop_column('influential_citation_count')
        batch_op.drop_column('citation_count')

    with op.batch_alter_table('publication_enrichments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_publication_enrichments_source_name'))
        batch_op.drop_index(batch_op.f('ix_publication_enrichments_publication_id'))

    op.drop_table('publication_enrichments')

    with op.batch_alter_table('enrichment_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_enrichment_runs_source_name'))
        batch_op.drop_index(batch_op.f('ix_enrichment_runs_run_type'))

    op.drop_table('enrichment_runs')
