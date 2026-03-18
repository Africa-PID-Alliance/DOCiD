"""Add national_id_researchers table

Revision ID: 1ab46a1e1952
Revises: a3f1c8d52e91
Create Date: 2026-03-18 18:39:40.500243

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ab46a1e1952'
down_revision = 'a3f1c8d52e91'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('national_id_researchers',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=500), nullable=False),
    sa.Column('national_id_number', sa.String(length=100), nullable=False),
    sa.Column('country', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('national_id_number', 'country', name='uq_national_id_country')
    )
    with op.batch_alter_table('national_id_researchers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_national_id_researchers_country'), ['country'], unique=False)
        batch_op.create_index(batch_op.f('ix_national_id_researchers_national_id_number'), ['national_id_number'], unique=False)


def downgrade():
    with op.batch_alter_table('national_id_researchers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_national_id_researchers_national_id_number'))
        batch_op.drop_index(batch_op.f('ix_national_id_researchers_country'))

    op.drop_table('national_id_researchers')
