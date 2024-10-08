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
from app.models.models_items import GETItemsByLocation
from app.models.models_items import ItemStatus
from app.models.sql_items import ItemModel


async def search_permissions_filter(
    item_query: Query,
    current_identity: dict,
    params: GETItemsByLocation,
) -> Query:

    searching_for_namefolders = False
    if params.status == ItemStatus.ARCHIVED:
        item_location_for_permissions = ItemModel.restore_path
    elif not params.parent_path and not params.restore_path and not params.recursive:
        searching_for_namefolders = True
    else:
        item_location_for_permissions = ItemModel.parent_path
    search_auth_user = encode_label_for_ltree(current_identity['username']) + '.*'

    project_code = params.container_code
    if not await has_permission(ConfigClass.AUTH_SERVICE, project_code, 'file_any', 'core', 'view', current_identity):
        if not await has_permission(
            ConfigClass.AUTH_SERVICE, project_code, 'file_in_own_namefolder', 'core', 'view', current_identity
        ):
            item_query = item_query.filter(ItemModel.zone != ConfigClass.CORE_ZONE_VALUE)
        else:
            if searching_for_namefolders:
                item_query = item_query.filter(
                    or_(ItemModel.zone != ConfigClass.CORE_ZONE_VALUE, ItemModel.name == current_identity['username'])
                )
            else:
                item_query = item_query.filter(
                    or_(
                        ItemModel.zone != ConfigClass.CORE_ZONE_VALUE,
                        item_location_for_permissions.lquery(expression.cast(search_auth_user, LQUERY)),
                    )
                )

    if not await has_permission(
        ConfigClass.AUTH_SERVICE, project_code, 'file_any', 'greenroom', 'view', current_identity
    ):
        if not await has_permission(
            ConfigClass.AUTH_SERVICE, project_code, 'file_in_own_namefolder', 'greenroom', 'view', current_identity
        ):
            item_query = item_query.filter(ItemModel.zone != ConfigClass.GREENROOM_ZONE_VALUE)
        else:
            if searching_for_namefolders:
                item_query = item_query.filter(
                    or_(
                        ItemModel.zone != ConfigClass.GREENROOM_ZONE_VALUE,
                        ItemModel.name == current_identity['username'],
                    )
                )
            else:
                item_query = item_query.filter(
                    or_(
                        ItemModel.zone != ConfigClass.GREENROOM_ZONE_VALUE,
                        item_location_for_permissions.lquery(expression.cast(search_auth_user, LQUERY)),
                    )
                )
    return item_query
