# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Add items table.

Revision ID: 212e0e60c178
Revises:
Create Date: 2022-03-14 15:17:34.248801
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import LtreeType

# revision identifiers, used by Alembic.
revision = '212e0e60c178'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'items',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('parent', UUID()),
        sa.Column('parent_path', LtreeType()),
        sa.Column('restore_path', LtreeType()),
        sa.Column('archived', sa.Boolean(), nullable=False),
        sa.Column('type', pg.ENUM('name_folder', 'folder', 'file', name='type_enum', create_type=True), nullable=False),
        sa.Column('zone', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('size', sa.Integer()),
        sa.Column('owner', sa.String()),
        sa.Column('container_code', sa.String()),
        sa.Column(
            'container_type', pg.ENUM('project', 'dataset', name='container_enum', create_type=True), nullable=False
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
        sa.UniqueConstraint('parent_path', 'archived', 'zone', 'name', 'container_code', 'container_type'),
        sa.Index(
            'name_folder_unique',
            'zone',
            'name',
            'container_code',
            'container_type',
            unique=True,
            postgresql_where=sa.Column('type') == 'name_folder',
        ),
        schema='metadata',
    )


def downgrade():
    op.drop_table('items', schema='metadata')
    op.execute('drop type type_enum; drop type container_enum;')
