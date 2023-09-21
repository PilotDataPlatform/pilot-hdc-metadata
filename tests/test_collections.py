# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
import uuid

from app.config import ConfigClass
from app.models.models_items import ItemStatus

from .conftest import generate_random_collection_name


class TestCollections:
    def test_get_collection_200(self, app, test_collections):
        param = {'owner': test_collections[0]['owner'], 'container_code': test_collections[0]['container_code']}
        response = app.get('/v1/collection/search/', params=param)
        res = response.json()['result'][0]
        assert res['name'] == test_collections[0]['collection_name']

    def test_get_collection_with_invalid_sorting_400(self, app, test_collections):
        param = {
            'owner': test_collections[0]['owner'],
            'container_code': test_collections[0]['container_code'],
            'sorting': 'created_time_x',
        }
        response = app.get('/v1/collection/search/', params=param)
        assert response.status_code == 400

    def test_get_collection_by_id_200(self, app, test_collections):
        response = app.get(f'/v1/collection/{test_collections[0]["id"]}/')
        res = response.json()['result']
        assert response.status_code == 200
        assert res['name'] == test_collections[0]['collection_name']

    def test_get_collection_by_id_with_nonexistent_id_404(self, app, test_collections):
        invalid_id = str(uuid.uuid4())
        response = app.get(f'/v1/collection/{invalid_id}/')
        res = response.json()['error_msg']
        assert response.status_code == 404
        assert f'Collection id {invalid_id} does not exist' in res

    def test_delete_collection_200(self, app, test_collections):
        param = {'id': test_collections[0]['id']}
        response = app.delete('/v1/collection/', params=param)
        assert response.status_code == 200

    def test_create_collection_200(self, app):
        collection_id = str(uuid.uuid4())
        payload = {'id': collection_id, 'owner': 'owner', 'container_code': 'testproject', 'name': 'collectiontest'}
        response = app.post('/v1/collection/', json=payload)
        assert response.status_code == 200

    def test_create_collection_with_invalid_characters_in_name_422(self, app):
        collection_id = str(uuid.uuid4())
        payload = {
            'id': collection_id,
            'owner': 'owner',
            'container_code': 'testproject',
            'name': r'collectiontest\/:?*<>|',
        }
        response = app.post('/v1/collection/', json=payload)
        assert response.status_code == 422

    def test_create_collection_over_limit_400(self, app):
        for _i in range(0, ConfigClass.MAX_COLLECTIONS):
            collection_id = str(uuid.uuid4())
            payload = {
                'id': collection_id,
                'owner': 'owner',
                'container_code': 'testproject',
                'name': generate_random_collection_name(),
            }
            app.post('/v1/collection/', json=payload)

        collection_id = str(uuid.uuid4())
        payload = {
            'id': collection_id,
            'owner': 'owner',
            'container_code': 'testproject',
            'name': generate_random_collection_name(),
        }

        response = app.post('/v1/collection/', json=payload)
        res = response.json()['error_msg']
        assert response.status_code == 400
        assert f'Cannot create more than {ConfigClass.MAX_COLLECTIONS} collections' in res

    def test_create_collection_name_already_exists_409(self, app, test_collections):
        collection_id = str(uuid.uuid4())
        collection_name = test_collections[0]['collection_name']
        payload = {
            'id': collection_id,
            'owner': test_collections[0]['owner'],
            'container_code': test_collections[0]['container_code'],
            'name': test_collections[0]['collection_name'],
        }

        response = app.post('/v1/collection/', json=payload)
        res = response.json()['error_msg']
        assert response.status_code == 409
        assert f'Collection {collection_name} already exists' in res

    def test_update_collection_name_200(self, app, test_collections):
        payload = {
            'owner': test_collections[0]['owner'],
            'container_code': test_collections[0]['container_code'],
            'collections': [{'id': test_collections[0]['id'], 'name': 'updatedcollection'}],
        }
        response = app.put('/v1/collection/', json=payload)
        assert response.status_code == 200

    def test_update_collection_with_duplicate_name_in_payload_422(self, app):
        payload = {
            'owner': 'owner',
            'container_code': 'code',
            'collections': [
                {'id': str(uuid.uuid4()), 'name': 'duplicatename'},
                {'id': str(uuid.uuid4()), 'name': 'duplicatename'},
            ],
        }
        response = app.put('/v1/collection/', json=payload)
        assert response.status_code == 422

    def test_update_collection_with_name_already_exists_409(self, app, test_collections):
        payload = {
            'owner': test_collections[0]['owner'],
            'container_code': test_collections[0]['container_code'],
            'collections': [{'id': test_collections[0]['id'], 'name': test_collections[0]['collection_name']}],
        }
        response = app.put('/v1/collection/', json=payload)
        assert response.status_code == 409

    def test_update_collection_name_with_non_existent_id_404(self, app, test_collections):
        invalid_id = str(uuid.uuid4())
        payload = {
            'owner': test_collections[0]['owner'],
            'container_code': test_collections[0]['container_code'],
            'collections': [{'id': test_collections[0]['id'], 'name': 'name1'}, {'id': invalid_id, 'name': 'name2'}],
        }
        response = app.put('/v1/collection/', json=payload)
        res = response.json()['error_msg']
        assert response.status_code == 404
        assert f'Collection id: {invalid_id} does not exist' in res

    def test_get_collection_items_archived_false_200(
        self, app, test_collections, test_items, httpx_mock, jwt_token_admin
    ):
        url = re.compile(rf'^{ConfigClass.AUTH_SERVICE}authorize\?role=admin&resource=file_any.*$')
        httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
        payload = {
            'id': test_collections[0]['id'],
            'item_ids': [test_items['ids']['file_1'], test_items['ids']['file_2']],
        }
        app.post('/v1/collection/items/', json=payload)

        trash_payload = {'id': test_items['ids']['file_1'], 'status': ItemStatus.ARCHIVED}
        app.patch('/v1/item/', params=trash_payload)

        params = {'id': test_collections[0]['id'], 'container_code': 'test_project'}
        response = app.get('/v1/collection/items/', params=params)
        res = response.json()['result']
        assert response.status_code == 200
        assert len(res) == 1
        assert res[0]['name'] == 'test_file_2.txt'
        assert res[0]['status'] == ItemStatus.ACTIVE

    def test_get_collection_items_archived_true_200(
        self, app, test_collections, test_items, httpx_mock, jwt_token_admin
    ):
        url = re.compile(rf'^{ConfigClass.AUTH_SERVICE}authorize\?role=admin&resource=file_any.*$')
        httpx_mock.add_response(method='GET', url=url, json={'result': {'has_permission': True}})
        payload = {
            'id': test_collections[0]['id'],
            'item_ids': [test_items['ids']['file_1'], test_items['ids']['file_2']],
        }
        app.post('/v1/collection/items/', json=payload)

        trash_payload = {'id': test_items['ids']['file_2'], 'status': ItemStatus.ARCHIVED}
        app.patch('/v1/item/', params=trash_payload)

        params = {'id': test_collections[0]['id'], 'status': ItemStatus.ARCHIVED, 'container_code': 'test_project'}
        response = app.get('/v1/collection/items/', params=params)
        res = response.json()['result']
        assert response.status_code == 200
        assert len(res) == 1
        assert res[0]['name'] == 'test_file_2.txt'
        assert res[0]['status'] == ItemStatus.ARCHIVED

    def test_get_collection_items_archived_true_no_permission_200(
        self, app, test_collections, test_items, httpx_mock, jwt_token_admin
    ):
        item_id = str(uuid.uuid4())
        item = {
            'id': item_id,
            'parent': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            'parent_path': 'user',
            'type': 'file',
            'status': ItemStatus.REGISTERED,
            'zone': 1,
            'name': 'test_zone2.txt',
            'size': 0,
            'owner': 'admin',
            'container_code': test_collections[0]['container_code'],
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=item)

        payload = {
            'id': test_collections[0]['id'],
            'item_ids': [item['id']],
        }
        app.post('/v1/collection/items/', json=payload)

        params = {'id': test_collections[0]['id'], 'container_code': test_collections[0]['container_code']}
        response = app.get('/v1/collection/items/', params=params)
        res = response.json()['result']
        assert response.status_code == 200
        assert len(res) == 0

    def test_add_collection_items_200(self, app, test_collections, test_items):
        payload = {
            'id': test_collections[0]['id'],
            'item_ids': [test_items['ids']['file_1'], test_items['ids']['file_2']],
        }
        response = app.post('/v1/collection/items/', json=payload)
        res = response.json()['result']
        assert response.status_code == 200
        assert res['item_ids'][0] == test_items['ids']['file_1']
        assert res['item_ids'][1] == test_items['ids']['file_2']

    def test_remove_collection_items_200(self, app, test_collections, test_items):
        payload = {
            'id': test_collections[0]['id'],
            'item_ids': [test_items['ids']['file_1'], test_items['ids']['file_2']],
        }
        app.post('/v1/collection/items/', json=payload)

        params = {
            'id': test_collections[0]['id'],
            'item_ids': [test_items['ids']['file_1'], test_items['ids']['file_2']],
        }
        response = app.delete('/v1/collection/items/', json=params)
        assert response.status_code == 200
