# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import uuid

from sqlalchemy import JSON
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from app.config import ConfigClass

Base = declarative_base()


class AttributeTemplateModel(Base):
    __tablename__ = 'attribute_templates'
    id = Column(UUID(as_uuid=True), unique=True, primary_key=True)
    name = Column(String(), nullable=False)
    project_code = Column(String(), nullable=False)
    attributes = Column(JSON())

    __table_args__ = ({'schema': ConfigClass.METADATA_SCHEMA},)

    def __init__(self, name, project_code, attributes):
        self.id = uuid.uuid4()
        self.name = name
        self.project_code = project_code
        self.attributes = attributes

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'project_code': self.project_code,
            'attributes': self.attributes,
        }
