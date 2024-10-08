# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""Add lineage provenance tables.

Revision ID: fe53c1185f01
Revises: 7bb14ddd2c05
Create Date: 2023-03-06 14:10:47.376740
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import LtreeType

from app.models.models_lineage_provenance import TransformationType

# revision identifiers, used by Alembic.
revision = 'fe53c1185f01'
down_revision = '7bb14ddd2c05'
branch_labels = None
depends_on = None


def upgrade():
    tfrm_type_enum = pg.ENUM(TransformationType, name='tfrm_type_enum')
    tfrm_type_enum.create(op.get_bind())

    op.create_table(
        'lineage',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('consumes', sa.ARRAY(UUID()), nullable=False),
        sa.Column('produces', sa.ARRAY(UUID()), nullable=False),
        sa.Column(
            'tfrm_type',
            pg.ENUM(TransformationType, name='tfrm_type_enum', create_type=False),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
        schema='metadata',
    )

    op.create_table(
        'provenance',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('lineage_id', UUID(), nullable=False),
        sa.Column('item_id', UUID(), nullable=False),
        sa.Column('snapshot_time', sa.DateTime(), nullable=False),
        sa.Column('parent', UUID()),
        sa.Column('parent_path', LtreeType()),
        sa.Column('restore_path', LtreeType()),
        sa.Column('archived', sa.Boolean(), nullable=False),
        sa.Column(
            'type',
            pg.ENUM(name='type_enum', create_type=False),
            nullable=False,
        ),
        sa.Column('zone', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('size', sa.Integer()),
        sa.Column('owner', sa.String()),
        sa.Column('container_code', sa.String()),
        sa.Column(
            'container_type',
            pg.ENUM(name='container_enum', create_type=False),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
        schema='metadata',
    )


def downgrade():
    op.drop_table('lineage', schema='metadata')
    op.drop_table('provenance', schema='metadata')
    op.execute('drop type tfrm_type_enum;')
