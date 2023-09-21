# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from sqlalchemy_utils import Ltree

from app.app_utils import decode_path_from_ltree
from app.app_utils import encode_path_for_ltree
from app.models.models_items import ItemStatus
from app.models.sql_items import ItemModel


def combine_item_tables(item_result: tuple, args: dict = None) -> dict:
    item_data = item_result[0].to_dict()
    storage_data = item_result[1].to_dict()
    storage_data.pop('item_id')
    extended_data = item_result[2].to_dict()
    extended_data.pop('item_id')
    item_data['storage'] = storage_data
    item_data['extended'] = extended_data
    item_data['favourite'] = False
    if args and args.get('fav_user'):
        if len(item_result) == 4 and item_result[3] and item_result[3].user == args['fav_user']:
            item_data['favourite'] = True
    return item_data


def combine_collection_tables(collection_result: tuple, args: dict = None) -> dict:
    collection_data = collection_result[0].to_dict()
    collection_data['favourite'] = True if len(collection_result) == 2 and collection_result[1] else False
    return collection_data


def get_path_depth(item: ItemModel) -> int:
    return len(decode_path_from_ltree(item.parent_path).split('/'))


def get_relative_path_depth(parent: ItemModel, child: ItemModel) -> int:
    return get_path_depth(child) - get_path_depth(parent)


def rename_folder_in_path(renamed_folder: ItemModel, item_to_repath: ItemModel, status: ItemStatus = ItemStatus.ACTIVE):
    decoded_parent_path = (
        decode_path_from_ltree(item_to_repath.restore_path)
        if status == ItemStatus.ARCHIVED
        else decode_path_from_ltree(item_to_repath.parent_path)
    )
    root_item_depth = get_path_depth(renamed_folder)
    labels = decoded_parent_path.split('/')
    labels[root_item_depth] = renamed_folder.name
    new_parent_path = '/'.join(labels)
    if status == ItemStatus.ARCHIVED:
        item_to_repath.restore_path = Ltree(encode_path_for_ltree(new_parent_path))
    else:
        item_to_repath.parent_path = Ltree(encode_path_for_ltree(new_parent_path))
