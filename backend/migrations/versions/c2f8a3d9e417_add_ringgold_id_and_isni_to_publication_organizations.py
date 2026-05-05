"""add ringgold_id and isni to publication_organizations

Revision ID: c2f8a3d9e417
Revises: e1b2c3d4f5a6
Create Date: 2026-05-05 16:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2f8a3d9e417'
down_revision = 'e1b2c3d4f5a6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('publication_organizations',
                  sa.Column('ringgold_id', sa.String(length=50), nullable=True))
    op.add_column('publication_organizations',
                  sa.Column('isni', sa.String(length=50), nullable=True))
    op.create_index('ix_publication_organizations_ringgold_id',
                    'publication_organizations', ['ringgold_id'])
    op.create_index('ix_publication_organizations_isni',
                    'publication_organizations', ['isni'])

    # Backfill from existing identifier where possible
    op.execute("""
        UPDATE publication_organizations
        SET isni = REGEXP_REPLACE(identifier, '.*/', '')
        WHERE identifier_type = 'isni' AND identifier IS NOT NULL AND isni IS NULL
    """)
    op.execute("""
        UPDATE publication_organizations
        SET ringgold_id = identifier
        WHERE identifier_type = 'ringgold' AND identifier IS NOT NULL AND ringgold_id IS NULL
    """)
    # Cross-fill from ringgold_institutions seed
    op.execute("""
        UPDATE publication_organizations po
        SET ringgold_id = ri.ringgold_id::text
        FROM ringgold_institutions ri
        WHERE po.isni = ri.isni AND po.ringgold_id IS NULL AND po.isni IS NOT NULL
    """)
    op.execute("""
        UPDATE publication_organizations po
        SET isni = ri.isni
        FROM ringgold_institutions ri
        WHERE po.ringgold_id::text = ri.ringgold_id::text AND po.isni IS NULL AND ri.isni IS NOT NULL
    """)


def downgrade():
    op.drop_index('ix_publication_organizations_isni', table_name='publication_organizations')
    op.drop_index('ix_publication_organizations_ringgold_id', table_name='publication_organizations')
    op.drop_column('publication_organizations', 'isni')
    op.drop_column('publication_organizations', 'ringgold_id')
