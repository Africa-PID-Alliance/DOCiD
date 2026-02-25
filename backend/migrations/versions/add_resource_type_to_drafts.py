"""Add resource_type_id to publication_drafts for multiple drafts per user

Revision ID: add_resource_type_to_drafts
Revises: add_ringgold_institutions
Create Date: 2024-12-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_resource_type_to_drafts'
down_revision = 'add_ringgold_institutions'
branch_labels = None
depends_on = None


def upgrade():
    # Add resource_type_id column (nullable initially for existing data)
    with op.batch_alter_table('publication_drafts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('resource_type_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_publication_drafts_resource_type',
            'resource_types',
            ['resource_type_id'],
            ['id']
        )
        batch_op.create_index('ix_publication_drafts_resource_type_id', ['resource_type_id'])

    # Set default resource_type_id for existing drafts (1 = default type)
    op.execute("UPDATE publication_drafts SET resource_type_id = 1 WHERE resource_type_id IS NULL")

    # Make column non-nullable after setting defaults
    with op.batch_alter_table('publication_drafts', schema=None) as batch_op:
        batch_op.alter_column('resource_type_id', nullable=False)
        # Drop the unique index on email only (it's implemented as a unique index, not constraint)
        batch_op.drop_index('ix_publication_drafts_email')
        # Create composite unique constraint on email + resource_type_id
        batch_op.create_unique_constraint(
            'uq_publication_drafts_email_resource_type',
            ['email', 'resource_type_id']
        )
        # Re-create non-unique index on email for lookups
        batch_op.create_index('ix_publication_drafts_email', ['email'], unique=False)


def downgrade():
    with op.batch_alter_table('publication_drafts', schema=None) as batch_op:
        # Drop composite unique constraint
        batch_op.drop_constraint('uq_publication_drafts_email_resource_type', type_='unique')
        # Drop non-unique email index
        batch_op.drop_index('ix_publication_drafts_email')
        # Restore unique index on email only
        batch_op.create_index('ix_publication_drafts_email', ['email'], unique=True)
        # Drop the foreign key and index
        batch_op.drop_index('ix_publication_drafts_resource_type_id')
        batch_op.drop_constraint('fk_publication_drafts_resource_type', type_='foreignkey')
        # Drop the column
        batch_op.drop_column('resource_type_id')
