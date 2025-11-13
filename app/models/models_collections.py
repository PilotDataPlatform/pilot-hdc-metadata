# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from .base_models import APIResponse
from .base_models import PaginationRequest
from .models_items import ItemStatus


class Collection(BaseModel):
    id: UUID
    name: str


class GETCollection(PaginationRequest):
    owner: str
    container_code: str


class GETCollectionID(BaseModel):
    id: UUID


class GETCollectionItems(PaginationRequest):
    id: UUID
    status: ItemStatus = ItemStatus.ACTIVE
    container_code: str


class GETCollectionResponse(APIResponse):
    result: list = Field(
        {},
        example=[
            {
                'id': '52c4a134-8550-4acc-9ab9-596548c91c52',
                'name': 'collection1',
                'owner': 'admin',
                'container_code': 'project123',
                'created_time': '2022-04-13 13:30:10.890347',
                'last_updated_time': '2022-04-13 13:30:10.890347',
            }
        ],
    )


class GETCollectionItemsResponse(APIResponse):
    result: dict = Field(
        {},
        example={
            'id': '85465212-168a-4f0c-a7aa-f3a19795d2ff',
            'parent': '28c608ac-1693-4318-a1c4-412caf2cd74a',
            'parent_path': 'path/to/file',
            'type': 'file',
            'zone': 0,
            'name': 'filename',
            'size': 0,
            'owner': 'username',
            'container_code': 'project_code',
            'container_type': 'project',
            'created_time': '2022-04-13 13:30:10.890347',
            'last_updated_time': '2022-04-13 13:30:10.890347',
            'storage': {
                'id': 'ba623005-8183-419a-972a-e4ce0d539349',
                'location_uri': 'https://example.com/item',
                'version': '1.0',
            },
            'extended': {
                'id': 'dc763d28-7e74-4db3-a702-fa719aa702c6',
                'extra': {
                    'tags': ['tag1', 'tag2'],
                    'system_tags': ['tag1', 'tag2'],
                    'attributes': {'101778d7-a628-41ea-823b-e4b377f3476c': {'key1': 'value1', 'key2': 'value2'}},
                },
            },
        },
    )


class POSTCollection(BaseModel):
    id: UUID | None = Field(example='3fa85f64-5717-4562-b3fc-2c963f66afa6')
    owner: str
    container_code: str
    name: str

    class Config:
        anystr_strip_whitespace = True

    @validator('name')
    def check_special_characters_in_name(cls, v):
        special_char = re.compile(r'[\/:?*<>|"\']')
        found_char = special_char.findall(v)
        if found_char:
            raise ValueError(f'Cannot use special character(s) {list(set(found_char))} in collection name')
        return v


class POSTCollectionResponse(GETCollectionResponse):
    pass


class PUTCollections(BaseModel):
    owner: str
    container_code: str
    collections: list[Collection]

    @validator('collections')
    def check_duplicate_collection_names(cls, v):
        names = [collection.name for collection in v]
        if len(names) is not len(set(names)):
            raise ValueError('Cannot use duplicate collection names')
        return v

    @validator('collections')
    def check_special_characters_in_name(cls, v):
        special_char = re.compile(r'[\/:?*<>|"\']')
        for collection in v:
            found_char = special_char.findall(collection.name)
            if found_char:
                raise ValueError(f'Cannot use special character(s) {list(set(found_char))} in collection name')
        return v


class PUTCollectionResponse(APIResponse):
    result: dict = Field(
        {},
        example={
            'owner': 'admin',
            'container_code': 'project123',
            'collections': [{'id': '52c4a134-8550-4acc-9ab9-596548c91c52', 'name': 'collection2'}],
        },
    )


class POSTCollectionItems(BaseModel):
    id: UUID
    item_ids: list[UUID]


class POSTCollectionItemsResponse(APIResponse):
    result: list = Field(
        [],
        example=['3b3aad9e-2a39-4153-8146-87fb0923bab8', '95f1c2ac-dd77-43b4-af53-2ce8f901ff78'],
    )


class DELETECollectionResponse(APIResponse):
    pass


class DELETECollectionItems(BaseModel):
    id: UUID
    item_ids: list[UUID]


class DELETECollectionItemsResponse(APIResponse):
    pass
