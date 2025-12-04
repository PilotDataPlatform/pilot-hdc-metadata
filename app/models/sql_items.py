# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime

from sqlalchemy import BIGINT
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import LtreeType

from app.app_utils import decode_path_from_ltree
from app.config import ConfigClass
from app.models.models_items import ItemStatus

Base = declarative_base()


class ItemModel(Base):
    __tablename__ = 'items'
    id = Column(UUID(as_uuid=True), unique=True, primary_key=True)
    parent = Column(UUID(as_uuid=True))
    parent_path = Column(LtreeType())
    restore_path = Column(LtreeType())
    status = Column(Enum(ItemStatus, name='item_status_enum', create_type=False), nullable=False)
    type = Column(Enum('name_folder', 'folder', 'file', name='type_enum', create_type=False), nullable=False)
    zone = Column(Integer(), nullable=False)
    name = Column(String(), nullable=False)
    size = Column(BIGINT(), nullable=False)
    owner = Column(String())
    container_code = Column(String(), nullable=False)
    container_type = Column(Enum('project', 'dataset', name='container_enum', create_type=False), nullable=False)
    deleted = Column(Boolean(), default=False, nullable=False)
    deleted_by = Column(String())
    deleted_at = Column(DateTime(), default=None)
    created_time = Column(DateTime(), default=datetime.utcnow, nullable=False)
    last_updated_time = Column(DateTime(), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index(
            'name_folder_unique',
            'zone',
            'name',
            'container_code',
            'container_type',
            unique=True,
            postgresql_where=Column('type') == 'name_folder',
        ),
        {'schema': ConfigClass.METADATA_SCHEMA},
    )

    def __init__(
        self, id_, parent, parent_path, status, type_, zone, name, size, owner, container_code, container_type
    ):
        self.id = id_
        self.parent = parent
        self.parent_path = parent_path
        self.status = status
        self.type = type_
        self.zone = zone
        self.name = name
        self.size = size
        self.owner = owner
        self.container_code = container_code
        self.container_type = container_type

    def to_dict(self):
        return {
            'id': str(self.id),
            'parent': str(self.parent) if self.parent else None,
            'parent_path': decode_path_from_ltree(self.parent_path) if self.parent_path else None,
            'restore_path': decode_path_from_ltree(self.restore_path) if self.restore_path else None,
            'status': str(self.status),
            'type': self.type,
            'zone': self.zone,
            'name': self.name,
            'size': self.size,
            'owner': self.owner,
            'container_code': self.container_code,
            'container_type': self.container_type,
            'deleted': self.deleted,
            'deleted_time': str(self.deleted_at) if self.deleted_at else None,
            '' 'created_time': str(self.created_time),
            'last_updated_time': str(self.last_updated_time),
        }
