# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import random
import re
import string
import uuid
from datetime import datetime

import pytest
from alembic.command import upgrade
from alembic.config import Config
from faker import Faker
from fastapi.testclient import TestClient as Client
from fastapi_sqlalchemy import DBSessionMiddleware
from fastapi_sqlalchemy import db as db_session
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.schema import CreateSchema
from sqlalchemy_utils import create_database
from sqlalchemy_utils import database_exists
from testcontainers.postgres import PostgresContainer

from app.clients.kafka_client import get_kafka_client
from app.config import ConfigClass
from app.models.models_items import ContainerType
from app.models.models_items import ItemStatus
from app.models.models_items import ItemType
from app.models.models_lineage_provenance import TransformationType
from tests.main import KafkaTestClient

POSTGRES_DOCKER_IMAGE = 'postgres:14.2-alpine'


def generate_random_container_code() -> str:
    random_container_code = 'test_'
    for _ in range(8):
        random_container_code += chr(random.randint(32, 126))
    return random_container_code.replace(' ', '')


def generate_random_collection_name() -> str:
    random_collection_name = 'test'
    letters = string.ascii_lowercase
    for _ in range(8):
        random_collection_name += random.choice(letters)
    return random_collection_name.replace(' ', '')


def generate_random_username() -> str:
    fake = Faker()
    return fake.user_name().replace(' ', '')


def generate_random_file_name() -> str:
    fake = Faker()
    return fake.file_name()


@pytest.fixture(scope='function')
def test_items(app) -> dict:
    props = {
        'container_code': 'test_project',
        'container_code_dataset': 'test_dataset',
        'zone': 0,
        'datetime': datetime.utcnow(),
        'ids': {
            'name_folder': str(uuid.uuid4()),
            'folder': str(uuid.uuid4()),
            'file_1': str(uuid.uuid4()),
            'file_2': str(uuid.uuid4()),
            'file_3': str(uuid.uuid4()),
        },
        'ids_dataset': {'file_dataset': str(uuid.uuid4())},
    }
    payload = {
        'items': [
            {
                'id': props['ids']['name_folder'],
                'parent': None,
                'parent_path': None,
                'type': 'name_folder',
                'status': ItemStatus.ACTIVE,
                'zone': props['zone'],
                'name': 'user',
                'size': 0,
                'owner': 'user',
                'container_code': props['container_code'],
                'container_type': 'project',
                'location_uri': '',
                'version': '',
            },
            {
                'id': props['ids']['folder'],
                'parent': props['ids']['name_folder'],
                'parent_path': 'user',
                'type': 'folder',
                'status': ItemStatus.ACTIVE,
                'zone': props['zone'],
                'name': 'test_folder',
                'size': 0,
                'owner': 'user',
                'container_code': props['container_code'],
                'container_type': 'project',
                'location_uri': '',
                'version': '',
                'tags': [],
                'system_tags': [],
            },
            {
                'id': props['ids']['file_1'],
                'parent': props['ids']['folder'],
                'parent_path': 'user/test_folder',
                'type': 'file',
                'status': ItemStatus.REGISTERED,
                'zone': props['zone'],
                'name': 'test_file_1.txt',
                'size': 100,
                'owner': 'user',
                'container_code': props['container_code'],
                'container_type': 'project',
                'location_uri': '',
                'version': '',
                'tags': [],
                'system_tags': [],
            },
            {
                'id': props['ids']['file_2'],
                'parent': props['ids']['folder'],
                'parent_path': 'user/test_folder',
                'type': 'file',
                'status': ItemStatus.REGISTERED,
                'zone': props['zone'],
                'name': 'test_file_2.txt',
                'size': 100,
                'owner': 'user',
                'container_code': props['container_code'],
                'container_type': 'project',
                'location_uri': '',
                'version': '',
                'tags': [],
                'system_tags': [],
            },
            {
                'id': props['ids']['file_3'],
                'parent': props['ids']['folder'],
                'parent_path': 'user/test_folder',
                'type': 'file',
                'status': ItemStatus.REGISTERED,
                'zone': props['zone'],
                'name': 'test_file_3.txt',
                'size': 100,
                'owner': 'user',
                'container_code': props['container_code'],
                'container_type': 'project',
                'location_uri': '',
                'version': '',
                'tags': [],
                'system_tags': [],
            },
            {
                'id': props['ids_dataset']['file_dataset'],
                'parent': props['ids']['folder'],
                'parent_path': 'user/test_folder',
                'type': 'file',
                'status': ItemStatus.REGISTERED,
                'zone': 1,
                'name': 'test_file_dataset.txt',
                'size': 100,
                'owner': 'user',
                'container_code': props['container_code_dataset'],
                'container_type': 'dataset',
                'location_uri': '',
                'version': '',
                'tags': [],
                'system_tags': [],
            },
        ],
    }

    app.post('/v1/items/batch/', json=payload)

    update_payload = {
        'items': [
            {
                'id': props['ids']['file_1'],
                'status': ItemStatus.ACTIVE,
            },
            {
                'id': props['ids']['file_2'],
                'status': ItemStatus.ACTIVE,
            },
            {
                'id': props['ids']['file_3'],
                'status': ItemStatus.ACTIVE,
            },
            {
                'id': props['ids_dataset']['file_dataset'],
                'status': ItemStatus.ACTIVE,
            },
        ],
    }
    update_ids = {
        'ids': [
            props['ids']['file_1'],
            props['ids']['file_2'],
            props['ids']['file_3'],
            props['ids_dataset']['file_dataset'],
        ]
    }
    app.put('/v1/items/batch/', params=update_ids, json=update_payload)

    props_registered = {
        'zone': 0,
        'datetime': datetime.utcnow(),
        'ids': {
            'file_4': str(uuid.uuid4()),
        },
    }
    props['ids'].update({'file_4': props_registered['ids']['file_4']})
    payload = {
        'items': [
            {
                'id': props_registered['ids']['file_4'],
                'parent': props['ids']['folder'],
                'parent_path': 'user/test_folder',
                'type': 'file',
                'status': ItemStatus.REGISTERED,
                'zone': props['zone'],
                'name': 'test_file_4.txt',
                'size': 100,
                'owner': 'user',
                'container_code': props['container_code'],
                'container_type': 'project',
                'location_uri': '',
                'version': '',
                'tags': [],
                'system_tags': [],
            },
        ],
    }
    app.post('/v1/items/batch/', json=payload)

    yield props
    ids = list({**props['ids'], **props['ids_dataset']}.values())
    for item in ids:
        params = {'id': item}
        app.delete('/v1/item/', params=params)


