# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Update items model.

Revision ID: 6417f7affeb1
Revises: c12398f0647f
Create Date: 2022-08-12 18:25:43.362053
"""
from alembic import op

revision = '6417f7affeb1'
down_revision = 'c12398f0647f'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('update metadata.items set "size" = 0 where "size" is null;')
    op.alter_column('items', 'size', nullable=False, schema='metadata')


def downgrade():
    op.alter_column('items', 'size', nullable=True, schema='metadata')
