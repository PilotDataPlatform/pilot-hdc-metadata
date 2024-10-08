# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import uuid
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from app.config import ConfigClass

Base = declarative_base()


class CollectionsModel(Base):
    __tablename__ = 'collections'
    __table_args__ = {'schema': ConfigClass.METADATA_SCHEMA}
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(), nullable=False)
    container_code = Column(String(), nullable=False)
    owner = Column(String(), nullable=False)
    created_time = Column(DateTime(), default=datetime.utcnow, nullable=False)
    last_updated_time = Column(DateTime(), default=datetime.utcnow, nullable=False)

    def __init__(self, name, container_code, owner, id_=None, last_updated_time=None):
        self.id = id_ if id_ else uuid.uuid4()
        self.name = name
        self.container_code = container_code
        self.owner = owner
        self.last_updated_time = last_updated_time if last_updated_time else datetime.utcnow()

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'container_code': self.container_code,
            'owner': self.owner,
            'created_time': str(self.created_time),
            'last_updated_time': str(self.last_updated_time),
        }
