# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LoggerFactory
from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv

from app.config import ConfigClass
from app.models.base_models import EAPIResponseCode
from app.models.models_lineage_provenance import GETLineageProvenance
from app.models.models_lineage_provenance import GETLineageProvenanceResponse
from app.routers.router_utils import set_api_response_error
from app.routers.v1.items.crud_lineage_provenance import get_lineage_provenance_by_item_id

router = APIRouter()
_logger = LoggerFactory(
    name='api_lineage_provenance',
    level_default=ConfigClass.LOG_LEVEL_DEFAULT,
    level_file=ConfigClass.LOG_LEVEL_FILE,
    level_stdout=ConfigClass.LOG_LEVEL_STDOUT,
    level_stderr=ConfigClass.LOG_LEVEL_STDERR,
).get_logger()


@cbv(router)
class APILineageProvenance:
    @router.get(
        '/{item_id}/', response_model=GETLineageProvenanceResponse, summary='Get lineage and provenance for an item'
    )
    async def get_lineage_provenance(self, params: GETLineageProvenance = Depends()) -> JSONResponse:
        try:
            api_response = GETLineageProvenanceResponse()
            api_response.result = get_lineage_provenance_by_item_id(params.item_id)
        except Exception:
            set_api_response_error(
                api_response,
                f'Failed to get lineage for item with id {params.item_id}',
                EAPIResponseCode.not_found,
                _logger,
            )
        return api_response.json_response()
