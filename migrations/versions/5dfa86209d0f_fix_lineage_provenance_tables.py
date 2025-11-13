# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Fix lineage provenance tables.

Revision ID: 5dfa86209d0f
Revises: f10349cb95a9
Create Date: 2023-03-17 10:07:53.444002
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

from app.models.models_items import ItemStatus

# revision identifiers, used by Alembic.
revision = '5dfa86209d0f'
down_revision = 'f10349cb95a9'
branch_labels = None
depends_on = None


def upgrade():
    # Allow some lineage, provenance fields to be null
    op.alter_column('lineage', 'consumes', nullable=True, schema='metadata')
    op.alter_column('lineage', 'produces', nullable=True, schema='metadata')
    op.alter_column('provenance', 'lineage_id', nullable=True, schema='metadata')

    # Change provenance "archived" to "status"
    op.add_column(
        'provenance',
        sa.Column(
            'status',
            pg.ENUM(ItemStatus, name='item_status_enum', create_type=False),
            nullable=False,
            server_default=ItemStatus.REGISTERED,
        ),
        schema='metadata',
    )
    op.drop_column('provenance', 'archived', schema='metadata')


def downgrade():
    op.alter_column('lineage', 'consumes', nullable=False, schema='metadata')
    op.alter_column('lineage', 'produces', nullable=False, schema='metadata')
    op.alter_column('provenance', 'lineage_id', nullable=False, schema='metadata')
    op.add_column(
        'provenance',
        sa.Column('archived', sa.Boolean(), nullable=False),
        schema='metadata',
    )
    op.drop_column('provenance', 'status', schema='metadata')
