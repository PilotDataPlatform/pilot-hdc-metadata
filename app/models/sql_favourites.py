# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import uuid
from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from app.config import ConfigClass

from .sql_collections import CollectionsModel
from .sql_items import ItemModel

Base = declarative_base()


class FavouritesModel(Base):
    __tablename__ = 'favourites'
    id = Column(UUID(as_uuid=True), unique=True, primary_key=True)
    user = Column(String())
    item_id = Column(UUID(as_uuid=True), ForeignKey(ItemModel.id), unique=True)
    collection_id = Column(UUID(as_uuid=True), ForeignKey(CollectionsModel.id), unique=True)
    created_time = Column(DateTime(), default=datetime.utcnow, nullable=False)
    pinned = Column(Boolean(), nullable=False)

    __table_args__ = ({'schema': ConfigClass.METADATA_SCHEMA},)

    def __init__(self, user, item_id, collection_id, pinned):
        self.id = uuid.uuid4()
        self.user = user
        self.item_id = item_id
        self.collection_id = collection_id
        self.pinned = pinned

    def to_dict(self):
        return {
            'id': str(self.id),
            'user': self.user,
            'item_id': str(self.item_id) if self.item_id else None,
            'collection_id': str(self.collection_id) if self.collection_id else None,
            'created_time': str(self.created_time),
            'pinned': self.pinned,
        }
