# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import has_permission
from sqlalchemy import or_
from sqlalchemy.orm.query import Query
from sqlalchemy.sql import expression
from sqlalchemy_utils.types.ltree import LQUERY

from app.app_utils import encode_label_for_ltree
from app.config import ConfigClass
from app.models.sql_items import ItemModel


async def collection_query_permissions(project_code: str, current_identity: dict, item_query: Query) -> Query:
    search_auth_user = encode_label_for_ltree(current_identity['username']) + '.*'
    if not await has_permission(ConfigClass.AUTH_SERVICE, project_code, 'file_any', 'core', 'view', current_identity):
        if not await has_permission(
            ConfigClass.AUTH_SERVICE, project_code, 'file_in_own_namefolder', 'core', 'view', current_identity
        ):
            item_query = item_query.filter(ItemModel.zone != ConfigClass.CORE_ZONE_VALUE)
        else:
            item_query = item_query.filter(
                or_(
                    ItemModel.zone != ConfigClass.CORE_ZONE_VALUE,
                    ItemModel.parent_path.lquery(expression.cast(search_auth_user, LQUERY)),
                )
            )
    return item_query
