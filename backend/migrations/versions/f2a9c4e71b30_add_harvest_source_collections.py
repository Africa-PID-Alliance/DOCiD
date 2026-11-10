"""add harvest_source_collections and DSpace status / write-back columns

Adds the watched-collection integration: one row per DSpace collection DOCiD
harvests for an institution (IK / CH), plus per-record columns on
dspace_mappings for the record's public status in DSpace and for writing the
DOCiD URL back into the item's dc.identifier.uri.

Revision ID: f2a9c4e71b30
Revises: e6f8c02d3b15
Create Date: 2026-11-04 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2a9c4e71b30'
down_revision = 'e6f8c02d3b15'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('harvest_source_collections',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('harvest_source_id', sa.Integer(), nullable=False),
    sa.Column('dspace_collection_uuid', sa.String(length=36), nullable=False),
    sa.Column('dspace_collection_handle', sa.String(length=255), nullable=True),
    sa.Column('collection_name', sa.String(length=255), nullable=True),
    sa.Column('resource_type_id', sa.Integer(), nullable=False),
    sa.Column('write_back_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
    sa.Column('write_back_ok', sa.Boolean(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
    sa.Column('last_harvested_at', sa.DateTime(), nullable=True),
    sa.Column('last_error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['harvest_source_id'], ['harvest_sources.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['resource_type_id'], ['resource_types.id']),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('harvest_source_id', 'dspace_collection_uuid', name='uq_harvest_source_collection_uuid')
    )
    with op.batch_alter_table('harvest_source_collections', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_harvest_source_collections_harvest_source_id'), ['harvest_source_id'], unique=False)

    with op.batch_alter_table('dspace_mappings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('harvest_source_collection_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('dspace_status', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('dspace_status_changed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('writeback_status', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('writeback_attempts', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('writeback_error', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('written_back_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            'fk_dspace_mappings_harvest_source_collection_id',
            'harvest_source_collections', ['harvest_source_collection_id'], ['id'],
            ondelete='SET NULL',
        )
        batch_op.create_index(batch_op.f('ix_dspace_mappings_harvest_source_collection_id'), ['harvest_source_collection_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_dspace_mappings_dspace_status'), ['dspace_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_dspace_mappings_writeback_status'), ['writeback_status'], unique=False)


def downgrade():
    with op.batch_alter_table('dspace_mappings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_dspace_mappings_writeback_status'))
        batch_op.drop_index(batch_op.f('ix_dspace_mappings_dspace_status'))
        batch_op.drop_index(batch_op.f('ix_dspace_mappings_harvest_source_collection_id'))
        batch_op.drop_constraint('fk_dspace_mappings_harvest_source_collection_id', type_='foreignkey')
        batch_op.drop_column('written_back_at')
        batch_op.drop_column('writeback_error')
        batch_op.drop_column('writeback_attempts')
        batch_op.drop_column('writeback_status')
        batch_op.drop_column('dspace_status_changed_at')
        batch_op.drop_column('dspace_status')
        batch_op.drop_column('harvest_source_collection_id')

    with op.batch_alter_table('harvest_source_collections', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_harvest_source_collections_harvest_source_id'))

    op.drop_table('harvest_source_collections')
