# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LoggerFactory
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi.responses import JSONResponse
from fastapi_sqlalchemy import db
from fastapi_utils.cbv import cbv
from kafka.errors import KafkaConnectionError
from kafka.errors import NoBrokersAvailable

from app.clients.kafka_client import get_kafka_client
from app.config import ConfigClass
from app.models.sql_attribute_templates import AttributeTemplateModel
from app.models.sql_extended import ExtendedModel
from app.models.sql_favourites import FavouritesModel
from app.models.sql_items import ItemModel
from app.models.sql_items_collections import ItemsCollectionsModel
from app.models.sql_storage import StorageModel

_logger = LoggerFactory(
    name='api_health',
    level_default=ConfigClass.LOG_LEVEL_DEFAULT,
    level_file=ConfigClass.LOG_LEVEL_FILE,
    level_stdout=ConfigClass.LOG_LEVEL_STDOUT,
    level_stderr=ConfigClass.LOG_LEVEL_STDERR,
).get_logger()


def opsdb_check() -> bool:
    try:
        db.session.query(ItemModel).first()
        db.session.query(ExtendedModel).first()
        db.session.query(AttributeTemplateModel).first()
        db.session.query(StorageModel).first()
        db.session.query(ItemsCollectionsModel).first()
        db.session.query(FavouritesModel).first()
    except Exception:
        _logger.exception('An exception occurred while performing database query.')
        return False
    return True


def kafka_check() -> bool:
    try:
        get_kafka_client()
        return True
    except KafkaConnectionError:
        _logger.exception('Kafka connection error')
    except NoBrokersAvailable:
        _logger.exception('No Broker available')
        return False


router = APIRouter()


@cbv(router)
class APIHealth:
    @router.get('/health', summary='Healthcheck if all service dependencies are online.')
    async def get_health(
        self, is_db_health: bool = Depends(opsdb_check), is_kafka_health: bool = Depends(kafka_check)
    ) -> Response:
        """Return response that represents status of the database and kafka connections."""
        if is_db_health and is_kafka_health:
            return Response(status_code=204)
        return JSONResponse(status_code=503, content='')
