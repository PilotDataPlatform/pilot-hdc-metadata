# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from fastapi_sqlalchemy import db

from app.models.sql_collections import CollectionsModel
from app.routers.router_exceptions import EntityNotFoundException


def validate_collection(collection_id: UUID) -> CollectionsModel:
    collection_query = db.session.query(CollectionsModel).filter(CollectionsModel.id == collection_id)
    collection_result = collection_query.first()
    if not collection_result:
        raise EntityNotFoundException(f'Collection {collection_id} does not exist')
    return collection_result
