# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import time
import uuid
from datetime import datetime
from typing import Tuple
from uuid import UUID

from fastapi_sqlalchemy import db
from sqlalchemy.sql import expression
from sqlalchemy_utils import Ltree
from sqlalchemy_utils.types.ltree import LQUERY

from app.app_utils import decode_path_from_ltree
from app.app_utils import encode_label_for_ltree
from app.app_utils import encode_path_for_ltree
from app.clients.kafka_client import KafkaProducerClient
from app.models.base_models import APIResponse
from app.models.models_items import GETItemsByIDs
from app.models.models_items import GETItemsByLocation
from app.models.models_items import ItemStatus
from app.models.models_items import PATCHItem
from app.models.models_items import POSTItem
from app.models.models_items import POSTItems
from app.models.models_items import PUTItem
from app.models.models_items import PUTItems
from app.models.models_items import PUTItemsBequeath
from app.models.models_lineage_provenance import TransformationType
from app.models.sql_attribute_templates import AttributeTemplateModel
from app.models.sql_extended import ExtendedModel
from app.models.sql_favourites import FavouritesModel
from app.models.sql_items import ItemModel
from app.models.sql_storage import StorageModel
from app.routers.router_exceptions import BadRequestException
from app.routers.router_exceptions import DuplicateRecordException
from app.routers.router_exceptions import EntityNotFoundException
from app.routers.router_utils import paginate
from app.routers.v1.favourites import crud_favourites
from app.routers.v1.items.crud_lineage_provenance import create_lineage
from app.routers.v1.items.crud_lineage_provenance import create_provenance
from app.routers.v1.items.permissions_items import search_permissions_filter
from app.routers.v1.items.utils import combine_item_tables
from app.routers.v1.items.utils import get_relative_path_depth
from app.routers.v1.items.utils import rename_folder_in_path


def check_item_consistency(id_: UUID, zone: int = None, container_code: str = None) -> int:
    item_query = db.session.query(ItemModel).filter(ItemModel.id == id_)
    item = item_query.first()
    if not item:
        return 404
    if (zone and item.zone != zone) or (container_code and item.container_code != container_code):
        return 400
    return 200


def get_available_file_name(
    container_code: UUID,
    zone: int,
    item_name: str,
    encoded_item_path: Ltree,
    status: ItemStatus,
) -> str:

    item = (
        db.session.query(ItemModel)
        .filter_by(
            container_code=container_code,
            zone=zone,
            name=item_name,
            parent_path=encoded_item_path,
            status=status,
        )
        .first()
    )

    if not item:
        return item_name
    item_extension = ''
    if '.' in item_name:
        item_name_split = item_name.split('.', 1)
        item_name = item_name_split[0]
        item_extension = '.' + item_name_split[1]
    timestamp = round(time.time())
    item_name_new = f'{item_name}_{timestamp}{item_extension}'
    return item_name_new


def get_item_children(root_item: ItemModel, group_by_depth: bool = False) -> dict:
    search_path = (
        f'{root_item.restore_path}.{encode_label_for_ltree(root_item.name)}.*'
        if root_item.status == ItemStatus.ARCHIVED
        else f'{root_item.parent_path}.{encode_label_for_ltree(root_item.name)}.*'
    )
    children_item_query = (
        db.session.query(ItemModel, StorageModel, ExtendedModel)
        .join(StorageModel, ExtendedModel)
        .filter(
            ItemModel.container_code == root_item.container_code,
            ItemModel.zone == root_item.zone,
            ItemModel.status == root_item.status,
            ItemModel.restore_path.lquery(expression.cast(search_path, LQUERY))
            if root_item.status == ItemStatus.ARCHIVED
            else ItemModel.parent_path.lquery(expression.cast(search_path, LQUERY)),
        )
    )
    children = children_item_query.all()
    if not group_by_depth:
        return children
    layers = {}
    for item in children:
        depth = get_relative_path_depth(root_item, item[0])
        if depth not in layers:
            layers[depth] = []
        layers[depth].append(item)
    return layers


def move_item(item: ItemModel, new_parent_path: str, children: dict = None, depth: int = 1):
    if not children:
        children = get_item_children(item, True)
    item.parent_path = Ltree(encode_path_for_ltree(new_parent_path)) if new_parent_path else None
    if depth not in children:
        return
    layer = children[depth]
    for child in layer:
        move_item(child[0], f'{new_parent_path}/{item.name}' if new_parent_path else item.name, children, depth + 1)