@pytest.fixture(scope='function')
def test_collections(app) -> dict:
    props = [
        {
            'collection_name': generate_random_collection_name(),
            'owner': 'user',
            'container_code': generate_random_container_code(),
            'id': str(uuid.uuid4()),
        },
        {
            'collection_name': generate_random_collection_name(),
            'owner': 'user',
            'container_code': generate_random_container_code(),
            'id': str(uuid.uuid4()),
        },
    ]
    for i in range(0, len(props)):
        payload = {
            'id': props[i]['id'],
            'owner': props[i]['owner'],
            'container_code': props[i]['container_code'],
            'name': props[i]['collection_name'],
        }
        app.post('/v1/collection/', json=payload)

    yield props
    for i in props:
        params = {'id': i['id']}
        app.delete('/v1/collection/', params=params)


@pytest.fixture(scope='function')
def test_attribute_template(app) -> dict:
    payload = {
        'name': 'test_template',
        'project_code': 'test_project',
        'attributes': [
            {'name': 'attribute_1', 'optional': True, 'type': 'multiple_choice', 'options': ['val1', 'val2']}
        ],
    }
    response = app.post('/v1/template/', json=payload)
    attribute_template_id = response.json()['result']['id']
    yield attribute_template_id
    params = {'id': attribute_template_id}
    app.delete('/v1/template/', params=params)


@pytest.fixture(scope='function')
def test_favourites(app, test_items, test_collections) -> dict:
    props = {
        'user': generate_random_username(),
        'entity_ids': [test_items['ids']['file_1'], test_collections[0]['id']],
        'type': {test_items['ids']['file_1']: 'item', test_collections[0]['id']: 'collection'},
    }
    payload = {
        'id': props['entity_ids'][0],
        'user': props['user'],
        'type': 'item',
        'container_code': test_items['container_code'],
        'zone': test_items['zone'],
    }
    app.post('/v1/favourite/', json=payload)
    payload = {
        'id': props['entity_ids'][1],
        'user': props['user'],
        'type': 'collection',
        'container_code': test_items['container_code'],
        'zone': test_items['zone'],
    }
    app.post('/v1/favourite/', json=payload)
    yield props
    for entity_id in props['entity_ids']:
        params = {'user': props['user'], 'id': entity_id, 'type': props['type'][entity_id]}
        app.delete('/v1/favourite/', params=params)


def mock_jwt_handle(mocker, httpx_mock, platform_role: str, project_role: str):
    mock_user = {
        'username': 'user',
        'email': 'test_user@example.org',
        'role': platform_role,
        'first_name': 'test',
        'last_name': 'user',
        'realm_roles': ['test_project-admin'],
    }
    if platform_role == 'admin':
        mock_user['realm_roles'] = ['platform-admin']
    else:
        mock_user['realm_roles'] = [f'test_project-{project_role}']

    class JWTHandlerMock:
        def get_token(*args, **kwargs):
            return ''

        def decode_validate_token(*args, **kwargs):
            return ''

        async def get_current_identity(*args, **kwargs):
            return mock_user

    mocker.patch('app.routers.v1.items.dependencies.JWTHandler', return_value=JWTHandlerMock)


@pytest.fixture
def jwt_token_admin(mocker, httpx_mock):
    mock_jwt_handle(mocker, httpx_mock, 'member', 'admin')


