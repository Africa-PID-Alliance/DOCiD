"""add default_poster_url to resource_types

Revision ID: b8c4e2a91f37
Revises: a7e3f1d8c052
Create Date: 2026-05-20 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b8c4e2a91f37'
down_revision = 'a7e3f1d8c052'
branch_labels = None
depends_on = None


# Per-type default card image, served from the frontend bundle at /assets/images/.
# Relative path so each deployment resolves it against its own public origin.
DEFAULTS_BY_TYPE = {
    'Indigeneous Knowledge': '/assets/images/museum.png',
    'Patent': '/assets/images/patent.png',
    'Cultural Heritage': '/assets/images/museums-Icon.png',
    'Project': '/assets/images/research.png',
    'Funder': '/assets/images/universities.png',
    'DMP (Data Management Plan)': '/assets/images/other-icon.png',
    'Manuscripts': '/assets/images/research-icon.png',
}


def upgrade():
    with op.batch_alter_table('resource_types') as batch_op:
        batch_op.add_column(sa.Column('default_poster_url', sa.String(length=500), nullable=True))

    for resource_type_name, asset_path in DEFAULTS_BY_TYPE.items():
        op.execute(
            sa.text("UPDATE resource_types SET default_poster_url = :u WHERE resource_type = :t")
            .bindparams(u=asset_path, t=resource_type_name)
        )


def downgrade():
    with op.batch_alter_table('resource_types') as batch_op:
        batch_op.drop_column('default_poster_url')
