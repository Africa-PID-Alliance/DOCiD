"""move the publication date to publication files, and add licences to them

The publication date and the licence belong to each publication file (a work
uploaded in the assign form), not to the DOCiD or to publication documents.

- publications: drop publication_date and publication_date_precision, which
  c5d7e9a1b3f2 added. They were never deployed; dropping them here (rather than
  deleting c5d7e9a1b3f2) keeps databases that already ran it upgradeable.
- New `licenses` reference table, filled with the licences DOCiD offers (CC0,
  the six Creative Commons 4.0 licences, All rights reserved) plus ones kept
  only to match licences from other sources (CC 3.0/2.5/2.0, Public Domain
  Mark, MIT, Apache 2.0, GPL 3.0).
- publications_files: publication_date, publication_date_precision, license_id.
  Nullable with no default, so existing files are untouched.

Revision ID: d4f6a8c0e2b1
Revises: c5d7e9a1b3f2
Create Date: 2026-11-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4f6a8c0e2b1'
down_revision = 'c5d7e9a1b3f2'
branch_labels = None
depends_on = None


# A frozen copy of app/utils/licenses.py LICENSE_CATALOGUE as of this revision.
_CC_ELEMENTS = {
    'by': ('BY', 'Attribution', True, True, False),
    'by-sa': ('BY-SA', 'Attribution-ShareAlike', True, True, True),
    'by-nd': ('BY-ND', 'Attribution-NoDerivatives', True, False, False),
    'by-nc': ('BY-NC', 'Attribution-NonCommercial', False, True, False),
    'by-nc-sa': ('BY-NC-SA', 'Attribution-NonCommercial-ShareAlike', False, True, True),
    'by-nc-nd': ('BY-NC-ND', 'Attribution-NonCommercial-NoDerivatives', False, False, False),
}
_CC_VERSION_SUFFIX = {'4.0': 'International', '3.0': 'Unported', '2.5': 'Generic', '2.0': 'Generic'}


def _cc_licence(path, version, selectable, sort_order):
    short, full, commercial, adaptations, share_alike = _CC_ELEMENTS[path]
    return {
        'code': f'CC-{short}-{version}',
        'short_name': f'CC {short} {version}',
        'name': f'Creative Commons {full} {version} {_CC_VERSION_SUFFIX[version]}',
        'url': f'https://creativecommons.org/licenses/{path}/{version}/',
        'requires_attribution': True,
        'allows_commercial': commercial,
        'allows_adaptations': adaptations,
        'share_alike': share_alike,
        'is_selectable': selectable,
        'sort_order': sort_order,
    }


def _catalogue():
    rows = [{
        'code': 'CC0-1.0', 'short_name': 'CC0 1.0',
        'name': 'Creative Commons Zero v1.0 Universal (public domain dedication)',
        'url': 'https://creativecommons.org/publicdomain/zero/1.0/',
        'requires_attribution': False, 'allows_commercial': True, 'allows_adaptations': True,
        'share_alike': False, 'is_selectable': True, 'sort_order': 10,
    }]
    for position, path in enumerate(['by', 'by-sa', 'by-nd', 'by-nc', 'by-nc-sa', 'by-nc-nd']):
        rows.append(_cc_licence(path, '4.0', True, 20 + position * 10))
    rows.append({
        'code': 'ALL-RIGHTS-RESERVED', 'short_name': 'All rights reserved',
        'name': 'All rights reserved (In Copyright)',
        'url': 'http://rightsstatements.org/vocab/InC/1.0/',
        'requires_attribution': True, 'allows_commercial': False, 'allows_adaptations': False,
        'share_alike': False, 'is_selectable': True, 'sort_order': 90,
    })
    sort_order = 100
    for version in ('3.0', '2.5', '2.0'):
        for path in _CC_ELEMENTS:
            rows.append(_cc_licence(path, version, False, sort_order))
            sort_order += 1
    rows.extend([
        {'code': 'CC-PDM-1.0', 'short_name': 'Public Domain Mark 1.0', 'name': 'Public Domain Mark 1.0',
         'url': 'https://creativecommons.org/publicdomain/mark/1.0/',
         'requires_attribution': False, 'allows_commercial': True, 'allows_adaptations': True,
         'share_alike': False, 'is_selectable': False, 'sort_order': 200},
        {'code': 'MIT', 'short_name': 'MIT', 'name': 'MIT License',
         'url': 'https://opensource.org/licenses/MIT',
         'requires_attribution': True, 'allows_commercial': True, 'allows_adaptations': True,
         'share_alike': False, 'is_selectable': False, 'sort_order': 210},
        {'code': 'Apache-2.0', 'short_name': 'Apache 2.0', 'name': 'Apache License 2.0',
         'url': 'https://www.apache.org/licenses/LICENSE-2.0',
         'requires_attribution': True, 'allows_commercial': True, 'allows_adaptations': True,
         'share_alike': False, 'is_selectable': False, 'sort_order': 220},
        {'code': 'GPL-3.0', 'short_name': 'GPL 3.0', 'name': 'GNU General Public License v3.0',
         'url': 'https://www.gnu.org/licenses/gpl-3.0.html',
         'requires_attribution': True, 'allows_commercial': True, 'allows_adaptations': True,
         'share_alike': True, 'is_selectable': False, 'sort_order': 230},
    ])
    return rows


def upgrade():
    licenses = op.create_table(
        'licenses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=40), nullable=False),
        sa.Column('short_name', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('url', sa.String(length=255), nullable=False),
        sa.Column('requires_attribution', sa.Boolean(), nullable=False),
        sa.Column('allows_commercial', sa.Boolean(), nullable=False),
        sa.Column('allows_adaptations', sa.Boolean(), nullable=False),
        sa.Column('share_alike', sa.Boolean(), nullable=False),
        sa.Column('is_selectable', sa.Boolean(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('url'),
    )
    op.bulk_insert(licenses, _catalogue())

    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.drop_index('ix_publications_publication_date')
        batch_op.drop_column('publication_date_precision')
        batch_op.drop_column('publication_date')

    with op.batch_alter_table('publications_files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('publication_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('publication_date_precision', sa.String(length=5), nullable=True))
        batch_op.add_column(sa.Column('license_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_publications_files_license_id'), ['license_id'], unique=False)
        batch_op.create_foreign_key('fk_publications_files_license_id', 'licenses', ['license_id'], ['id'])


def downgrade():
    with op.batch_alter_table('publications_files', schema=None) as batch_op:
        batch_op.drop_constraint('fk_publications_files_license_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_publications_files_license_id'))
        batch_op.drop_column('license_id')
        batch_op.drop_column('publication_date_precision')
        batch_op.drop_column('publication_date')

    # Back to c5d7e9a1b3f2's columns (empty: the dates themselves aren't restored).
    with op.batch_alter_table('publications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('publication_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('publication_date_precision', sa.String(length=5), nullable=True))
        batch_op.create_index('ix_publications_publication_date', ['publication_date'], unique=False)

    op.drop_table('licenses')