@pytest.fixture
def jwt_token_collab(mocker, httpx_mock):
    mock_jwt_handle(mocker, httpx_mock, 'member', 'collaborator')


@pytest.fixture
def jwt_token_contrib(mocker, httpx_mock):
    mock_jwt_handle(mocker, httpx_mock, 'member', 'contributor')


@pytest.fixture
def has_admin_file_permission(httpx_mock):
    url = re.compile(rf'^{ConfigClass.AUTH_SERVICE}authorize\?role=admin&resource=file_any.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
    url = re.compile(rf'^{ConfigClass.AUTH_SERVICE}authorize\?role=admin&resource=file_any.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})


@pytest.fixture
def has_collab_file_permission(httpx_mock):
    url = re.compile(rf'^{ConfigClass.AUTH_SERVICE}authorize\?role=collaborator&resource=file_in_own_namefolder.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
    url = re.compile(rf'^{ConfigClass.AUTH_SERVICE}authorize\?role=collaborator&resource=file_any&zone=core.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
    url = re.compile(rf'^{ConfigClass.AUTH_SERVICE}authorize\?role=collaborator&resource=file_any&zone=greenroom.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': False}})


@pytest.fixture
def has_contrib_file_permission(httpx_mock):
    url = re.compile(
        rf'^{ConfigClass.AUTH_SERVICE}authorize\?role=contributor&resource=file_in_own_namefolder&zone=greenroom.*$'
    )
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
    url = re.compile(
        rf'^{ConfigClass.AUTH_SERVICE}authorize\?role=contributor&resource=file_in_own_namefolder&zone=core.*$'
    )
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': False}})
    url = re.compile(rf'^{ConfigClass.AUTH_SERVICE}authorize\?role=contributor&resource=file_any.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': False}})


@pytest.fixture(scope='session', autouse=True)
def db():
    with PostgresContainer(POSTGRES_DOCKER_IMAGE) as postgres:
        postgres_uri = postgres.get_connection_url()
        if not database_exists(postgres_uri):
            create_database(postgres_uri)
        engine = create_engine(postgres_uri)
        with engine.begin() as con:
            con.execute(text('CREATE EXTENSION IF NOT EXISTS ltree;'))

        if not engine.dialect.has_schema(engine, ConfigClass.METADATA_SCHEMA):
            engine.execute(CreateSchema(ConfigClass.METADATA_SCHEMA))

        config = Config('alembic.ini')
        ConfigClass.SQLALCHEMY_DATABASE_URI = postgres_uri
        config.set_main_option('sqlalchemy.url', postgres_uri)
        upgrade(config, 'head')
        yield postgres


@pytest.fixture()
def db_session_for_tests(app, db):
    db_url = db.get_connection_url()
    DBSessionMiddleware(app=app, db_url=db_url)
    with db_session():
        yield db_url


@pytest.fixture
def app(db):
    from app.main import app

    def get_kafka_test_client():
        return KafkaTestClient()

    app.add_middleware(DBSessionMiddleware, db_url=ConfigClass.SQLALCHEMY_DATABASE_URI)
    app.dependency_overrides[get_kafka_client] = get_kafka_test_client
    app = Client(app)
    return app


@pytest.fixture(scope='function')
def test_lineage(app) -> dict:
    """Creates a lineage of several transformations for use in unit tests."""
    item_1_id = uuid.uuid4()
    item_2_id = uuid.uuid4()

    create_item_payload = {
        'id': str(item_1_id),
        'parent': str(uuid.uuid4()),
        'parent_path': 'user/test_folder',
        'type': ItemType.FILE,
        'status': ItemStatus.REGISTERED,
        'zone': 0,
        'name': generate_random_file_name(),
        'size': 0,
        'owner': generate_random_username(),
        'container_code': generate_random_container_code(),
        'container_type': ContainerType.PROJECT,
        'location_uri': '',
        'upload_id': '',
        'version': '',
        'tags': [],
        'system_tags': [],
    }
    app.post('/v1/item/', json=create_item_payload)

    copy_to_zone_payload = {
        'id': str(item_2_id),
        'parent': str(uuid.uuid4()),
        'parent_path': 'user/test_folder',
        'type': ItemType.FILE,
        'status': ItemStatus.REGISTERED,
        'zone': 1,
        'name': generate_random_file_name(),
        'size': 0,
        'owner': generate_random_username(),
        'container_code': generate_random_container_code(),
        'container_type': ContainerType.PROJECT,
        'location_uri': '',
        'upload_id': '',
        'version': '',
        'tags': [],
        'system_tags': [],
        'tfrm_type': TransformationType.COPY_TO_ZONE,
        'tfrm_source': str(item_1_id),
    }
    app.post('/v1/item/', json=copy_to_zone_payload)

    archive_params = {
        'id': str(item_2_id),
        'status': ItemStatus.ARCHIVED,
    }
    app.patch('/v1/item/', params=archive_params)

    items_in_lineage = [item_1_id, item_2_id]
    yield items_in_lineage


@pytest.fixture
def non_mocked_hosts() -> list[str]:
    return ['testserver']
