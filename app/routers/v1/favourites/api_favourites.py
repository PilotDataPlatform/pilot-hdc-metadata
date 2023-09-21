# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LoggerFactory
from fastapi import APIRouter
from fastapi import Depends
from fastapi_utils.cbv import cbv

from app.config import ConfigClass
from app.models.base_models import EAPIResponseCode
from app.models.models_favourites import DELETEFavourite
from app.models.models_favourites import DELETEFavouriteResponse
from app.models.models_favourites import DELETEFavourites
from app.models.models_favourites import GETFavourite
from app.models.models_favourites import GETFavouriteResponse
from app.models.models_favourites import PATCHFavourite
from app.models.models_favourites import PATCHFavouriteResponse
from app.models.models_favourites import PATCHFavourites
from app.models.models_favourites import POSTFavourite
from app.models.models_favourites import POSTFavouriteResponse
from app.routers.router_exceptions import BadRequestException
from app.routers.router_exceptions import DuplicateRecordException
from app.routers.router_exceptions import EntityNotFoundException
from app.routers.router_exceptions import UnauthorizedException
from app.routers.router_utils import set_api_response_error
from app.routers.v1.favourites.crud_favourites import bulk_delete_favourites
from app.routers.v1.favourites.crud_favourites import bulk_pin_unpin_favourites
from app.routers.v1.favourites.crud_favourites import create_favourite
from app.routers.v1.favourites.crud_favourites import delete_favourite_by_user_and_entity_id
from app.routers.v1.favourites.crud_favourites import get_favourites_by_user
from app.routers.v1.favourites.crud_favourites import pin_unpin_favourite_by_user_and_entity_id

router = APIRouter()
router_bulk = APIRouter()
_logger = LoggerFactory(
    name='api_favourites',
    level_default=ConfigClass.LOG_LEVEL_DEFAULT,
    level_file=ConfigClass.LOG_LEVEL_FILE,
    level_stdout=ConfigClass.LOG_LEVEL_STDOUT,
    level_stderr=ConfigClass.LOG_LEVEL_STDERR,
).get_logger()


@cbv(router)
class APIFavourites:
    @router.post('/', response_model=POSTFavouriteResponse, summary='Favourite an entity')
    async def create_favourite(self, data: POSTFavourite):
        try:
            api_response = POSTFavouriteResponse()
            api_response.result = create_favourite(data)
        except UnauthorizedException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.forbidden, _logger)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request, _logger)
        except EntityNotFoundException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.not_found, _logger)
        except DuplicateRecordException:
            set_api_response_error(api_response, 'Favourite conflict in database', EAPIResponseCode.conflict, _logger)
        except Exception:
            set_api_response_error(api_response, 'Failed to create favourite', EAPIResponseCode.internal_error, _logger)
        return api_response.json_response()

    @router.patch('/', response_model=PATCHFavouriteResponse, summary='Pin or unpin an existing favourite')
    async def pin_favourite(self, user: str, params: PATCHFavourite = Depends(PATCHFavourite)):
        try:
            api_response = PATCHFavouriteResponse()
            api_response.result = pin_unpin_favourite_by_user_and_entity_id(user, params.id, params.type, params.pinned)
        except EntityNotFoundException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.not_found, _logger)
        except Exception:
            set_api_response_error(
                api_response, 'Failed to pin or unpin favourite', EAPIResponseCode.internal_error, _logger
            )
        return api_response.json_response()

    @router.delete('/', response_model=DELETEFavouriteResponse, summary='Remove an existing favourite')
    async def delete_favourite(self, params: DELETEFavourite = Depends(DELETEFavourite)):
        try:
            api_response = DELETEFavouriteResponse()
            delete_favourite_by_user_and_entity_id(params.id, params.user, params.type, api_response)
        except EntityNotFoundException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.not_found, _logger)
        except Exception:
            set_api_response_error(api_response, 'Failed to remove favourite', EAPIResponseCode.internal_error, _logger)
        return api_response.json_response()


@cbv(router_bulk)
class APIFavouritesBulk:
    @router_bulk.get('/{user}/', response_model=GETFavouriteResponse, summary='Get all favourites for a user')
    async def get_favourites(self, params: GETFavourite = Depends(GETFavourite)):
        try:
            api_response = GETFavouriteResponse()
            get_favourites_by_user(params, api_response)
        except BadRequestException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.bad_request)
        except Exception:
            set_api_response_error(
                api_response, f'Failed to get favourites for user {params.user}', EAPIResponseCode.not_found, _logger
            )
        return api_response.json_response()

    @router_bulk.patch('/', response_model=PATCHFavouriteResponse, summary='Pin or unpin many existing favourites')
    async def pin_favourites(self, data: PATCHFavourites, user: str):
        try:
            api_response = PATCHFavouriteResponse()
            bulk_pin_unpin_favourites(user, data, api_response)
        except EntityNotFoundException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.not_found, _logger)
        except Exception:
            set_api_response_error(
                api_response, 'Failed to pin or unpin favourite', EAPIResponseCode.internal_error, _logger
            )
        return api_response.json_response()

    @router_bulk.delete('/', response_model=DELETEFavouriteResponse, summary='Remove many existing favourites')
    async def delete_favourites(self, data: DELETEFavourites, user: str):
        try:
            api_response = DELETEFavouriteResponse()
            bulk_delete_favourites(user, data, api_response)
        except EntityNotFoundException as e:
            set_api_response_error(api_response, str(e), EAPIResponseCode.not_found, _logger)
        except Exception:
            set_api_response_error(
                api_response, 'Failed to remove favourites', EAPIResponseCode.internal_error, _logger
            )
        return api_response.json_response()
