"""Add Book, Masters Thesis and PhD Thesis resource types

Requested by client amendment: the publication-type dropdown needs Book and the
two thesis levels so that monographs and postgraduate research can be minted
under their own type instead of being filed as something else.

Inserted by NAME rather than id, because the environments genuinely hold
different resource-type sets (production runs the Indigenous Knowledge / Patent
/ Cultural Heritage set, while a fresh local DB seeded by seed_reference_data.py
holds the DataCite-style Article / Dataset / Software set). Anything keyed on id
would corrupt one of them.

Revision ID: d5e7b91c2a04
Revises: c8f1a3d4e5b6
"""
import sqlalchemy as sa
from alembic import op

revision = 'd5e7b91c2a04'
down_revision = 'c8f1a3d4e5b6'
branch_labels = None
depends_on = None


# Reuses icons already shipped in the frontend bundle — no new binary assets.
# Theses share the universities icon; swap these paths if dedicated artwork lands.
NEW_RESOURCE_TYPES = [
    ('Book', '/assets/images/research-icon.png'),
    ('Masters Thesis', '/assets/images/universities-icon.png'),
    ('PhD Thesis', '/assets/images/universities-icon.png'),
]


def upgrade():
    connection = op.get_bind()

    # resource_types.default_poster_url is added by b8c4e2a91f37, but this
    # migration must also survive an environment where that column is absent.
    has_poster_column = connection.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'resource_types' AND column_name = 'default_poster_url'"
    )).first() is not None

    for resource_type_name, poster_url in NEW_RESOURCE_TYPES:
        already_present = connection.execute(
            sa.text("SELECT 1 FROM resource_types WHERE resource_type = :name"),
            {'name': resource_type_name},
        ).first()
        if already_present:
            continue

        if has_poster_column:
            connection.execute(
                sa.text(
                    "INSERT INTO resource_types (resource_type, default_poster_url) "
                    "VALUES (:name, :poster)"
                ),
                {'name': resource_type_name, 'poster': poster_url},
            )
        else:
            connection.execute(
                sa.text("INSERT INTO resource_types (resource_type) VALUES (:name)"),
                {'name': resource_type_name},
            )


def downgrade():
    connection = op.get_bind()
    for resource_type_name, _poster_url in NEW_RESOURCE_TYPES:
        # Never strand publications: only remove a type nothing is filed under.
        in_use = connection.execute(
            sa.text(
                "SELECT 1 FROM publications p JOIN resource_types rt ON rt.id = p.resource_type_id "
                "WHERE rt.resource_type = :name LIMIT 1"
            ),
            {'name': resource_type_name},
        ).first()
        if in_use:
            continue
        connection.execute(
            sa.text("DELETE FROM resource_types WHERE resource_type = :name"),
            {'name': resource_type_name},
        )
