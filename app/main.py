# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import configure_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_sqlalchemy import DBSessionMiddleware

from app.clients.kafka_client import get_kafka_client

from .api_registry import api_registry
from .config import ConfigClass


def create_app():
    app = FastAPI(
        title='Metadata service',
        description='Create and update file metadata',
        docs_url='/v1/api-doc',
        version=ConfigClass.version,
    )

    configure_logging(ConfigClass.LOGGING_LEVEL, ConfigClass.LOGGING_FORMAT)

    app.add_middleware(DBSessionMiddleware, db_url=ConfigClass.SQLALCHEMY_DATABASE_URI)

    app.add_middleware(
        CORSMiddleware,
        allow_origins='*',
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    @app.on_event('shutdown')
    def shutdown_event():
        """
        Summary:
            shutdown event to gracefully close the
            kafka producer.
        """

        client = get_kafka_client()
        client.close_connection()

    api_registry(app)

    return app


app = create_app()
