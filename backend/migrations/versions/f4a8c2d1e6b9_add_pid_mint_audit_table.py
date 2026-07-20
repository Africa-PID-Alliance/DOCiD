"""Add PID mint security audit table.

Revision ID: f4a8c2d1e6b9
Revises: e8f1a2b3c4d5
Create Date: 2026-07-20
"""

from alembic import op
import sqlalchemy as sa


revision = 'f4a8c2d1e6b9'
down_revision = 'e8f1a2b3c4d5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'pid_mint_audit',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('request_id', sa.String(length=36), nullable=False),
        sa.Column('payload_sha256', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('identifier', sa.String(length=255), nullable=True),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user_accounts.user_id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_id'),
        sa.UniqueConstraint(
            'user_id', 'operation', 'idempotency_key',
            name='uq_pid_mint_audit_actor_operation_key',
        ),
    )
    op.create_index('ix_pid_mint_audit_created_at', 'pid_mint_audit', ['created_at'])
    op.create_index('ix_pid_mint_audit_identifier', 'pid_mint_audit', ['identifier'])
    op.create_index('ix_pid_mint_audit_operation', 'pid_mint_audit', ['operation'])
    op.create_index('ix_pid_mint_audit_request_id', 'pid_mint_audit', ['request_id'], unique=True)
    op.create_index('ix_pid_mint_audit_status', 'pid_mint_audit', ['status'])
    op.create_index('ix_pid_mint_audit_user_id', 'pid_mint_audit', ['user_id'])


def downgrade():
    op.drop_index('ix_pid_mint_audit_user_id', table_name='pid_mint_audit')
    op.drop_index('ix_pid_mint_audit_status', table_name='pid_mint_audit')
    op.drop_index('ix_pid_mint_audit_request_id', table_name='pid_mint_audit')
    op.drop_index('ix_pid_mint_audit_operation', table_name='pid_mint_audit')
    op.drop_index('ix_pid_mint_audit_identifier', table_name='pid_mint_audit')
    op.drop_index('ix_pid_mint_audit_created_at', table_name='pid_mint_audit')
    op.drop_table('pid_mint_audit')
