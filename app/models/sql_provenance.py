# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import uuid
from datetime import datetime

from sqlalchemy import BIGINT
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import LtreeType

from app.app_utils import decode_path_from_ltree
from app.config import ConfigClass
from app.models.models_items import ItemStatus
from app.models.sql_items import ItemModel
from app.models.sql_lineage import LineageModel

Base = declarative_base()


class ProvenanceModel(Base):
    """Model for provenance table."""

    __tablename__ = 'provenance'
    id = Column(UUID(as_uuid=True), unique=True, primary_key=True)
    lineage_id = Column(UUID(as_uuid=True), ForeignKey(LineageModel.id))
    item_id = Column(UUID(as_uuid=True), ForeignKey(ItemModel.id))
    snapshot_time = Column(DateTime(), default=datetime.utcnow, nullable=False)
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

    __table_args__ = ({'schema': ConfigClass.METADATA_SCHEMA},)

    def __init__(
        self,
        lineage_id,
        item_id,
        parent,
        parent_path,
        status,
        type_,
        zone,
        name,
        size,
        owner,
        container_code,
        container_type,
    ):
        self.id = uuid.uuid4()
        self.lineage_id = lineage_id
        self.item_id = item_id
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

    def to_dict(self) -> dict:
        """Return model properties as dict."""
        return {
            'id': str(self.id),
            'lineage_id': str(self.lineage_id),
            'item_id': str(self.item_id),
            'snapshot_time': str(self.snapshot_time),
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
        }
