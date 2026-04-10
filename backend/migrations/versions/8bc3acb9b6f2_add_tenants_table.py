"""add tenants table

Revision ID: 8bc3acb9b6f2
Revises: 43bbf20ef475
Create Date: 2026-04-09 09:04:16.656866

NOTE: This migration was manually trimmed down from the auto-generated
version. Alembic autogenerate picked up several unrelated schema-drift
items (local_context_audit_log, dspace_mappings index uniqueness,
local_contexts constraint, publications.document_docid nullability,
etc.) that are NOT part of the tenants work. Those are pre-existing
drift between models.py and the actual prod DB that deserves its own
migration. Keeping this file strictly additive (one new table) so it's
safe to apply to any environment.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8bc3acb9b6f2'
down_revision = '43bbf20ef475'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('logo_dark_url', sa.String(length=500), nullable=True),
        sa.Column('favicon_url', sa.String(length=500), nullable=True),
        sa.Column('og_image_url', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=9), nullable=True),
        sa.Column('primary_color_dark', sa.String(length=9), nullable=True),
        sa.Column('accent_color', sa.String(length=9), nullable=True),
        sa.Column('page_title', sa.String(length=255), nullable=True),
        sa.Column('page_description', sa.Text(), nullable=True),
        sa.Column('hero_tagline', sa.String(length=500), nullable=True),
        sa.Column('footer_copyright', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('email_from_name', sa.String(length=255), nullable=True),
        sa.Column(
            'feature_flags',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            'is_active',
            sa.Boolean(),
            server_default='true',
            nullable=False,
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_tenants_slug'),
            ['slug'],
            unique=True,
        )


def downgrade():
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_tenants_slug'))
    op.drop_table('tenants')
