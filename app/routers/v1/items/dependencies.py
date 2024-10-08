# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import JWTHandler
from fastapi import Request

from app.config import ConfigClass
from app.routers.router_exceptions import UnauthorizedException


async def jwt_required(request: Request):
    jwt_handler = JWTHandler(ConfigClass.RSA_PUBLIC_KEY)
    try:
        encoded_token = jwt_handler.get_token(request)
        decoded_token = jwt_handler.decode_validate_token(encoded_token)
        current_identity = await jwt_handler.get_current_identity(ConfigClass.AUTH_HOST, decoded_token)
    except Exception:
        raise UnauthorizedException()
    return current_identity
