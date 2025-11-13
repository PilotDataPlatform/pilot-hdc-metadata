# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from app.config import ConfigClass
from app.models.models_lineage_provenance import TransformationType

from .base_models import APIResponse
from .base_models import PaginationRequest


class ItemStatus(str, Enum):
    """The new enum type for file status.

    - REGISTERED means file is created by upload service but not complete yet. either in progress or fail.
    - ACTIVE means file uploading is complete.
    - ARCHIVED means the file has been deleted.
    """

    REGISTERED = 'REGISTERED'
    ACTIVE = 'ACTIVE'
    ARCHIVED = 'ARCHIVED'

    def __str__(self):
        return f'{self.name}'


class ItemType(str, Enum):
    FILE = 'file'
    FOLDER = 'folder'
    NAME_FOLDER = 'name_folder'

    def __str__(self):
        return f'{self.name}'


class ContainerType(str, Enum):
    PROJECT = 'project'
    DATASET = 'dataset'

    def __str__(self):
        return f'{self.name}'


class GETItem(BaseModel):
    id: UUID


class GETItemByLocation(BaseModel):
    name: str
    parent_path: str | None
    container_code: str
    container_type: ContainerType
    zone: int
    status: ItemStatus


class GETItemsByIDs(BaseModel):
    page_size: int = 10
    page: int = 0


class GETItemsByLocation(PaginationRequest):
    container_code: str | None
    zone: int | None
    recursive: bool = False
    status: ItemStatus = ItemStatus.ACTIVE
    parent_path: str | None
    restore_path: str | None
    name: str | None
    owner: str | None
    type: str | None
    container_type: str | None
    auth_user: str | None
    project_role: str | None
    fav_user: str | None
    last_updated_start: datetime | None = None
    last_updated_end: datetime | None = None

    class Config:
        anystr_strip_whitespace = True


class GETItemResponse(APIResponse):
    result: dict = Field(
        {},
        example={
            'id': '85465212-168a-4f0c-a7aa-f3a19795d2ff',
            'parent': '28c608ac-1693-4318-a1c4-412caf2cd74a',
            'parent_path': 'path/to/file',
            'restore_path': None,
            'status': ItemStatus.ACTIVE,
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


class POSTItem(BaseModel):
    id: UUID | None
    parent: UUID | None = Field(example='3fa85f64-5717-4562-b3fc-2c963f66afa6')
    parent_path: str | None = Field(example='path/to/file')
    container_code: str
    container_type: str = 'project'
    type: str = 'file'
    status: ItemStatus = ItemStatus.REGISTERED
    zone: int = 0
    name: str = Field(example='file_name.txt')
    size: int = 0
    owner: str
    upload_id: str | None
    location_uri: str | None
    version: str | None
    tags: list[str] = []
    system_tags: list[str] = []
    attribute_template_id: UUID | None
    attributes: dict | None = {}
    tfrm_source: UUID | None = None
    tfrm_type: TransformationType | None = None

    class Config:
        anystr_strip_whitespace = True

    @validator('type')
    def type_is_valid(cls, v, values):
        if v not in ['file', 'folder', 'name_folder']:
            raise ValueError('type must be one of: file, folder, name_folder')
        elif 'parent' in values and values['parent'] and v == 'name_folder':
            raise ValueError('Name folders cannot have a parent')
        elif 'parent_path' in values and values['parent_path'] and v == 'name_folder':
            raise ValueError('Name folders cannot have a parent_path')
        elif (
            'parent' not in values
            or not values['parent']
            and v != 'name_folder'
            and values['container_type'] == 'project'
        ):
            raise ValueError('Files and folders must have a parent if not part of a dataset')
        elif (
            'parent_path' not in values
            or not values['parent_path']
            and v != 'name_folder'
            and values['container_type'] == 'project'
        ):
            raise ValueError('Files and folders must have a parent_path if not part of a dataset')
        return v

    @validator('container_type')
    def container_type_is_valid(cls, v, values):
        if v not in ['project', 'dataset']:
            raise ValueError('container_type must be project or dataset')
        elif 'type' in values and values['type'] == 'name_folder' and v != 'project':
            raise ValueError('Name folders are only allowed in projects')
        return v

    @validator('tags')
    def tags_count(cls, v):
        if len(v) > ConfigClass.MAX_TAGS:
            raise ValueError(f'Maximum of {ConfigClass.MAX_TAGS} tags')
        return v

    @validator('system_tags')
    def system_tags_count(cls, v):
        if len(v) > ConfigClass.MAX_SYSTEM_TAGS:
            raise ValueError(f'Maximum of {ConfigClass.MAX_SYSTEM_TAGS} system tags')
        return v

    @validator('name')
    def folder_name_is_valid(cls, v, values):
        if 'type' in values and values['type'] == 'folder' and '/' in v:
            raise ValueError('Folder name cannot contain reserved character: /')
        return v

    @validator('attributes')
    def attributes_are_valid(cls, v, values):
        if 'type' in values and values['type'] and values['type'] != 'file':
            raise ValueError('Attributes can only be applied to files')
        for attribute in v.values():
            if len(attribute) > ConfigClass.MAX_ATTRIBUTE_LENGTH:
                raise ValueError(
                    f'Attribute exceeds maximum length of {ConfigClass.MAX_ATTRIBUTE_LENGTH} characters: {attribute}'
                )
        return v

    @validator('attribute_template_id')
    def attribute_template_only_on_files(cls, v, values):
        if 'type' in values and values['type'] and values['type'] != 'file':
            raise ValueError('Attribute templates can only be applied to files')
        return v


class POSTItems(BaseModel):
    items: list[POSTItem]
    skip_duplicates: bool = False


class PATCHItem(BaseModel):
    id: UUID
    status: ItemStatus


class PATCHItemResponse(GETItemResponse):
    pass


class POSTItemResponse(GETItemResponse):
    pass


class PUTItem(POSTItem):
    parent: UUID | None = Field(example='3fa85f64-5717-4562-b3fc-2c963f66afa6', default='')
    parent_path: str | None = Field(example='path/to/file', default='')
    type: str | None
    status: ItemStatus | None
    zone: int | None
    name: str | None = Field(example='file_name.txt')
    size: int | None
    owner: str | None
    container_code: str | None
    container_type: str | None
    location_uri: str | None
    version: str | None
    tags: list[str] | None
    system_tags: list[str] | None
    attribute_template_id: UUID | None
    attributes: dict | None

    class Config:
        anystr_strip_whitespace = True


class PUTItems(BaseModel):
    items: list[PUTItem]


class PUTItemResponse(GETItemResponse):
    pass


class DELETEItem(BaseModel):
    id: UUID


class DELETEItemResponse(APIResponse):
    pass


class PUTItemsBequeath(BaseModel):
    attribute_template_id: UUID | None
    attributes: dict | None
    system_tags: list[str] | None


class PUTItemsBequeathResponse(GETItemResponse):
    pass
