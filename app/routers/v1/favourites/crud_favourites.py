# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from fastapi_sqlalchemy import db
from sqlalchemy import or_

from app.models.base_models import APIResponse
from app.models.models_favourites import DELETEFavourites
from app.models.models_favourites import GETFavourite
from app.models.models_favourites import PATCHFavourites
from app.models.models_favourites import POSTFavourite
from app.models.models_items import ItemStatus
from app.models.sql_collections import CollectionsModel
from app.models.sql_favourites import FavouritesModel
from app.models.sql_items import ItemModel
from app.routers.router_exceptions import BadRequestException
from app.routers.router_exceptions import DuplicateRecordException
from app.routers.router_exceptions import EntityNotFoundException
from app.routers.router_exceptions import UnauthorizedException
from app.routers.v1.collections import crud_collections
from app.routers.v1.favourites.utils import combine_favourites_query_result
from app.routers.v1.favourites.utils import create_favourite_response
from app.routers.v1.items import crud_items

from ...router_utils import paginate


def get_favourites_by_user(params: GETFavourite, api_response: APIResponse):
    try:
        custom_sort = getattr(FavouritesModel, params.sorting).asc()
        if params.order == 'desc':
            custom_sort = getattr(FavouritesModel, params.sorting).desc()
    except Exception:
        raise BadRequestException(f'Cannot sort by {params.sorting}')
    favourites_query = (
        db.session.query(FavouritesModel, ItemModel, CollectionsModel)
        .outerjoin(ItemModel, CollectionsModel)
        .filter(
            FavouritesModel.user == params.user,
            or_(ItemModel.status == ItemStatus.ACTIVE, CollectionsModel.id is not None),
        )
        .order_by(FavouritesModel.pinned.desc(), custom_sort)
    )
    paginate(params, api_response, favourites_query, combine_favourites_query_result)


def create_favourite(data: POSTFavourite) -> dict:
    input_validation = (
        crud_items.check_item_consistency(data.id, data.zone, data.container_code)
        if data.type == 'item'
        else crud_collections.check_collection_consistency(data.id, data.container_code, data.user)
    )
    if input_validation == 403:
        raise UnauthorizedException(f'{data.user} does not own {data.type} {data.id}')
    elif input_validation == 404:
        raise EntityNotFoundException(f'{data.type.capitalize()} {data.id} not found')
    elif input_validation == 400:
        raise BadRequestException(f'{data.type.capitalize()} {data.id} not found with given parameters')
    favourite_model_data = {
        'user': data.user,
        'item_id': data.id if data.type == 'item' else None,
        'collection_id': data.id if data.type == 'collection' else None,
        'pinned': False,
    }
    model = ItemModel if favourite_model_data['item_id'] else CollectionsModel
    entity_exists_query = db.session.query(model).filter(model.id == data.id)
    entity = entity_exists_query.first()
    if type(entity) == ItemModel:
        if entity.status != ItemStatus.ACTIVE:
            raise BadRequestException('Cannot favourite an archived or incompleted item')
        if entity.type == 'name_folder':
            raise BadRequestException('Cannot favourite an item of type name_folder')
    if not entity:
        raise EntityNotFoundException(f'{data.type.capitalize()} {data.id} not found')
    favourite = FavouritesModel(**favourite_model_data)
    try:
        db.session.add(favourite)
        db.session.commit()
        db.session.refresh(favourite)
    except Exception:
        raise DuplicateRecordException
    return create_favourite_response(favourite, entity)


def pin_unpin_favourite_by_user_and_entity_id(user: str, id_: UUID, type_: str, pinned: bool):
    favourite_query = (
        db.session.query(FavouritesModel, ItemModel, CollectionsModel)
        .outerjoin(ItemModel, CollectionsModel)
        .filter(
            FavouritesModel.item_id == id_ if type_ == 'item' else FavouritesModel.collection_id == id_,
            FavouritesModel.user == user,
        )
    )
    favourites_result = favourite_query.first()
    if not favourites_result:
        raise EntityNotFoundException(f'{type_.capitalize()} {id} not found')
    favourites_result[0].pinned = pinned
    db.session.commit()
    db.session.refresh(favourites_result[0])
    return combine_favourites_query_result(favourites_result)


def bulk_pin_unpin_favourites(user: str, data: PATCHFavourites, api_response: APIResponse):
    results = []
    for favourite in data.favourites:
        try:
            results.append(
                pin_unpin_favourite_by_user_and_entity_id(user, favourite.id, favourite.type, favourite.pinned)
            )
        except EntityNotFoundException as e:
            raise e
    api_response.result = results
    api_response.total = len(results)


def delete_favourites_for_all_users(ids: list[str], type_: str):
    favourite_query = db.session.query(FavouritesModel).filter(
        FavouritesModel.item_id.in_(ids) if type_ == 'item' else FavouritesModel.collection_id.in_(ids)
    )
    favourites = favourite_query.all()
    for favourite in favourites:
        db.session.delete(favourite)
        db.session.commit()


def delete_favourite_by_user_and_entity_id(id_: UUID, user: str, type_: str, api_response: APIResponse):
    favourite_query = db.session.query(FavouritesModel).filter(
        FavouritesModel.item_id == id_ if type_ == 'item' else FavouritesModel.collection_id == id_,
        FavouritesModel.user == user,
    )
    favourite = favourite_query.first()
    if not favourite:
        raise EntityNotFoundException(f'{type_.capitalize()} {id_} not found')
    db.session.delete(favourite)
    db.session.commit()
    api_response.total = 0


def bulk_delete_favourites(user: str, data: DELETEFavourites, api_response: APIResponse):
    for favourite in data.favourites:
        delete_favourite_by_user_and_entity_id(favourite.id, user, favourite.type, api_response)
