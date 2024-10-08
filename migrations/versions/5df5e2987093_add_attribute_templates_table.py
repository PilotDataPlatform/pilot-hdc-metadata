# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""Add attribute_templates table.

Revision ID: 5df5e2987093
Revises: 212e0e60c178
Create Date: 2022-03-15 15:26:46.407896
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '5df5e2987093'
down_revision = '212e0e60c178'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'attribute_templates',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('project_code', sa.String(), nullable=False),
        sa.Column('attributes', sa.JSON()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
        schema='metadata',
    )


def downgrade():
    op.drop_table('attribute_templates', schema='metadata')
