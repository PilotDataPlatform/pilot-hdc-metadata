# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base

from app.config import ConfigClass
from app.models.sql_collections import CollectionsModel
from app.models.sql_items import ItemModel

Base = declarative_base()


class ItemsCollectionsModel(Base):
    __tablename__ = 'items_collections'
    __table_args__ = {'schema': ConfigClass.METADATA_SCHEMA}
    item_id = Column(ForeignKey(ItemModel.id), primary_key=True)
    collection_id = Column(ForeignKey(CollectionsModel.id), primary_key=True)
