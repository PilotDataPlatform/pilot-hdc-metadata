# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""update file unique constraint.

Revision ID: f10349cb95a9
Revises: fe53c1185f01
Create Date: 2023-03-09 15:23:56.278739
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f10349cb95a9'
down_revision = 'fe53c1185f01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        'file_constraint',
        'items',
        ['container_code', 'container_type', 'parent_path', 'name', 'zone'],
        schema='metadata',
    )


def downgrade():
    op.drop_constraint('file_constraint', 'items', schema='metadata')
