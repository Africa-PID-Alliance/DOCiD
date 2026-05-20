"""Add project_external_id to publication_local_contexts (per-attachment provenance)

Replaces the single (publication_id, local_context_id) unique constraint with two
partial unique indexes to support shared items appearing under multiple LC projects.

Revision ID: a9f2c1d4e7b8
Revises: b8c4e2a91f37
Create Date: 2026-05-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a9f2c1d4e7b8'
down_revision = 'b8c4e2a91f37'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('publication_local_contexts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_external_id', sa.String(length=255), nullable=True))
        batch_op.drop_constraint('uq_publication_local_context', type_='unique')
        batch_op.create_index('idx_plc_project_external_id', ['project_external_id'], unique=False)

    # Partial unique indexes (PostgreSQL treats NULL as distinct under plain unique).
    op.create_index(
        'uq_plc_item_no_project',
        'publication_local_contexts',
        ['publication_id', 'local_context_id'],
        unique=True,
        postgresql_where=sa.text('project_external_id IS NULL'),
    )
    op.create_index(
        'uq_plc_item_with_project',
        'publication_local_contexts',
        ['publication_id', 'local_context_id', 'project_external_id'],
        unique=True,
        postgresql_where=sa.text('project_external_id IS NOT NULL'),
    )


def downgrade():
    op.drop_index('uq_plc_item_with_project', table_name='publication_local_contexts')
    op.drop_index('uq_plc_item_no_project', table_name='publication_local_contexts')

    with op.batch_alter_table('publication_local_contexts', schema=None) as batch_op:
        batch_op.drop_index('idx_plc_project_external_id')
        batch_op.create_unique_constraint(
            'uq_publication_local_context',
            ['publication_id', 'local_context_id'],
        )
        batch_op.drop_column('project_external_id')
