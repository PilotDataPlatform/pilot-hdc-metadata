# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
from datetime import datetime
from operator import or_
from uuid import UUID

from fastapi_sqlalchemy import db

from app.config import ConfigClass
from app.models.base_models import APIResponse
from app.models.models_collections import DELETECollectionItems
from app.models.models_collections import GETCollection
from app.models.models_collections import GETCollectionID
from app.models.models_collections import GETCollectionItems
from app.models.models_collections import POSTCollection
from app.models.models_collections import POSTCollectionItems
from app.models.models_collections import PUTCollections
from app.models.sql_collections import CollectionsModel
from app.models.sql_extended import ExtendedModel
from app.models.sql_favourites import FavouritesModel
from app.models.sql_items import ItemModel
from app.models.sql_items_collections import ItemsCollectionsModel
from app.models.sql_storage import StorageModel
from app.routers.router_exceptions import BadRequestException
from app.routers.router_exceptions import DuplicateRecordException
from app.routers.router_exceptions import EntityNotFoundException
from app.routers.router_utils import paginate
from app.routers.v1.collections.permissions_collections import collection_query_permissions
from app.routers.v1.items.utils import combine_collection_tables
from app.routers.v1.items.utils import combine_item_tables

from .utils import validate_collection


def check_collection_consistency(id_: UUID, container_code: str = None, owner: str = None) -> int:
    collection_query = db.session.query(CollectionsModel).filter(CollectionsModel.id == id_)
    collection = collection_query.first()
    if not collection:
        return 404
    if container_code and collection.container_code != container_code:
        return 422
    if owner and collection.owner != owner:
        return 403
    return 200


def get_user_collections(params: GETCollection, api_response: APIResponse):
    try:
        custom_sort = getattr(CollectionsModel, params.sorting).asc()
        if params.order == 'desc':
            custom_sort = getattr(CollectionsModel, params.sorting).desc()
    except Exception:
        raise BadRequestException(f'Cannot sort by {params.sorting}')

    collection_query = (
        db.session.query(CollectionsModel, FavouritesModel)
        .outerjoin(FavouritesModel)
        .filter(
            CollectionsModel.owner == params.owner,
            CollectionsModel.container_code == params.container_code,
            or_(FavouritesModel.user == params.owner, FavouritesModel.id.is_(None)),
        )
        .order_by(custom_sort)
    )

    paginate(params, api_response, collection_query, combine_collection_tables)


def get_collections_by_id(params: GETCollectionID, api_response: APIResponse):
    collection_query = db.session.query(CollectionsModel).filter(CollectionsModel.id == params.id)
    collection_result = collection_query.first()
    if collection_result:
        api_response.result = collection_result.to_dict()
        api_response.total = 1
    else:
        raise EntityNotFoundException(f'Collection id {params.id} does not exist')


async def get_items_per_collection(params: GETCollectionItems, api_response: APIResponse, current_identity: dict):
    collection = validate_collection(collection_id=params.id)

    try:
        custom_sort = getattr(ItemModel, params.sorting).asc()
        if params.order == 'desc':
            custom_sort = getattr(ItemModel, params.sorting).desc()
    except Exception:
        raise BadRequestException(f'Cannot sort by {params.sorting}')

    item_query = (
        db.session.query(ItemModel, StorageModel, ExtendedModel, FavouritesModel)
        .outerjoin(StorageModel, ExtendedModel, ItemsCollectionsModel, FavouritesModel)
        .filter(
            ItemsCollectionsModel.collection_id == params.id,
            ItemModel.status == params.status,
            or_(FavouritesModel.user == collection.owner, FavouritesModel.id.is_(None)),
        )
        .order_by(ItemModel.type, custom_sort)
    )
    item_query = await collection_query_permissions(
        params.container_code,
        current_identity,
        item_query,
    )

    paginate(params, api_response, item_query, combine_item_tables)


def create_collection(data: POSTCollection, api_response: APIResponse):
    collection_query = db.session.query(CollectionsModel).filter(
        CollectionsModel.owner == data.owner, CollectionsModel.container_code == data.container_code
    )
    collection_result = collection_query.all()
    if len(collection_result) == ConfigClass.MAX_COLLECTIONS:
        raise BadRequestException(f'Cannot create more than {ConfigClass.MAX_COLLECTIONS} collections')
    elif data.name in (collection.name for collection in collection_result):
        raise DuplicateRecordException(f'Collection {data.name} already exists')
    else:
        model_data = {'id_': data.id, 'owner': data.owner, 'container_code': data.container_code, 'name': data.name}
        collection = CollectionsModel(**model_data)
        db.session.add(collection)
        db.session.commit()
        db.session.refresh(collection)
        api_response.result = collection.to_dict()
        api_response.total = 1


def update_collection(data: PUTCollections, api_response: APIResponse):
    collections = {c.id: c.name for c in data.collections}

    query = db.session.query(CollectionsModel).filter(
        CollectionsModel.owner == data.owner, CollectionsModel.container_code == data.container_code
    )
    query_result = query.all()
    exist_collections = {c.id: c.name for c in query_result}

    for c_id in collections:
        if c_id not in exist_collections:
            raise EntityNotFoundException(f'Collection id: {c_id} does not exist')
        elif collections[c_id] in exist_collections.values():
            raise DuplicateRecordException(f'Collection name: {collections[c_id]} already exists')

    for collection in data.collections:
        db.session.merge(
            CollectionsModel(
                id_=collection.id,
                name=collection.name,
                container_code=data.container_code,
                owner=data.owner,
                last_updated_time=datetime.utcnow(),
            )
        )
        db.session.commit()

    result = json.loads(data.json())
    api_response.result = result
    api_response.total = len(data.collections)


def add_items(data: POSTCollectionItems, api_response: APIResponse):
    validate_collection(collection_id=data.id)
    for item_id in data.item_ids:
        db.session.merge(ItemsCollectionsModel(collection_id=data.id, item_id=item_id))
    db.session.commit()
    result = json.loads(data.json())
    api_response.result = result
    api_response.total = len(data.item_ids)


def remove_items(data: DELETECollectionItems):
    validate_collection(collection_id=data.id)
    db.session.query(ItemsCollectionsModel).filter(
        ItemsCollectionsModel.collection_id == data.id, ItemsCollectionsModel.item_id.in_(data.item_ids)
    ).delete(synchronize_session=False)

    db.session.commit()


def remove_collection(collection_id: UUID, api_response: APIResponse):
    validate_collection(collection_id=collection_id)
    db.session.query(CollectionsModel).filter(CollectionsModel.id == collection_id).delete()
    db.session.commit()
    api_response.total = 0
