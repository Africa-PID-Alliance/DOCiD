"""Add append-only audit log for state-changing requests.

Revision ID: a7c9e2f4b6d8
Revises: f4a8c2d1e6b9
Create Date: 2026-07-20
"""

from alembic import op
import sqlalchemy as sa


revision = 'a7c9e2f4b6d8'
down_revision = 'f4a8c2d1e6b9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'mutation_audit',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('request_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_role', sa.String(length=50), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=True),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('payload_sha256', sa.String(length=64), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=False),
        sa.Column('outcome', sa.String(length=20), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mutation_audit_created_at', 'mutation_audit', ['created_at'])
    op.create_index('ix_mutation_audit_outcome', 'mutation_audit', ['outcome'])
    op.create_index('ix_mutation_audit_request_id', 'mutation_audit', ['request_id'], unique=True)
    op.create_index('ix_mutation_audit_response_status', 'mutation_audit', ['response_status'])
    op.create_index('ix_mutation_audit_user_id', 'mutation_audit', ['user_id'])

    # Enforce append-only semantics below the ORM. The application database
    # role may insert and select events, but no UPDATE or DELETE can succeed.
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_mutation_audit_change()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'mutation_audit records are immutable';
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER mutation_audit_immutable
        BEFORE UPDATE OR DELETE ON mutation_audit
        FOR EACH ROW EXECUTE FUNCTION prevent_mutation_audit_change()
    """)


def downgrade():
    op.execute('DROP TRIGGER IF EXISTS mutation_audit_immutable ON mutation_audit')
    op.execute('DROP FUNCTION IF EXISTS prevent_mutation_audit_change()')
    op.drop_index('ix_mutation_audit_user_id', table_name='mutation_audit')
    op.drop_index('ix_mutation_audit_response_status', table_name='mutation_audit')
    op.drop_index('ix_mutation_audit_request_id', table_name='mutation_audit')
    op.drop_index('ix_mutation_audit_outcome', table_name='mutation_audit')
    op.drop_index('ix_mutation_audit_created_at', table_name='mutation_audit')
    op.drop_table('mutation_audit')
