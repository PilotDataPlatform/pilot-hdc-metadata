# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""empty message.

Revision ID: 0a475ee40d8a
Revises: 5dfa86209d0f
Create Date: 2023-03-29 14:04:16.516966
"""
from alembic import op
from sqlalchemy import BIGINT
from sqlalchemy import Integer

# revision identifiers, used by Alembic.
revision = '0a475ee40d8a'
down_revision = '5dfa86209d0f'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'provenance',
        'size',
        nullable=True,
        schema='metadata',
        existing_type=Integer(),
        type_=BIGINT(),
        postgresql_using='size::bigint',
    )


def downgrade():
    op.alter_column(
        'provenance',
        'size',
        nullable=True,
        schema='metadata',
        existing_type=BIGINT(),
        type_=Integer(),
        postgresql_using='size::integer',
    )
