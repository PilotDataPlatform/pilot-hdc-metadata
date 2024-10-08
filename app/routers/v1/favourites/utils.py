# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Union

from app.app_utils import construct_display_path
from app.models.sql_collections import CollectionsModel
from app.models.sql_favourites import FavouritesModel
from app.models.sql_items import ItemModel


def create_favourite_response(favourite: FavouritesModel, entity: Union[ItemModel, CollectionsModel]) -> dict:
    return {
        'id': str(favourite.item_id) if type(entity) is ItemModel else str(favourite.collection_id),
        'type': entity.type if type(entity) is ItemModel else 'collection',
        'name': entity.name,
        'display_path': (
            construct_display_path(entity.container_code, entity.zone, entity.parent_path)
            if type(entity) is ItemModel
            else entity.container_code
        ),
        'pinned': favourite.pinned,
    }


def combine_favourites_query_result(favourites_result: tuple, args: dict = None) -> dict:
    trimmed_favourites_result = []
    for entity in favourites_result:
        if entity is not None:
            trimmed_favourites_result.append(entity)
    return create_favourite_response(trimmed_favourites_result[0], trimmed_favourites_result[1])