def rename_item(
    root_item: ItemModel, item: ItemModel, old_name: str, new_name: str, children: dict = None, depth: int = 1
):
    if not children:
        children = get_item_children(item, True)
    if item == root_item:
        item.name = new_name
    else:
        rename_folder_in_path(root_item, item)
    if depth not in children:
        return
    layer = children[depth]
    for child in layer:
        rename_item(root_item, child[0], old_name, new_name, children, depth + 1)


def attributes_match_template(attributes: dict, template_id: UUID) -> bool:
    if not template_id and not attributes:
        return True
    try:
        attribute_template = db.session.query(AttributeTemplateModel).filter_by(id=template_id).first().to_dict()
        if len(attributes) > len(attribute_template['attributes']):
            return False
        for format_ in attribute_template['attributes']:
            if not format_['optional']:
                input_value = attributes[format_['name']]
                if 'options' in format_:
                    if format_['options']:
                        if input_value not in format_['options']:
                            return False
        return True
    except Exception:
        return False


def get_item_by_id(item_id: UUID) -> Tuple[ItemModel, StorageModel, ExtendedModel]:
    item_query = (
        db.session.query(ItemModel, StorageModel, ExtendedModel)
        .join(StorageModel, ExtendedModel)
        .filter(ItemModel.id == item_id)
    )
    item_result = item_query.first()
    if not item_result:
        raise EntityNotFoundException()
    return item_result


def get_item_by_location(params: GETItemsByLocation):
    item_query = (
        db.session.query(ItemModel, StorageModel, ExtendedModel)
        .join(StorageModel, ExtendedModel)
        .filter(
            ItemModel.name == params.name,
            ItemModel.parent_path == Ltree(encode_path_for_ltree(params.parent_path)),
            ItemModel.container_code == params.container_code,
            ItemModel.container_type == params.container_type,
            ItemModel.zone == params.zone,
            ItemModel.status == params.status,
        )
    )
    item_result = item_query.first()
    if item_result:
        return combine_item_tables(item_result)
    else:
        raise EntityNotFoundException()


def get_items_by_ids(params: GETItemsByIDs, ids: list[UUID], api_response: APIResponse):
    item_query = (
        db.session.query(ItemModel, StorageModel, ExtendedModel)
        .join(StorageModel, ExtendedModel)
        .filter(ItemModel.id.in_(ids))
    )
    paginate(params, api_response, item_query, combine_item_tables)


async def get_items_by_location(  # noqa: C901
    params: GETItemsByLocation, api_response: APIResponse, current_identity: dict
):
    if params.type and params.type not in ['name_folder', 'folder', 'file']:
        raise BadRequestException(f'Invalid type {params.type}')
    if params.container_type and params.container_type not in ['project', 'dataset']:
        raise BadRequestException(f'Invalid container_type {params.container_type}')
    try:
        custom_sort = getattr(ItemModel, params.sorting).asc()
        if params.order == 'desc':
            custom_sort = getattr(ItemModel, params.sorting).desc()
    except Exception:
        raise BadRequestException(f'Cannot sort by {params.sorting}')

    item_query = db.session.query(ItemModel, StorageModel, ExtendedModel).join(StorageModel, ExtendedModel)
    if params.fav_user:
        item_query = db.session.query(ItemModel, StorageModel, ExtendedModel, FavouritesModel).outerjoin(
            StorageModel, ExtendedModel, FavouritesModel
        )
    item_query = item_query.filter(
        ItemModel.status == params.status,
    ).order_by(ItemModel.type, custom_sort)

    if params.container_code:
        item_query = item_query.filter(ItemModel.container_code == params.container_code)
    if params.zone is not None:
        item_query = item_query.filter(ItemModel.zone == params.zone)
    if params.name:
        item_query = item_query.filter(ItemModel.name.ilike(f'%{params.name}%'))
    if params.owner:
        item_query = item_query.filter(ItemModel.owner.like(params.owner))
    if params.type:
        item_query = item_query.filter(ItemModel.type == params.type)
    if params.container_type:
        item_query = item_query.filter(ItemModel.container_type == params.container_type)

    if params.container_type != 'dataset':
        item_query = await search_permissions_filter(
            item_query,
            current_identity,
            params,
        )

    if params.parent_path:
        search_path = encode_path_for_ltree(params.parent_path)
        if params.recursive:
            search_path += '.*'
        item_query = item_query.filter(ItemModel.parent_path.lquery(expression.cast(search_path, LQUERY)))
    else:
        if not params.recursive:
            item_query = item_query.filter(ItemModel.parent_path.is_(None))
    if params.restore_path:
        search_path = encode_path_for_ltree(params.restore_path)
        if params.recursive:
            search_path += '.*'
        item_query = item_query.filter(ItemModel.restore_path.lquery(expression.cast(search_path, LQUERY)))
    if params.last_updated_start:
        item_query = item_query.filter(ItemModel.last_updated_time >= params.last_updated_start)
    if params.last_updated_end:
        item_query = item_query.filter(ItemModel.last_updated_time <= params.last_updated_end)

    paginate(params, api_response, item_query, combine_item_tables, fav_user=params.fav_user)


