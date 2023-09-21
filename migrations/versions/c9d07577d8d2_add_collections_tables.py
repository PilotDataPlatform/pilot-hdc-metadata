# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""add_collections_tables.

Revision ID: c9d07577d8d2
Revises: 76ffd36326a3
Create Date: 2022-05-05 16:20:30.559058
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = 'c9d07577d8d2'
down_revision = '76ffd36326a3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'collections',
        sa.Column('id', UUID(), nullable=False, primary_key=True),
        sa.Column('name', sa.String()),
        sa.Column('container_code', sa.String()),
        sa.Column('owner', sa.String()),
        schema='metadata',
    )
    op.create_table(
        'items_collections',
        sa.Column('item_id', UUID(), sa.ForeignKey('metadata.items.id', ondelete='CASCADE'), nullable=False),
        sa.Column(
            'collection_id', UUID(), sa.ForeignKey('metadata.collections.id', ondelete='CASCADE'), nullable=False
        ),
        sa.PrimaryKeyConstraint('item_id', 'collection_id'),
        sa.Index('collection_item_unique', 'collection_id', 'item_id', unique=True),
        schema='metadata',
    )


def downgrade():
    op.drop_table('collections', schema='metadata')
    op.drop_table('items_collections', schema='metadata')
