# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from common import LoggerFactory
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi_utils.cbv import cbv

from app.config import ConfigClass
from app.models.base_models import EAPIResponseCode
from app.models.models_collections import DELETECollectionItems
from app.models.models_collections import DELETECollectionItemsResponse
from app.models.models_collections import DELETECollectionResponse
from app.models.models_collections import GETCollection
from app.models.models_collections import GETCollectionID
from app.models.models_collections import GETCollectionItems
from app.models.models_collections import GETCollectionItemsResponse
from app.models.models_collections import GETCollectionResponse
from app.models.models_collections import POSTCollection
from app.models.models_collections import POSTCollectionItems
from app.models.models_collections import POSTCollectionItemsResponse
from app.models.models_collections import POSTCollectionResponse
from app.models.models_collections import PUTCollectionResponse
from app.models.models_collections import PUTCollections
from app.routers.router_exceptions import BadRequestException
from app.routers.router_exceptions import DuplicateRecordException
from app.routers.router_exceptions import EntityNotFoundException
from app.routers.router_utils import set_api_response_error
from app.routers.v1.items.dependencies import jwt_required

from .crud_collections import add_items
from .crud_collections import create_collection
from .crud_collections import get_collections_by_id
from .crud_collections import get_items_per_collection
from .crud_collections import get_user_collections
from .crud_collections import remove_collection
from .crud_collections import remove_items
from .crud_collections import update_collection

router = APIRouter()
router_bulk = APIRouter()
_logger = LoggerFactory(
    name='api_collections',
    level_default=ConfigClass.LOG_LEVEL_DEFAULT,
    level_file=ConfigClass.LOG_LEVEL_FILE,
    level_stdout=ConfigClass.LOG_LEVEL_STDOUT,
    level_stderr=ConfigClass.LOG_LEVEL_STDERR,
).get_logger()


@cbv(router)
class APICollections:
    @router.get(
        '/search/', response_model=GETCollectionResponse, summary='Get collections that belong to a user per project'
    )
    async def get_collections(self, params: GETCollection = Depends(GETCollection)):
        try:
            api_response = GETCollectionResponse()
            get_user_collections(params, api_response)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except Exception as e:
            _logger.exception(f'Error when get_collections {str(e)}')
            set_api_response_error(
                api_response,
                f'Failed to get collections:user {params.owner}; project {params.container_code}',
                EAPIResponseCode.internal_error,
            )
        return api_response.json_response()

    @router.get('/items/', response_model=GETCollectionItemsResponse, summary='Get items that belong to a collection')
    async def get_collection_items(
        self, params: GETCollectionItems = Depends(GETCollectionItems), current_identity: dict = Depends(jwt_required)
    ):
        try:
            api_response = GETCollectionItemsResponse()
            await get_items_per_collection(params, api_response, current_identity)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except EntityNotFoundException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.not_found)
        except Exception as e:
            _logger.exception(f'Error when get_collection_items {str(e)}')
            set_api_response_error(api_response, 'Failed to get items from collection', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router.get('/{id}/', response_model=GETCollectionResponse, summary='Get collection by id')
    async def get_collections_id(self, params: GETCollectionID = Depends(GETCollectionID)):
        try:
            api_response = GETCollectionResponse()
            get_collections_by_id(params, api_response)
        except EntityNotFoundException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.not_found)
        except Exception as e:
            _logger.exception(f'Error when get_collections_id {str(e)}')
            set_api_response_error(
                api_response, f'Failed to get collections: {params.id}', EAPIResponseCode.internal_error
            )
        return api_response.json_response()

    @router.post('/', response_model=POSTCollectionResponse, summary='Create a collection')
    async def create_new_collection(self, data: POSTCollection):
        try:
            api_response = POSTCollectionResponse()
            create_collection(data, api_response)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except DuplicateRecordException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.conflict)
        except Exception as e:
            _logger.exception(f'Error when create_new_collection {str(e)}')
            set_api_response_error(
                api_response, f'Failed to create collection with id {data.id}', EAPIResponseCode.internal_error
            )
        return api_response.json_response()

    @router.put('/', response_model=PUTCollectionResponse, summary='Update a collection(s) name')
    async def update_collection_name(self, data: PUTCollections):
        try:
            api_response = PUTCollectionResponse()
            update_collection(data, api_response)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except EntityNotFoundException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.not_found)
        except DuplicateRecordException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.conflict)
        except Exception as e:
            _logger.exception(f'Error when update_collection_name {str(e)}')
            set_api_response_error(api_response, 'Failed to update collection(s)', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router.delete('/', response_model=DELETECollectionResponse, summary='Delete a collection')
    async def remove_collection(self, id_: UUID = Query(None, alias='id')):
        try:
            api_response = DELETECollectionResponse()
            remove_collection(id_, api_response)
        except EntityNotFoundException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.not_found)
        except Exception as e:
            _logger.exception(f'Error when remove_collection {str(e)}')
            set_api_response_error(api_response, f'Failed to delete collection {id_}', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router.post('/items/', response_model=POSTCollectionItemsResponse, summary='Add items to a collection')
    async def add_items_to_collection(self, data: POSTCollectionItems):
        try:
            api_response = POSTCollectionItemsResponse()
            add_items(data, api_response)
        except EntityNotFoundException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.not_found)
        except Exception as e:
            _logger.exception(f'Error when add_items_to_collection {str(e)}')
            set_api_response_error(
                api_response, f'Failed to add items to collection {data.id}', EAPIResponseCode.internal_error
            )
        return api_response.json_response()

    @router.delete('/items/', response_model=DELETECollectionItemsResponse, summary='Remove items from a collection')
    async def remove_items_from_collection(self, data: DELETECollectionItems):
        try:
            api_response = DELETECollectionItemsResponse()
            remove_items(data)
        except EntityNotFoundException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.not_found)
        except Exception as e:
            _logger.exception(f'Error when remove_items_from_collection {str(e)}')
            set_api_response_error(
                api_response, f'Failed to delete items from collection {data.id}', EAPIResponseCode.internal_error
            )
        return api_response.json_response()
