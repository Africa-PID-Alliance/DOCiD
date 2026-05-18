"""add owner_email and owner_user_id to harvest_sources

Revision ID: a7e3f1d8c052
Revises: c2f8a3d9e417
Create Date: 2026-05-18 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a7e3f1d8c052'
down_revision = 'c2f8a3d9e417'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('harvest_sources') as batch_op:
        batch_op.add_column(sa.Column('owner_email', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('owner_user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_harvest_sources_owner_user_id',
            'user_accounts',
            ['owner_user_id'],
            ['user_id'],
            ondelete='SET NULL',
        )

    op.execute(
        "UPDATE harvest_sources SET owner_email = 'bibalerts@lists.lib.sun.ac.za', "
        "owner_user_id = (SELECT user_id FROM user_accounts WHERE email = 'bibalerts@lists.lib.sun.ac.za' LIMIT 1) "
        "WHERE name = 'Stellenbosch University'"
    )
    op.execute(
        "UPDATE harvest_sources SET owner_email = 'librarian@unilag.edu.ng', "
        "owner_user_id = (SELECT user_id FROM user_accounts WHERE email = 'librarian@unilag.edu.ng' LIMIT 1) "
        "WHERE name = 'University of Lagos'"
    )


def downgrade():
    with op.batch_alter_table('harvest_sources') as batch_op:
        batch_op.drop_constraint('fk_harvest_sources_owner_user_id', type_='foreignkey')
        batch_op.drop_column('owner_user_id')
        batch_op.drop_column('owner_email')
