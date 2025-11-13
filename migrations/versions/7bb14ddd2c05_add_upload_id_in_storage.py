# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""add_upload_id_in_storage.

Revision ID: 7bb14ddd2c05
Revises: 15315557f1fd
Create Date: 2023-03-01 09:46:24.834120
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '7bb14ddd2c05'
down_revision = '15315557f1fd'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('storage', sa.Column('upload_id', sa.String(), server_default=''), schema='metadata')


def downgrade():
    op.drop_column('storage', 'upload_id', schema='metadata')
