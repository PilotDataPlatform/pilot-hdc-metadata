# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv

from app.clients.kafka_client import KafkaProducerClient
from app.clients.kafka_client import get_kafka_client
from app.models.base_models import EAPIResponseCode
from app.models.models_items import DELETEItem
from app.models.models_items import DELETEItemResponse
from app.models.models_items import GETItem
from app.models.models_items import GETItemByLocation
from app.models.models_items import GETItemResponse
from app.models.models_items import GETItemsByIDs
from app.models.models_items import GETItemsByLocation
from app.models.models_items import PATCHItem
from app.models.models_items import PATCHItemResponse
from app.models.models_items import POSTItem
from app.models.models_items import POSTItemResponse
from app.models.models_items import POSTItems
from app.models.models_items import PUTItem
from app.models.models_items import PUTItemResponse
from app.models.models_items import PUTItems
from app.models.models_items import PUTItemsBequeath
from app.models.models_items import PUTItemsBequeathResponse
from app.routers.router_exceptions import BadRequestException
from app.routers.router_exceptions import DuplicateRecordException
from app.routers.router_exceptions import EntityNotFoundException
from app.routers.router_utils import set_api_response_error
from app.routers.v1.items.utils import combine_item_tables

from .crud_items import archive_item_by_id
from .crud_items import bequeath_to_children
from .crud_items import create_item
from .crud_items import create_items
from .crud_items import delete_item_by_id
from .crud_items import delete_items_by_ids
from .crud_items import get_item_by_id
from .crud_items import get_item_by_location
from .crud_items import get_items_by_ids
from .crud_items import get_items_by_location
from .crud_items import get_marked_items_by_username
from .crud_items import mark_delete_item_by_id
from .crud_items import mark_restore_item_by_id
from .crud_items import update_item
from .crud_items import update_items
from .dependencies import jwt_required

router = APIRouter()
router_bulk = APIRouter()


