# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field

from .base_models import APIResponse


class TransformationType(str, Enum):
    """Enum contains every allowed type of lineage transformation."""

    COPY_TO_ZONE = 'copy_to_zone'
    ARCHIVE = 'archive'

    def __str__(self):
        return '%s' % self.name


class GETLineageProvenance(BaseModel):
    item_id: UUID


class GETLineageProvenanceResponse(APIResponse):
    result: dict = Field(
        {},
        example={
            'lineage': {
                '176c729a-b85a-494c-94ac-e86e78b054fa': {
                    'tfrm_type': 'COPY_TO_ZONE',
                    'consumes': ['ecbe5a8a-4324-4350-9af2-a444fbf55066'],
                    'produces': ['df77c805-e824-46e7-a465-5837eae26d89'],
                },
                '991fe983-855e-4581-b0c9-e511642161a1': {
                    'tfrm_type': 'ARCHIVE',
                    'consumes': ['df77c805-e824-46e7-a465-5837eae26d89'],
                    'produces': None,
                },
            },
            'provenance': {
                'ecbe5a8a-4324-4350-9af2-a444fbf55066': {
                    'id': '8ea0d88c-6d16-4fb2-9696-7d9f6ed9387b',
                    'lineage_id': '176c729a-b85a-494c-94ac-e86e78b054fa',
                    'snapshot_time': '2023-03-22 15:10:58.703542',
                    'parent': 'a3f64e1f-be8b-4c97-8f77-994f5529b969',
                    'parent_path': 'user/test_folder',
                    'restore_path': None,
                    'status': 'ACTIVE',
                    'type': 'file',
                    'zone': 0,
                    'name': 'hour.flac',
                    'size': 0,
                    'owner': 'lopezkathy',
                    'container_code': 'test_container',
                    'container_type': 'project',
                },
                'df77c805-e824-46e7-a465-5837eae26d89': {
                    'id': 'af682935-63f1-4f77-b111-441043165163',
                    'lineage_id': '991fe983-855e-4581-b0c9-e511642161a1',
                    'snapshot_time': '2023-03-22 15:10:58.774891',
                    'parent': None,
                    'parent_path': 'user/test_folder',
                    'restore_path': None,
                    'status': 'ARCHIVED',
                    'type': 'file',
                    'zone': 1,
                    'name': 'official.webm',
                    'size': 0,
                    'owner': 'ryan64',
                    'container_code': 'test_container',
                    'container_type': 'project',
                },
            },
        },
    )
