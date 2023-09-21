# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_sqlalchemy import DBSessionMiddleware

from app.clients.kafka_client import get_kafka_client

from .api_registry import api_registry
from .config import ConfigClass

app = FastAPI(
    title='Metadata service',
    description='Create and update file metadata',
    docs_url='/v1/api-doc',
    version=ConfigClass.version,
)
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
    '''
    Summary:
        shutdown event to gracefully close the
        kafka producer.
    '''

    client = get_kafka_client()
    client.close_connection()


api_registry(app)
