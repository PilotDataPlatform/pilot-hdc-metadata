# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum

from fastapi.responses import JSONResponse
from pydantic import BaseModel


class EAPIResponseCode(Enum):
    success = 200
    bad_request = 400
    unauthorized = 401
    forbidden = 403
    not_found = 404
    conflict = 409
    too_large = 413
    internal_error = 500


class APIResponse(BaseModel):
    code: EAPIResponseCode = EAPIResponseCode.success
    error_msg: str = ''
    page: int = 0
    total: int = 1
    num_of_pages: int = 1
    result = []

    def json_response(self) -> JSONResponse:
        data = self.dict()
        data['code'] = self.code.value
        return JSONResponse(status_code=self.code.value, content=data)

    def set_error_msg(self, error_msg):
        self.error_msg = error_msg

    def set_code(self, code):
        self.code = code


class PaginationRequest(BaseModel):
    page: int = 0
    page_size: int = 25
    order: str = 'asc'
    sorting: str = 'created_time'
