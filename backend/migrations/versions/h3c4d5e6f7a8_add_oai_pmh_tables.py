"""Add harvest_state and harvest_staging_records tables for OAI-PMH harvesting.

The harvest_state table uses a COALESCE-based unique index so that NULL set_spec
rows deduplicate correctly (PostgreSQL allows multiple NULLs under a plain
UniqueConstraint, which would let duplicate state rows accumulate).

in_progress is set atomically via a conditional UPDATE (UPDATE … WHERE in_progress=FALSE)
so parallel cron workers cannot both claim the same harvest concurrently.

Revision ID: h3c4d5e6f7a8
Revises: a7b8c9d0e1f2
Create Date: 2026-06-10 10:02:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'h3c4d5e6f7a8'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'harvest_state',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('endpoint', sa.String(500), nullable=False),
        sa.Column('metadata_prefix', sa.String(50), nullable=False),
        sa.Column('set_spec', sa.String(255), nullable=True),
        sa.Column('granularity', sa.String(40), nullable=True),
        sa.Column('last_success_from', sa.DateTime(), nullable=True),
        sa.Column('last_success_until', sa.DateTime(), nullable=True),
        sa.Column('last_resumption_token', sa.String(500), nullable=True),
        sa.Column('in_progress', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('in_progress_since', sa.DateTime(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_run_status', sa.String(20), nullable=True),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_harvest_state_endpoint', 'harvest_state', ['endpoint'])
    # COALESCE-based unique index so NULL set_spec still deduplicates.
    op.execute(
        "CREATE UNIQUE INDEX uq_harvest_state_endpoint_prefix_set "
        "ON harvest_state (endpoint, metadata_prefix, COALESCE(set_spec, ''))"
    )

    op.create_table(
        'harvest_staging_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('endpoint', sa.String(500), nullable=False),
        sa.Column('oai_identifier', sa.String(255), nullable=False),
        sa.Column('oai_datestamp', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('raw_xml', sa.Text(), nullable=True),
        sa.Column('normalised', JSONB, nullable=True),
        sa.Column('matched_publication_id', sa.Integer(),
                  sa.ForeignKey('publications.id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('match_method', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='new'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_unique_constraint(
        'uq_harvest_staging_endpoint_id',
        'harvest_staging_records',
        ['endpoint', 'oai_identifier'],
    )
    op.create_index('ix_harvest_staging_status', 'harvest_staging_records', ['status'])
    op.create_index('ix_harvest_staging_oai_datestamp', 'harvest_staging_records', ['oai_datestamp'])
    op.create_index('ix_harvest_staging_matched_pub', 'harvest_staging_records', ['matched_publication_id'])


def downgrade():
    op.drop_index('ix_harvest_staging_matched_pub', table_name='harvest_staging_records')
    op.drop_index('ix_harvest_staging_oai_datestamp', table_name='harvest_staging_records')
    op.drop_index('ix_harvest_staging_status', table_name='harvest_staging_records')
    op.drop_constraint('uq_harvest_staging_endpoint_id', 'harvest_staging_records', type_='unique')
    op.drop_table('harvest_staging_records')

    op.execute('DROP INDEX IF EXISTS uq_harvest_state_endpoint_prefix_set')
    op.drop_index('ix_harvest_state_endpoint', table_name='harvest_state')
    op.drop_table('harvest_state')
