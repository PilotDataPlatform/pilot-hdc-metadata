# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Update column archived to status.

Revision ID: 15315557f1fd
Revises: 6417f7affeb1
Create Date: 2023-02-08 15:54:08.433214
"""
import time

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

from app.models.models_items import ItemStatus

# revision identifiers, used by Alembic.
revision = '15315557f1fd'
down_revision = '6417f7affeb1'
branch_labels = None
depends_on = None


def upgrade():
    status_enum = pg.ENUM(ItemStatus, name='item_status_enum')
    status_enum.create(op.get_bind())

    op.add_column(
        'items',
        sa.Column(
            'status',
            pg.ENUM(ItemStatus, name='item_status_enum', create_type=False),
            nullable=False,
            server_default=ItemStatus.REGISTERED,
        ),
        schema='metadata',
    )
    op.execute(f'update metadata.items set "status" = \'{ItemStatus.ACTIVE}\' where "archived" is false;')
    op.execute(f'update metadata.items set "status" = \'{ItemStatus.ARCHIVED}\' where "archived" is true;')
    op.drop_column('items', 'archived', schema='metadata')


def downgrade():
    op.add_column(
        'items', sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'), schema='metadata'
    )
    tmp_file = f'/tmp/item_{time.time()}.csv'
    op.execute(
        'COPY (select * from metadata.items where "status" = \'REGISTERED\') '
        f'TO \'{tmp_file}\'  WITH DELIMITER \',\' CSV HEADER'
    )
    op.execute('delete from metadata.items where "status" = \'REGISTERED\'')
    op.execute('update metadata.items set "archived" = false where "status" = \'ACTIVE\'')
    op.execute('update metadata.items set "archived" = true where "status" = \'ARCHIVED\'')

    op.drop_column('items', 'status', schema='metadata')
    op.execute('drop type item_status_enum;')
