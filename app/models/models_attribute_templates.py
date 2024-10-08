# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import List
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator

from .base_models import APIResponse


class GETTemplate(BaseModel):
    id: UUID


class GETTemplates(BaseModel):
    project_code: str
    name: Optional[str]
    page_size: int = 10
    page: int = 0


class GETTemplateResponse(APIResponse):
    result: dict = Field(
        {},
        example={
            'id': '85465212-168a-4f0c-a7aa-f3a19795d2ff',
            'name': 'template_name',
            'project_code': 'project0422',
            'attributes': [
                {
                    'name': 'attribute_1',
                    'optional': True,
                    'type': 'text',
                },
                {
                    'name': 'attribute_2',
                    'optional': True,
                    'type': 'multiple_choice',
                    'options': ['val1, val2'],
                },
            ],
        },
    )


class POSTTemplateAttributes(BaseModel):
    name: str
    optional: bool = True
    type: str = 'text'
    options: Optional[list[str]]

    @validator('type')
    def type_validation(cls, v):
        if v not in ['text', 'multiple_choice']:
            raise ValueError('type must be text or multiple_choice')
        return v


class POSTTemplate(BaseModel):
    name: str
    project_code: str
    attributes: List[POSTTemplateAttributes]


class POSTTemplateResponse(GETTemplateResponse):
    pass


class PUTTemplate(POSTTemplate):
    pass


class PUTTemplateResponse(GETTemplateResponse):
    pass


class DELETETemplate(BaseModel):
    id: UUID


class DELETETemplateResponse(APIResponse):
    pass
