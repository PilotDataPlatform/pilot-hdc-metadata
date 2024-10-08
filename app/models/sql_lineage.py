# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import uuid

from sqlalchemy import ARRAY
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

from app.config import ConfigClass
from app.models.models_lineage_provenance import TransformationType

Base = declarative_base()


class LineageModel(Base):
    """Model for lineage table."""

    __tablename__ = 'lineage'
    id = Column(UUID(as_uuid=True), unique=True, primary_key=True)
    consumes = Column(ARRAY(UUID(as_uuid=True)))
    produces = Column(ARRAY(UUID(as_uuid=True)))
    tfrm_type = Column(Enum(TransformationType, name='tfrm_type_enum', create_type=False), nullable=False)

    __table_args__ = ({'schema': ConfigClass.METADATA_SCHEMA},)

    def __init__(self, consumes, produces, tfrm_type):
        self.id = uuid.uuid4()
        self.consumes = consumes
        self.produces = produces
        self.tfrm_type = tfrm_type

    def to_dict(self) -> dict:
        """Return model properties as dict."""
        return {
            'id': str(self.id),
            'consumes': self.consumes,
            'produces': self.produces,
            'tfrm_type': str(self.tfrm_type),
        }
