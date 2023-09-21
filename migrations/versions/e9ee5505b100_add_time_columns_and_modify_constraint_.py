# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""add_time_columns_and_modify_constraint_to_collections_table.

Revision ID: e9ee5505b100
Revises: c9d07577d8d2
Create Date: 2022-05-09 12:53:04.316417
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e9ee5505b100'
down_revision = 'c9d07577d8d2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('collections', sa.Column('created_time', sa.DateTime(), nullable=False), schema='metadata')
    op.add_column('collections', sa.Column('last_updated_time', sa.DateTime(), nullable=False), schema='metadata')
    op.alter_column('collections', sa.Column('name', sa.String(), nullable=False), schema='metadata')
    op.alter_column('collections', sa.Column('container_code', sa.String(), nullable=False), schema='metadata')
    op.alter_column('collections', sa.Column('owner', sa.String(), nullable=False), schema='metadata')


def downgrade():
    op.drop_column('collections', 'created_time', schema='metadata')
    op.drop_column('collections', 'last_updated_time', schema='metadata')
    op.alter_column('collections', sa.Column('name', sa.String()), schema='metadata')
    op.alter_column('collections', sa.Column('container_code', sa.String()), schema='metadata')
    op.alter_column('collections', sa.Column('owner', sa.String()), schema='metadata')
