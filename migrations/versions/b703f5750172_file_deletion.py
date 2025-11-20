# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""File deletion.

Revision ID: b703f5750172
Revises: 0a475ee40d8a
Create Date: 2025-11-20 11:13:47.323529
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b703f5750172'
down_revision = '0a475ee40d8a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'items',
        sa.Column(
            'deleted',
            sa.Boolean(),
            nullable=False,
            server_default=sa.sql.false(),
        ),
        schema='metadata',
    )
    op.add_column(
        'items',
        sa.Column(
            'deleted_by',
            sa.Boolean(),
            nullable=True,
            server_default=sa.sql.null(),
        ),
        schema='metadata',
    )
    op.add_column(
        'items',
        sa.Column(
            'deleted_at',
            sa.DateTime(),
            nullable=True,
            server_default=sa.sql.null(),
        ),
        schema='metadata',
    )


def downgrade():
    op.drop_column('items', 'deleted', schema='metadata')
    op.drop_column('items', 'deleted_by', schema='metadata')
    op.drop_column('items', 'deleted_at', schema='metadata')