@cbv(router)
class APIItems:
    @router.get('/{id}/', response_model=GETItemResponse, summary='Get an item by ID or check if an item exists')
    async def get_item(self, params: GETItem = Depends()) -> JSONResponse:
        try:
            api_response = GETItemResponse()
            api_response.result = combine_item_tables(get_item_by_id(params.id))
        except Exception:
            set_api_response_error(api_response, f'Failed to get item with id {params.id}', EAPIResponseCode.not_found)
        return api_response.json_response()

    @router.get('/', response_model=GETItemResponse, summary='Get zero or one item(s) by location')
    async def get_item_by_location(self, params: GETItemByLocation = Depends()) -> JSONResponse:
        try:
            api_response = GETItemResponse()
            api_response.result = get_item_by_location(params)
        except Exception:
            set_api_response_error(api_response, 'Failed to get item', EAPIResponseCode.not_found)
        return api_response.json_response()

    @router.post('/', response_model=POSTItemResponse, summary='Create a new item')
    async def create_item(
        self, data: POSTItem, kafka_client: KafkaProducerClient = Depends(get_kafka_client)
    ) -> JSONResponse:
        try:
            api_response = POSTItemResponse()
            api_response.result = create_item(data, kafka_client)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except DuplicateRecordException:
            set_api_response_error(api_response, 'Item conflict in database', EAPIResponseCode.conflict)
        except Exception:
            set_api_response_error(api_response, 'Failed to create item', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router.put('/', response_model=PUTItemResponse, summary='Update an item')
    async def update_item(
        self,
        data: PUTItem,
        id_: UUID = Query(None, alias='id'),
        kafka_client: KafkaProducerClient = Depends(get_kafka_client),
    ) -> JSONResponse:
        try:
            api_response = PUTItemResponse()
            api_response.result = update_item(id_, data, kafka_client)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except EntityNotFoundException:
            set_api_response_error(api_response, f'Failed to get item with id {id_}', EAPIResponseCode.not_found)
        except Exception:
            set_api_response_error(api_response, 'Failed to update item', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router.patch('/', response_model=PATCHItemResponse, summary='Move an item to or out of the trash')
    async def trash_item(
        self, params: PATCHItem = Depends(), kafka_client: KafkaProducerClient = Depends(get_kafka_client)
    ) -> JSONResponse:
        try:
            api_response = PATCHItemResponse()
            archive_item_by_id(params, kafka_client, api_response)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except EntityNotFoundException:
            set_api_response_error(api_response, f'Failed to get item with id {params.id}', EAPIResponseCode.not_found)
        except Exception:
            set_api_response_error(api_response, 'Failed to archive item', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router.delete('/', response_model=DELETEItemResponse, summary='Permanently delete an item')
    async def delete_item(
        self, params: DELETEItem = Depends(), kafka_client: KafkaProducerClient = Depends(get_kafka_client)
    ) -> JSONResponse:
        try:
            api_response = DELETEItemResponse()
            delete_item_by_id(params.id, kafka_client, api_response)
        except EntityNotFoundException:
            set_api_response_error(api_response, f'Failed to get item with id {params.id}', EAPIResponseCode.not_found)
        except Exception:
            set_api_response_error(api_response, 'Failed to delete item', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router.delete('/mark/')
    async def mark_item_deleted(
        self, id_: UUID = Query(None, alias='id'), current_identity: dict = Depends(jwt_required)
    ) -> JSONResponse:
        try:
            api_response = DELETEItemResponse()
            mark_delete_item_by_id(id_, current_identity['username'])
        except EntityNotFoundException:
            set_api_response_error(api_response, f'Failed to get item with id {id_}', EAPIResponseCode.not_found)
        except Exception:
            set_api_response_error(api_response, 'Failed to mark item as deleted', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router.put('/mark/')
    async def mark_item_restore(
        self, id_: UUID = Query(None, alias='id'), current_identity: dict = Depends(jwt_required)
    ) -> JSONResponse:
        try:
            api_response = PUTItemResponse()
            mark_restore_item_by_id(id_)
        except EntityNotFoundException:
            set_api_response_error(api_response, f'Failed to get item with id {id_}', EAPIResponseCode.not_found)
        except Exception:
            set_api_response_error(api_response, 'Failed to mark item as deleted', EAPIResponseCode.internal_error)
        return api_response.json_response()


@cbv(router_bulk)
class APIItemsBulk:
    @router_bulk.get('/batch/', response_model=GETItemResponse, summary='Get many items by IDs')
    async def get_items_by_ids(self, ids: list[UUID] = Query(None), params: GETItemsByIDs = Depends()) -> JSONResponse:
        try:
            api_response = GETItemResponse()
            get_items_by_ids(params, ids, api_response)
        except Exception:
            set_api_response_error(api_response, 'Failed to get item', EAPIResponseCode.not_found)
        return api_response.json_response()

    @router_bulk.get('/search/', response_model=GETItemResponse, summary='Get all items by location')
    async def get_items_by_location(
        self, params: GETItemsByLocation = Depends(), current_identity: dict = Depends(jwt_required)
    ) -> JSONResponse:
        try:
            api_response = GETItemResponse()
            await get_items_by_location(params, api_response, current_identity)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except Exception:
            set_api_response_error(api_response, 'Failed to get item', EAPIResponseCode.not_found)
        return api_response.json_response()

    @router_bulk.post('/batch/', response_model=POSTItemResponse, summary='Create many new items')
    async def create_items(
        self, data: POSTItems, kafka_client: KafkaProducerClient = Depends(get_kafka_client)
    ) -> JSONResponse:
        try:
            api_response = POSTItemResponse()
            create_items(data, kafka_client, api_response)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except DuplicateRecordException:
            set_api_response_error(api_response, 'Item conflict in database', EAPIResponseCode.conflict)
        except Exception as e:
            set_api_response_error(api_response, f'Failed to create items: {e}', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router_bulk.put('/batch/', response_model=PUTItemResponse, summary='Update many items')
    async def update_items(
        self,
        data: PUTItems,
        ids: list[UUID] = Query(None),
        kafka_client: KafkaProducerClient = Depends(get_kafka_client),
    ) -> JSONResponse:
        try:
            api_response = PUTItemResponse()
            if len(data.items) != len(ids):
                raise BadRequestException('Number of IDs does not match number of update data')
            update_items(ids, data, kafka_client, api_response)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except Exception as e:
            set_api_response_error(api_response, f'Failed to update items: {e}', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router_bulk.delete('/batch/', response_model=DELETEItemResponse, summary='Permanently delete many items by IDs')
    async def delete_items_by_ids(
        self, ids: list[UUID] = Query(None), kafka_client: KafkaProducerClient = Depends(get_kafka_client)
    ) -> JSONResponse:
        try:
            api_response = DELETEItemResponse()
            delete_items_by_ids(ids, kafka_client, api_response)
        except Exception:
            set_api_response_error(api_response, 'Failed to delete items', EAPIResponseCode.not_found)
        return api_response.json_response()

    @router_bulk.delete('/mark/')
    async def mark_items_deleted(
        self, ids: list[UUID] = Query(None), current_identity: dict = Depends(jwt_required)
    ) -> JSONResponse:
        try:
            api_response = DELETEItemResponse()
            for id_ in ids:
                mark_delete_item_by_id(id_, current_identity['username'])
        except EntityNotFoundException:
            set_api_response_error(api_response, 'One or more items not found', EAPIResponseCode.not_found)
        except Exception:
            set_api_response_error(api_response, 'Failed to mark items as deleted', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router_bulk.get('/mark/')
    async def get_items_mark(self, current_identity: dict = Depends(jwt_required)) -> JSONResponse:
        try:
            api_response = GETItemResponse()
            result = get_marked_items_by_username(current_identity['username'])
            api_response.result = [combine_item_tables(item) for item in result]
        except Exception:
            set_api_response_error(api_response, 'Failed to get marked items', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router_bulk.put(
        '/batch/bequeath/',
        response_model=PUTItemsBequeathResponse,
        summary='Bequeath properties to a folder\'s children',
    )
    async def update_items_bequeath(
        self,
        data: PUTItemsBequeath,
        id_: UUID = Query(None, alias='id'),
        kafka_client: KafkaProducerClient = Depends(get_kafka_client),
    ) -> JSONResponse:
        try:
            api_response = PUTItemsBequeathResponse()
            bequeath_to_children(id_, data, kafka_client, api_response)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except Exception:
            set_api_response_error(api_response, f'Failed to get item with id {id_}', EAPIResponseCode.not_found)
        return api_response.json_response()
