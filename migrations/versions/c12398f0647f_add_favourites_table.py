# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""Add favourites table.

Revision ID: c12398f0647f
Revises: 644ba6b47222
Create Date: 2022-08-10 13:34:23.888686
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = 'c12398f0647f'
down_revision = '644ba6b47222'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'favourites',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('user', sa.String(), nullable=False),
        sa.Column('item_id', UUID(), sa.ForeignKey('metadata.items.id', ondelete='CASCADE')),
        sa.Column('collection_id', UUID(), sa.ForeignKey('metadata.collections.id', ondelete='CASCADE')),
        sa.Column('created_time', sa.DateTime(), nullable=False),
        sa.Column('pinned', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user', 'item_id'),
        sa.UniqueConstraint('user', 'collection_id'),
        schema='metadata',
    )


def downgrade():
    op.drop_table('favourites', schema='metadata')
