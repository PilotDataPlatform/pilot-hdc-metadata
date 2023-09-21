# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Callable

from common import LoggerFactory
from pydantic import BaseModel

from app.models.base_models import APIResponse
from app.models.base_models import EAPIResponseCode
from app.models.sql_items import Base


def paginate(
    params: BaseModel, api_response: APIResponse, query: Base, expand_func: Callable = None, **kwargs
) -> APIResponse:
    total = query.count()
    query = query.limit(params.page_size).offset(params.page * params.page_size)
    entities = query.all()
    results = []
    for entity in entities:
        if expand_func:
            entity_dict = expand_func(entity, kwargs)
            results.append(entity_dict)
        else:
            results.append(entity.to_dict())
    api_response.page = params.page
    api_response.num_of_pages = int(int(total) / int(params.page_size)) + 1
    api_response.total = total
    api_response.result = results


def set_api_response_error(
    api_response: APIResponse, message: str, code: EAPIResponseCode, _logger: LoggerFactory = None
):
    if _logger:
        _logger.exception(message)
    api_response.set_error_msg(message)
    api_response.set_code(code)
    api_response.total = 0
    api_response.num_of_pages = 0
