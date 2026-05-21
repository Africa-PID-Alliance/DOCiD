"""Defensive: ensure local_context_audit_log exists.

The original 709369017e99 migration created this table, but on some dev
databases it was dropped (or the original migration failed mid-flight).
When the table is missing, project-attach savepoints silently roll back
because the helper writes a PROJECT_ATTACH audit row inside `begin_nested()`
and the UndefinedTable exception aborts the savepoint — so the publish
endpoint returns success while writing zero publication_local_contexts rows.

This migration creates the table only if it isn't already there. Safe to
apply repeatedly and on any environment.

Revision ID: c3e9b2a17d40
Revises: b1d4e7f9a2c5
Create Date: 2026-05-21 11:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c3e9b2a17d40'
# Direct parent on `main` is the LC schema migration. (Locally this was
# generated when an unrelated enrichment migration `b1d4e7f9a2c5` was applied
# in-between; that migration is not on `main`, so we point straight at the
# LC parent here. Existing local DBs already at `c3e9b2a17d40` are unaffected
# because alembic only stores the head version, not the chain history.)
down_revision = 'a9f2c1d4e7b8'
branch_labels = None
depends_on = None


TABLE_NAME = 'local_context_audit_log'


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(name)


def upgrade():
    if _has_table(TABLE_NAME):
        return

    op.create_table(
        TABLE_NAME,
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('publication_id', sa.Integer(), nullable=True),
        sa.Column('local_context_id', sa.Integer(), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user_accounts.user_id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table(TABLE_NAME, schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_local_context_audit_log_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_local_context_audit_log_local_context_id'), ['local_context_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_local_context_audit_log_publication_id'), ['publication_id'], unique=False)


def downgrade():
    # Defensive: only drop if it exists. Some environments may have already
    # created/managed this table outside the original migration chain.
    if not _has_table(TABLE_NAME):
        return
    with op.batch_alter_table(TABLE_NAME, schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_local_context_audit_log_publication_id'))
        batch_op.drop_index(batch_op.f('ix_local_context_audit_log_local_context_id'))
        batch_op.drop_index(batch_op.f('ix_local_context_audit_log_created_at'))
    op.drop_table(TABLE_NAME)
