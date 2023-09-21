# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""Add time columns to items table.

Revision ID: 76ffd36326a3
Revises: cad81b7e09aa
Create Date: 2022-04-13 13:23:46.380997
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '76ffd36326a3'
down_revision = 'cad81b7e09aa'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('items', sa.Column('created_time', sa.DateTime(), nullable=False), schema='metadata')
    op.add_column('items', sa.Column('last_updated_time', sa.DateTime(), nullable=False), schema='metadata')


def downgrade():
    op.drop_column('items', 'created_time', schema='metadata')
    op.drop_column('items', 'last_updated_time', schema='metadata')