def create_item(data: POSTItem, kafka_client: KafkaProducerClient) -> dict:
    def create_lineage_provenance(
        transformation_type: TransformationType, consumed_item_id: UUID, produced_item: ItemModel
    ) -> None:
        lineage_id = None
        if transformation_type == TransformationType.COPY_TO_ZONE:
            lineage_id = create_lineage(
                consumes=[consumed_item_id], produces=[produced_item.id], tfrm_type=transformation_type
            )
            consumed_item = get_item_by_id(consumed_item_id)[0]
            create_provenance(
                lineage_id=lineage_id,
                item_id=consumed_item.id,
                parent=consumed_item.parent,
                parent_path=consumed_item.parent_path,
                status=consumed_item.status,
                type_=consumed_item.type,
                zone=consumed_item.zone,
                name=consumed_item.name,
                size=consumed_item.size,
                owner=consumed_item.owner,
                container_code=consumed_item.container_code,
                container_type=consumed_item.container_type,
            )
        create_provenance(
            lineage_id=lineage_id,
            item_id=produced_item.id,
            parent=produced_item.parent,
            parent_path=produced_item.parent_path,
            status=produced_item.status,
            type_=produced_item.type,
            zone=produced_item.zone,
            name=produced_item.name,
            size=produced_item.size,
            owner=produced_item.owner,
            container_code=produced_item.container_code,
            container_type=produced_item.container_type,
        )

    if not attributes_match_template(data.attributes, data.attribute_template_id):
        raise BadRequestException('Attributes do not match attribute template')
    if data.type == 'file' and data.status == ItemStatus.ACTIVE:
        raise BadRequestException('Can not create file as active status.')
    item_model_data = {
        'id_': data.id if data.id else uuid.uuid4(),
        'parent': data.parent if data.parent else None,
        'parent_path': Ltree(f'{encode_path_for_ltree(data.parent_path)}') if data.parent_path else None,
        'status': data.status,
        'type_': data.type,
        'zone': data.zone,
        'name': data.name,
        'size': data.size,
        'owner': data.owner,
        'container_code': data.container_code,
        'container_type': data.container_type,
    }
    item = ItemModel(**item_model_data)
    storage_model_data = {
        'item_id': item.id,
        'location_uri': data.location_uri,
        'version': data.version,
        'upload_id': data.upload_id,
    }
    storage = StorageModel(**storage_model_data)
    extended_model_data = {
        'item_id': item.id,
        'extra': {
            'tags': data.tags,
            'system_tags': data.system_tags,
            'attributes': {str(data.attribute_template_id): data.attributes} if data.attributes else {},
        },
    }
    extended = ExtendedModel(**extended_model_data)
    try:
        db.session.add_all([item, storage, extended])
        db.session.commit()
        db.session.refresh(item)
        db.session.refresh(storage)
        db.session.refresh(extended)
    except Exception:
        raise DuplicateRecordException
    combined_item = combine_item_tables((item, storage, extended))
    if kafka_client:
        kafka_client.send(combined_item)

    create_lineage_provenance(transformation_type=data.tfrm_type, consumed_item_id=data.tfrm_source, produced_item=item)

    return combined_item


def create_items(data: POSTItems, kafka_client: KafkaProducerClient, api_response: APIResponse):
    results = []
    for item in data.items:
        try:
            results.append(create_item(item, kafka_client))
        except DuplicateRecordException as e:
            if data.skip_duplicates:
                pass
            else:
                raise e
    api_response.result = results
    api_response.total = len(results)


