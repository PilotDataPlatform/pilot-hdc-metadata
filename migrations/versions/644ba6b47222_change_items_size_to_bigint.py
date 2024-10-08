# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""Change items size to bigint.

Revision ID: 644ba6b47222
Revises: e9ee5505b100
Create Date: 2022-07-20 00:07:29.948685
"""
import sqlalchemy as sa
from alembic import op

from app.config import ConfigClass

# revision identifiers, used by Alembic.
revision = '644ba6b47222'
down_revision = 'e9ee5505b100'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('items', 'size', existing_type=sa.Integer(), type_=sa.BIGINT(), schema=ConfigClass.METADATA_SCHEMA)


def downgrade():
    op.alter_column('items', 'size', existing_type=sa.BIGINT(), type_=sa.Integer(), schema=ConfigClass.METADATA_SCHEMA)
