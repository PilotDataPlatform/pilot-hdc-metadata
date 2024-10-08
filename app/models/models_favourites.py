# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from .base_models import APIResponse
from .base_models import PaginationRequest


class Favourite(BaseModel):
    id: UUID
    type: str = 'item'

    @validator('type')
    def type_is_valid(cls, v):
        if v not in ['item', 'collection']:
            raise ValueError('type must be item or collection')
        return v


class GETFavourite(PaginationRequest):
    user: str


class GETFavouriteResponse(APIResponse):
    result: dict = Field(
        {},
        example={
            'id': '5bc614a6-0930-435f-97a1-72f97b227039',
            'type': 'file',
            'name': 'my_file.txt',
            'display_path': 'My Project/Core/Home',
            'pinned': False,
        },
    )


class POSTFavourite(Favourite):
    user: str
    zone: int
    container_code: str


class POSTFavouriteResponse(GETFavouriteResponse):
    pass


class PATCHFavourite(Favourite):
    user: str
    pinned: bool


class PATCHFavourites(BaseModel):
    favourites: list[PATCHFavourite]


class PATCHFavouriteResponse(GETFavouriteResponse):
    pass


class DELETEFavourite(Favourite):
    user: str


class DELETEFavouriteResponse(APIResponse):
    pass


class DELETEFavourites(BaseModel):
    favourites: list[Favourite]