def update_item(item_id: UUID, data: PUTItem, kafka_client: KafkaProducerClient) -> dict:  # noqa: C901
    item = db.session.query(ItemModel).filter_by(id=item_id).first()
    if not item:
        raise EntityNotFoundException()
    if item.status == ItemStatus.REGISTERED and (data.status is None or data.status == ItemStatus.REGISTERED):
        raise BadRequestException('Cannot update attribute of a REGISTERED item')

    if data.parent != '':
        item.parent = data.parent if data.parent else None
    if data.parent_path != '' and item.status == ItemStatus.ACTIVE:
        move_item(item, data.parent_path)
    if data.type:
        item.type = data.type
    if data.status:
        item.status = data.status
    if data.zone:
        item.zone = data.zone
    if data.name and item.status == ItemStatus.ACTIVE:
        rename_item(item, item, item.name, data.name)
    if data.size:
        item.size = data.size
    if data.owner:
        item.owner = data.owner
    if data.container_code:
        item.container_code = data.container_code
    if data.container_type:
        item.container_type = data.container_type
    item.last_updated_time = datetime.utcnow()
    storage = db.session.query(StorageModel).filter_by(item_id=item_id).first()
    if data.location_uri:
        storage.location_uri = data.location_uri
    if data.version:
        storage.version = data.version
    extended = db.session.query(ExtendedModel).filter_by(item_id=item_id).first()
    extra = dict(extended.extra)
    if data.tags is not None:
        extra['tags'] = data.tags
    if data.system_tags is not None:
        extra['system_tags'] = data.system_tags
    if data.attribute_template_id and data.attributes:
        if not attributes_match_template(data.attributes, data.attribute_template_id):
            raise BadRequestException('Attributes do not match attribute template')
        extra['attributes'] = {str(data.attribute_template_id): data.attributes} if data.attributes else {}
    if extra != extended.extra:
        extended.extra = extra
    db.session.commit()
    db.session.refresh(item)
    db.session.refresh(storage)
    db.session.refresh(extended)
    combined_item = combine_item_tables((item, storage, extended))
    if kafka_client:
        kafka_client.send(combined_item)
    create_provenance(
        lineage_id=None,
        item_id=item.id,
        parent=item.parent,
        parent_path=item.parent_path,
        status=item.status,
        type_=item.type,
        zone=item.zone,
        name=item.name,
        size=item.size,
        owner=item.owner,
        container_code=item.container_code,
        container_type=item.container_type,
    )
    return combined_item


def update_items(ids: list[UUID], data: PUTItems, kafka_client: KafkaProducerClient, api_response: APIResponse):
    results = []
    for i in range(0, len(ids)):
        results.append(update_item(ids[i], data.items[i], kafka_client))
    api_response.result = results
    api_response.total = len(results)


def get_restore_destination_id(container_code: str, zone: int, restore_path: Ltree) -> UUID:
    decoded_restore_path = decode_path_from_ltree(restore_path)
    destination_name = decoded_restore_path
    destination_path = None
    decoded_restore_path_labels = decoded_restore_path.split('/')
    if len(decoded_restore_path_labels) > 1:
        destination_name = decoded_restore_path_labels[-1]
        destination_path = '/'.join(decoded_restore_path_labels[:-1])
    destination_query = db.session.query(ItemModel).filter(
        ItemModel.container_code == container_code,
        ItemModel.zone == zone,
        ItemModel.status == ItemStatus.ACTIVE,
        ItemModel.name == destination_name,
    )
    if destination_path:
        destination_query = destination_query.filter(
            ItemModel.parent_path.lquery(expression.cast(encode_path_for_ltree(destination_path), LQUERY))
        )
    destination = destination_query.first()
    if destination:
        return destination.id


def archive_item(item: ItemModel, trash_item: ItemStatus, root_item: ItemModel = None):
    if item.status != trash_item:
        if trash_item == ItemStatus.ARCHIVED:
            if not root_item:
                item.name = get_available_file_name(
                    item.container_code, item.zone, item.name, None, ItemStatus.ARCHIVED
                )
                item.parent = None
            else:
                rename_folder_in_path(root_item, item)
            item.restore_path = item.parent_path
        else:
            if not root_item:

                item_file_name = get_available_file_name(
                    item.container_code, item.zone, item.name, item.restore_path, ItemStatus.ACTIVE
                )

                restore_destination_id = get_restore_destination_id(item.container_code, item.zone, item.restore_path)

                if not restore_destination_id:

                    raise BadRequestException('Restore destination does not exist')
                item.parent = restore_destination_id
                item.name = item_file_name
            else:
                rename_folder_in_path(root_item, item, ItemStatus.ARCHIVED)
            item.parent_path = item.restore_path
            item.restore_path = None
        item.status = trash_item
        item.last_updated_time = datetime.utcnow()
        lineage_id = create_lineage(consumes=[item.id], produces=None, tfrm_type=TransformationType.ARCHIVE)
        create_provenance(
            lineage_id=lineage_id,
            item_id=item.id,
            parent=item.parent,
            parent_path=item.parent_path,
            status=item.status,
            type_=item.type,
            zone=item.zone,
            name=item.name,
            size=item.size,
            owner=item.owner,
            container_code=item.container_code,
            container_type=item.container_type,
        )


