"""Add DataCite resource types for Figshare/DSpace/OJS integrations

Revision ID: b8c3a1f5d720
Revises: 4e67049fd9a2
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8c3a1f5d720'
down_revision = '30fd2740d9c1'
branch_labels = None
depends_on = None

DATACITE_RESOURCE_TYPES = [
    'Text',
    'Dataset',
    'Image',
    'Audiovisual',
    'Collection',
    'Software',
    'Other',
]


def upgrade():
    connection = op.get_bind()

    # Fix sequence to match current max id (seed script may have reset it)
    connection.execute(
        sa.text("SELECT setval('resource_types_id_seq', COALESCE((SELECT MAX(id) FROM resource_types), 1))")
    )

    for resource_type_name in DATACITE_RESOURCE_TYPES:
        result = connection.execute(
            sa.text("SELECT id FROM resource_types WHERE resource_type = :name"),
            {"name": resource_type_name}
        )
        if result.fetchone() is None:
            connection.execute(
                sa.text("INSERT INTO resource_types (resource_type) VALUES (:name)"),
                {"name": resource_type_name}
            )


def downgrade():
    connection = op.get_bind()
    for resource_type_name in DATACITE_RESOURCE_TYPES:
        connection.execute(
            sa.text("DELETE FROM resource_types WHERE resource_type = :name"),
            {"name": resource_type_name}
        )
