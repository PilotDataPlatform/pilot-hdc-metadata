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
from app.models.models_attribute_templates import DELETETemplate
from app.models.models_attribute_templates import DELETETemplateResponse
from app.models.models_attribute_templates import GETTemplate
from app.models.models_attribute_templates import GETTemplateResponse
from app.models.models_attribute_templates import GETTemplates
from app.models.models_attribute_templates import POSTTemplate
from app.models.models_attribute_templates import POSTTemplateResponse
from app.models.models_attribute_templates import PUTTemplate
from app.models.models_attribute_templates import PUTTemplateResponse
from app.routers.router_exceptions import EntityNotFoundException
from app.routers.router_utils import set_api_response_error

from .crud import create_template
from .crud import delete_template_by_id
from .crud import get_template_by_id
from .crud import get_templates_by_project_code
from .crud import update_template

router = APIRouter()
_logger = LoggerFactory(
    name='api_attribute_templates',
    level_default=ConfigClass.LOG_LEVEL_DEFAULT,
    level_file=ConfigClass.LOG_LEVEL_FILE,
    level_stdout=ConfigClass.LOG_LEVEL_STDOUT,
    level_stderr=ConfigClass.LOG_LEVEL_STDERR,
).get_logger()


@cbv(router)
class APIAttributeTemplates:
    @router.get('/{id}/', response_model=GETTemplateResponse, summary='Get an attribute template')
    async def get_attribute_template(self, params: GETTemplate = Depends(GETTemplate)):
        try:
            api_response = GETTemplateResponse()
            get_template_by_id(params, api_response)
        except Exception as e:
            _logger.exception(f'Error when get_attribute_template {str(e)}')
            set_api_response_error(
                api_response, f'Failed to get template with id {params.id}', EAPIResponseCode.not_found
            )
        return api_response.json_response()

    @router.get('/', summary='Get all attribute templates associated with a project')
    async def get_attribute_templates(self, params: GETTemplates = Depends(GETTemplates)):
        try:
            api_response = GETTemplateResponse()
            get_templates_by_project_code(params, api_response)
        except Exception as e:
            _logger.exception(f'Error when get_attribute_templates {str(e)}')
            set_api_response_error(
                api_response, f'Failed to get templates with code {params.project_code}', EAPIResponseCode.not_found
            )
        return api_response.json_response()

    @router.post('/', response_model=POSTTemplateResponse, summary='Create a new attribute template')
    async def create_attribute_template(self, data: POSTTemplate):
        try:
            api_response = POSTTemplateResponse()
            create_template(data, api_response)
        except Exception as e:
            _logger.exception(f'Error when create_attribute_template {str(e)}')
            set_api_response_error(api_response, 'Failed to create attribute template', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router.put('/', response_model=PUTTemplateResponse, summary='Update an attribute template')
    async def update_attribute_template(self, data: PUTTemplate, id_: UUID = Query(None, alias='id')):
        try:
            api_response = PUTTemplateResponse()
            update_template(id_, data, api_response)
        except EntityNotFoundException:
            set_api_response_error(api_response, f'Failed to get template with id {id_}', EAPIResponseCode.not_found)
        except Exception as e:
            _logger.exception(f'Error when update_attribute_template {str(e)}')
            set_api_response_error(api_response, 'Failed to update attribute template', EAPIResponseCode.internal_error)
        return api_response.json_response()

    @router.delete('/', response_model=DELETETemplateResponse, summary='Delete an attribute template')
    async def delete_attribute_template(self, params: DELETETemplate = Depends(DELETETemplate)):
        try:
            api_response = DELETETemplateResponse()
            delete_template_by_id(params, api_response)
        except EntityNotFoundException:
            set_api_response_error(
                api_response, f'Failed to get template with id {params.id}', EAPIResponseCode.not_found
            )
        except Exception as e:
            _logger.exception(f'Error when delete_attribute_template {str(e)}')
            set_api_response_error(api_response, 'Failed to delete template', EAPIResponseCode.internal_error)
        return api_response.json_response()