def archive_item_by_id(params: PATCHItem, kafka_client: KafkaProducerClient, api_response: APIResponse):  # noqa: C901
    root_item_query = (
        db.session.query(ItemModel, StorageModel, ExtendedModel)
        .join(StorageModel, ExtendedModel)
        .filter(ItemModel.id == params.id)
    )
    root_item_result = root_item_query.first()
    if not root_item_result:
        raise EntityNotFoundException()
    if root_item_result[0].type == 'name_folder':
        raise BadRequestException('Name folders cannot be archived or restored')
    children_result = []
    if root_item_result[0].type == 'folder':
        children_result = get_item_children(root_item_result[0])
    all_items = []

    try:
        archive_item(root_item_result[0], params.status)
        all_items.append(root_item_result)
        for child in children_result:
            archive_item(child[0], params.status, root_item_result[0])
            all_items.append(child)
        if params.status == ItemStatus.ARCHIVED:
            move_item(root_item_result[0], None)
    except BadRequestException:

        raise
    db.session.commit()
    results = []
    for item in all_items:
        db.session.refresh(item[0])
        combined_item = combine_item_tables(item)
        results.append(combined_item)
        if kafka_client:
            kafka_client.send(combined_item)
    api_response.result = results
    api_response.total = len(results)
    if params.status == ItemStatus.ARCHIVED:
        item_ids_to_remove_from_favourites = []
        for item in all_items:
            item_ids_to_remove_from_favourites.append(str(item[0].id))
        crud_favourites.delete_favourites_for_all_users(item_ids_to_remove_from_favourites, 'item')


def delete_item_by_id(id_: UUID, kafka_client: KafkaProducerClient, api_response: APIResponse):
    del_items = []
    root_item_query = (
        db.session.query(ItemModel, StorageModel, ExtendedModel)
        .join(StorageModel, ExtendedModel)
        .filter(ItemModel.id == id_)
    )
    root_item_result = root_item_query.first()
    if not root_item_result:
        raise EntityNotFoundException()
    del_items.append(combine_item_tables(root_item_result))
    if root_item_result[0].type == 'folder':
        children_result = get_item_children(root_item_result[0])
        for child in children_result:
            del_items.append(combine_item_tables(child))
            for row in child:
                db.session.delete(row)
    for row in root_item_result:
        db.session.delete(row)
    db.session.commit()
    for item in del_items:
        item['to_delete'] = True
        if kafka_client:
            kafka_client.send(item)
    api_response.total = 0


def delete_items_by_ids(ids: list[UUID], kafka_client: KafkaProducerClient, api_response: APIResponse):
    for id_ in ids:
        delete_item_by_id(id_, kafka_client, api_response)


def bequeath_to_children(
    id_: UUID, data: PUTItemsBequeath, kafka_client: KafkaProducerClient, api_response: APIResponse
):
    if not attributes_match_template(data.attributes, data.attribute_template_id):
        raise BadRequestException('Attributes do not match attribute template')
    root_item_query = (
        db.session.query(ItemModel, StorageModel, ExtendedModel)
        .join(StorageModel, ExtendedModel)
        .filter(ItemModel.id == id_)
    )
    root_item_result = root_item_query.first()
    if not root_item_result:
        raise EntityNotFoundException()
    if root_item_result[0].type != 'folder':
        raise BadRequestException('Properties can only be bequeathed from folders')
    children_result = get_item_children(root_item_result[0])
    results = []
    for child in children_result:
        extra = dict(child[2].extra)
        if data.attribute_template_id and data.attributes:
            extra['attributes'] = {str(data.attribute_template_id): data.attributes} if data.attributes else {}
        if data.system_tags:
            extra['system_tags'] = data.system_tags
        child[2].extra = extra
    db.session.commit()
    for child in children_result:
        db.session.refresh(child[2])
        combined_item = combine_item_tables(child)
        results.append(combined_item)
        if kafka_client:
            kafka_client.send(combined_item)
    api_response.result = results
    api_response.total = len(results)
