# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import uuid
from datetime import datetime

import pytest

from app.models.models_items import ContainerType
from app.models.models_items import ItemStatus
from tests.conftest import generate_random_username


class TestItems:
    def test_get_item_by_id_200(self, app, test_items):
        response = app.get(f'/v1/item/{test_items["ids"]["file_1"]}/')
        assert response.status_code == 200

    def test_get_item_by_location_200(self, app, test_items, jwt_token_admin, has_admin_file_permission):
        params = {
            'parent_path': 'user/test_folder',
            'name': 'test_file_1.txt',
            'status': ItemStatus.ACTIVE,
            'zone': 0,
            'container_code': test_items['container_code'],
            'recursive': False,
        }
        response = app.get('/v1/items/search/', params=params)
        assert response.status_code == 200
        assert response.json()['total'] == 1

    def test_get_item_by_location_dataset_200(self, app, test_items, jwt_token_collab):
        params = {
            'parent_path': 'user/test_folder',
            'name': 'test_file_dataset.txt',
            'status': ItemStatus.ACTIVE,
            'zone': 1,
            'container_type': 'dataset',
            'container_code': test_items['container_code_dataset'],
            'recursive': False,
        }
        response = app.get('/v1/items/search/', params=params)
        assert response.status_code == 200
        assert response.json()['total'] == 1

    def test_get_archived_item_by_location_200(self, app, test_items, jwt_token_admin, has_admin_file_permission):
        params = {
            'id': test_items['ids']['file_3'],
            'status': ItemStatus.ARCHIVED,
        }
        app.patch('/v1/item/', params=params)
        params = {
            'restore_path': 'user/test_folder',
            'name': 'test_file_3.txt',
            'status': ItemStatus.ARCHIVED,
            'zone': 0,
            'container_code': test_items['container_code'],
            'recursive': False,
        }
        response = app.get('/v1/items/search/', params=params)
        assert response.status_code == 200
        assert response.json()['total'] == 1

    def test_get_registered_item_by_location_200(self, app, test_items, jwt_token_admin, has_admin_file_permission):
        params = {
            'parent_path': 'user/test_folder',
            'name': 'test_file_4.txt',
            'status': ItemStatus.REGISTERED,
            'zone': 0,
            'container_code': test_items['container_code'],
            'recursive': False,
        }
        response = app.get('/v1/items/search/', params=params)
        assert response.status_code == 200
        assert response.json()['total'] == 1

    @pytest.mark.parametrize('item_name', [('user'), ('User')])
    def test_get_item_by_location_filter_by_name_case_insensitive(
        self, app, item_name, test_items, jwt_token_admin, has_admin_file_permission
    ):
        params = {
            'name': item_name,
            'container_code': test_items['container_code'],
        }
        response = app.get('/v1/items/search/', params=params)
        items = response.json()['result']

        assert response.status_code == 200
        assert len(items) == 1
        assert items[0]['name'] == item_name.lower()

    def test_get_item_by_location_with_auth_user_greenroom(
        self, app, test_items, jwt_token_admin, has_admin_file_permission
    ):
        params = {
            'zone': 0,
            'parent_path': 'user',
            'container_code': test_items['container_code'],
            'status': ItemStatus.ACTIVE,
        }
        response = app.get('/v1/items/search/', params=params)
        items = response.json()['result']

        assert response.status_code == 200
        assert len(items) == 1

    @pytest.mark.parametrize('zone', [0, 1])
    def test_get_item_by_location_collab_namefolder_level(
        self, app, test_items, jwt_token_collab, has_collab_file_permission, zone
    ):
        item_id = str(uuid.uuid4())
        payload = {
            'id': item_id,
            'parent': None,
            'parent_path': None,
            'type': 'name_folder',
            'status': ItemStatus.ACTIVE,
            'zone': 1,
            'name': 'user',
            'size': 0,
            'owner': 'admin',
            'container_code': 'test_project',
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)

        params = {
            'zone': zone,
            'container_code': test_items['container_code'],
            'status': ItemStatus.ACTIVE,
        }
        response = app.get('/v1/items/search/', params=params)
        items = response.json()['result']

        assert response.status_code == 200
        assert len(items) == 1
        assert items[0]['name'] == 'user'

    @pytest.mark.parametrize('zone', [0, 1])
    def test_get_item_by_location_contrib_namefolder_level(
        self, app, test_items, jwt_token_contrib, has_contrib_file_permission, zone
    ):
        item_id = str(uuid.uuid4())
        payload = {
            'id': item_id,
            'parent': None,
            'parent_path': None,
            'type': 'name_folder',
            'status': ItemStatus.ACTIVE,
            'zone': 1,
            'name': 'user',
            'size': 0,
            'owner': 'admin',
            'container_code': 'test_project',
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)

        params = {
            'zone': zone,
            'container_code': test_items['container_code'],
            'status': ItemStatus.ACTIVE,
        }
        response = app.get('/v1/items/search/', params=params)
        items = response.json()['result']

        assert response.status_code == 200
        if zone == 0:
            assert len(items) == 1
            assert items[0]['name'] == 'user'
        else:
            assert len(items) == 0

    def test_get_item_by_location_with_auth_user_core(
        self, app, test_items, jwt_token_collab, has_collab_file_permission
    ):
        item_id = str(uuid.uuid4())
        payload = {
            'id': item_id,
            'parent': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            'parent_path': 'user',
            'type': 'file',
            'status': ItemStatus.REGISTERED,
            'zone': 1,
            'name': 'test_zone.txt',
            'size': 0,
            'owner': 'admin',
            'container_code': 'test_project',
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)

        update_payload = {
            'items': [
                {
                    'id': item_id,
                    'status': ItemStatus.ACTIVE,
                }
            ]
        }
        response = app.put('/v1/items/batch/', params={'ids': [item_id]}, json=update_payload)

        params = {
            'zone': 1,
            'parent_path': 'user',
            'container_code': 'test_project',
            'status': ItemStatus.ACTIVE,
        }
        response = app.get('/v1/items/search/', params=params)
        items = response.json()['result']

        assert response.status_code == 200
        assert len(items) == 1

    def test_get_item_by_location_with_auth_user_contrib(
        self, app, test_items, jwt_token_contrib, has_contrib_file_permission
    ):
        params = {
            'zone': 0,
            'parent_path': 'user',
            'status': ItemStatus.ACTIVE,
            'container_code': 'test_project',
        }

        response = app.get('/v1/items/search/', params=params)
        items = response.json()['result']

        assert response.status_code == 200
        assert len(items) == 1

    def test_get_item_by_location_with_auth_user_admin(
        self, app, test_items, jwt_token_admin, has_admin_file_permission
    ):
        params = {
            'zone': 0,
            'parent_path': 'user',
            'container_code': 'test_project',
            'status': ItemStatus.ACTIVE,
        }
        response = app.get('/v1/items/search/', params=params)
        items = response.json()['result']

        assert response.status_code == 200
        assert len(items) == 1

    def test_get_item_by_location_filter_by_name_substring(
        self, app, test_items, jwt_token_admin, has_admin_file_permission
    ):
        partial_name = 'file'
        params = {
            'name': partial_name,
            'recursive': True,
            'container_code': 'test_project',
        }
        response = app.get('/v1/items/search/', params=params)
        items = response.json()['result']

        assert response.status_code == 200
        items_name = [item['name'] for item in items]
        assert len(items) == 3
        for item_name in items_name:
            assert partial_name in item_name

    def test_get_item_by_location_filter_by_last_updated_date_range_200(
        self, app, test_items, jwt_token_admin, has_admin_file_permission
    ):
        params = {
            'last_updated_start': test_items['datetime'],
            'last_updated_end': datetime.utcnow(),
            'recursive': True,
            'container_code': 'test_project',
        }
        response = app.get('/v1/items/search/', params=params)
        items = response.json()['result']

        params = {
            'last_updated_start': test_items['datetime'],
            'last_updated_end': datetime.utcnow(),
            'status': ItemStatus.REGISTERED,
            'recursive': True,
            'container_code': 'test_project',
        }
        response = app.get('/v1/items/search/', params=params)
        registered_items = response.json()['result']
        items.extend(registered_items)
        items_ids = [item['id'] for item in items]

        assert response.status_code == 200
        assert len(items) == len(test_items['ids'])
        assert set(items_ids).issubset(test_items['ids'].values())

    def test_get_item_by_location_filter_by_last_updated_date_out_of_range_200(
        self, app, test_items, jwt_token_admin, has_admin_file_permission
    ):
        params = {
            'last_updated_start': datetime(1995, 7, 22, 20, 45, 23, 438749),
            'last_updated_end': datetime(2010, 7, 22, 20, 45, 23, 438749),
            'recursive': True,
            'container_code': test_items['container_code'],
        }
        response = app.get('/v1/items/search/', params=params)
        assert response.status_code == 200
        assert response.json()['total'] == 0

    def test_get_item_by_location_missing_zone_200(self, app, test_items, jwt_token_admin, has_admin_file_permission):
        params = {
            'parent_path': 'user/test_folder',
            'name': 'test_file_1.txt',
            'status': ItemStatus.ACTIVE,
            'container_code': test_items['container_code'],
            'recursive': False,
        }
        response = app.get('/v1/items/search/', params=params)
        assert response.status_code == 200
        assert response.json()['total'] == 1

    def test_get_item_by_location_favourited_by_other_user_200(
        self, app, test_items, jwt_token_admin, has_admin_file_permission
    ):
        payload = {
            'id': test_items['ids']['file_1'],
            'user': generate_random_username(),
            'type': 'item',
            'container_code': test_items['container_code'],
            'zone': test_items['zone'],
        }
        response = app.post('/v1/favourite/', json=payload)
        params = {
            'parent_path': 'user/test_folder',
            'name': 'test_file_1.txt',
            'status': ItemStatus.ACTIVE,
            'zone': 0,
            'container_code': test_items['container_code'],
            'recursive': False,
            'fav_user': generate_random_username(),
        }
        response = app.get('/v1/items/search/', params=params)
        assert response.status_code == 200
        assert response.json()['total'] == 1

    def test_get_items_by_id_batch_200(self, app, test_items):
        params = {'ids': [test_items['ids']['name_folder'], test_items['ids']['folder'], test_items['ids']['file_1']]}
        response = app.get('/v1/items/batch/', params=params)
        assert response.status_code == 200

    def test_create_item_200(self, app):
        item_id = str(uuid.uuid4())
        payload = {
            'id': item_id,
            'parent': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            'parent_path': 'user/test_folder',
            'type': 'file',
            'status': ItemStatus.REGISTERED,
            'zone': 0,
            'name': 'test_file.txt',
            'size': 0,
            'owner': 'admin',
            'container_code': 'create_item_200',
            'container_type': 'project',
            'location_uri': '',
            'upload_id': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 200

    def test_create_item_200_with_storage_info(self, app):
        item_id = str(uuid.uuid4())
        payload = {
            'id': item_id,
            'parent': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            'parent_path': 'user/test_folder',
            'type': 'file',
            'status': ItemStatus.REGISTERED,
            'zone': 0,
            'name': 'test_create_item_200_with_storage_info.txt',
            'size': 0,
            'owner': 'admin',
            'container_code': 'create_item_200',
            'container_type': 'project',
            'location_uri': 'test/path',
            'upload_id': 'test_id',
            'version': 'test_version',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 200

        item_info = response.json().get('result', {})
        storage_info = item_info.get('storage', None)
        assert storage_info is not None
        assert storage_info.get('location_uri') == 'test/path'
        assert storage_info.get('version') == 'test_version'
        assert storage_info.get('upload_id') == 'test_id'

    def test_create_items_batch_200(self, app):
        item_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        payload = {
            'items': [
                {
                    'id': item_ids[0],
                    'parent': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                    'parent_path': 'user/folder',
                    'type': 'file',
                    'zone': 0,
                    'name': 'file_1.txt',
                    'size': 0,
                    'owner': 'user',
                    'container_code': 'create_items_batch',
                    'container_type': 'project',
                    'location_uri': '',
                    'version': '',
                    'tags': [],
                    'system_tags': [],
                },
                {
                    'id': item_ids[1],
                    'parent': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                    'parent_path': 'user/folder',
                    'type': 'file',
                    'zone': 0,
                    'name': 'file_2.txt',
                    'size': 0,
                    'owner': 'user',
                    'container_code': 'create_items_batch',
                    'container_type': 'project',
                    'location_uri': '',
                    'version': '',
                    'tags': [],
                    'system_tags': [],
                },
            ]
        }
        response = app.post('/v1/items/batch/', json=payload)
        assert response.status_code == 200

    def test_create_file_item_as_active_failed(self, app, test_items):
        item_id = str(uuid.uuid4())
        payload = {
            'id': item_id,
            'parent': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            'parent_path': 'user',
            'type': 'file',
            'status': ItemStatus.ACTIVE,
            'zone': 1,
            'name': 'test_zone.txt',
            'size': 0,
            'owner': 'admin',
            'container_code': 'create_item_200',
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)

        assert response.status_code == 400

    def test_create_item_wrong_type_422(self, app):
        payload = {
            'id': str(uuid.uuid4()),
            'parent': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            'parent_path': 'user/test_folder',
            'type': 'invalid',
            'zone': 0,
            'name': 'test_file.txt',
            'size': 0,
            'owner': 'admin',
            'container_code': 'create_item_200',
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 422

    def test_create_item_with_null_size_422(self, app):
        payload = {
            'id': str(uuid.uuid4()),
            'parent': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            'parent_path': 'user/test_folder',
            'type': 'folder',
            'zone': 0,
            'name': 'my_empty_folder',
            'size': None,
            'owner': 'admin',
            'container_code': 'create_item_200',
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 422
        assert response.json()['detail'][0]['loc'] == ['body', 'size']

    def test_create_item_wrong_container_type_422(self, app):
        payload = {
            'id': str(uuid.uuid4()),
            'parent': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            'parent_path': 'user/test_folder',
            'type': 'file',
            'zone': 0,
            'name': 'test_file.txt',
            'size': 0,
            'owner': 'admin',
            'container_code': 'create_item_200',
            'container_type': 'invalid',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 422

    def test_create_name_folder_with_parent_422(self, app):
        payload = {
            'parent': str(uuid.uuid4()),
            'parent_path': None,
            'type': 'name_folder',
            'zone': 0,
            'name': 'user',
            'size': 0,
            'owner': 'user',
            'container_code': 'test_project',
            'container_type': 'project',
            'location_uri': '',
            'version': '',
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 422

    def test_file_empty_parent_project_422(self, app):
        item_id = str(uuid.uuid4())
        payload = {
            'id': item_id,
            'parent': None,
            'parent_path': '',
            'type': 'file',
            'zone': 0,
            'name': 'test_file_no_parent.txt',
            'size': 0,
            'owner': 'admin',
            'container_code': 'create_item_200',
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 422

    def test_active_file_with_duplicate_name_return_409(self, app, test_items):
        payload = {
            'id': test_items['ids']['file_1'],
            'parent': test_items['ids']['folder'],
            'parent_path': 'user/test_folder',
            'type': 'file',
            'zone': test_items['zone'],
            'name': 'test_file_1.txt',
            'size': 100,
            'owner': 'user',
            'container_code': test_items['container_code'],
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 409

    def test_registered_file_with_duplicate_name_return_409(self, app, test_items):
        payload = {
            'id': test_items['ids']['file_3'],
            'parent': test_items['ids']['folder'],
            'parent_path': 'user/test_folder',
            'type': 'file',
            'status': ItemStatus.REGISTERED,
            'zone': test_items['zone'],
            'name': 'test_file_3.txt',
            'size': 100,
            'owner': 'user',
            'container_code': test_items['container_code'],
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 409

    def test_active_folder_with_duplicate_name_return_409(self, app, test_items):
        payload = {
            'id': test_items['ids']['folder'],
            'parent': test_items['ids']['name_folder'],
            'parent_path': 'user',
            'type': 'folder',
            'status': ItemStatus.ACTIVE,
            'zone': test_items['zone'],
            'name': 'test_folder',
            'size': 0,
            'owner': 'user',
            'container_code': test_items['container_code'],
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 409

    def test_file_empty_parent_dataset_200(self, app):
        item_id = str(uuid.uuid4())
        payload = {
            'id': item_id,
            'parent': None,
            'parent_path': '',
            'type': 'file',
            'zone': 0,
            'name': 'test_file_no_parent.txt',
            'size': 0,
            'owner': 'admin',
            'container_code': 'dataset_empty_parent_200',
            'container_type': 'dataset',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 200

    def test_folder_empty_parent_dataset_200(self, app):
        item_id = str(uuid.uuid4())
        payload = {
            'id': item_id,
            'parent': None,
            'parent_path': '',
            'type': 'folder',
            'zone': 0,
            'name': 'test_folder_no_parent',
            'size': 0,
            'owner': 'admin',
            'container_code': 'dataset_empty_parent_200',
            'container_type': 'dataset',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        response = app.post('/v1/item/', json=payload)
        assert response.status_code == 200

    def test_update_item_200(self, app, test_items):
        params = {'id': test_items['ids']['file_1']}
        payload = {'name': 'test_file_updated.txt'}
        response = app.put('/v1/item/', json=payload, params=params)
        assert response.status_code == 200
        assert response.json()['result']['name'] == 'test_file_updated.txt'

    def test_update_items_batch_200(self, app, test_items):
        params = {'ids': [test_items['ids']['name_folder'], test_items['ids']['folder'], test_items['ids']['file_1']]}
        payload = {'items': [{'owner': 'user_2'}, {'tags': ['update_items_batch']}, {'size': 500}]}
        response = app.put('/v1/items/batch/', params=params, json=payload)
        assert response.status_code == 200
        assert response.json()['result'][0]['owner'] == 'user_2'
        assert response.json()['result'][1]['extended']['extra']['tags'] == ['update_items_batch']
        assert response.json()['result'][2]['size'] == 500

    def test_update_REGISTERED_items_fail(self, app, test_items):
        params = {'ids': [test_items['ids']['file_4']]}
        payload = {'items': [{'owner': 'user_2', 'tags': ['update_items_batch'], 'size': 500}]}
        response = app.put('/v1/items/batch/', params=params, json=payload)
        assert response.status_code == 400

    def test_update_item_wrong_type_422(self, app, test_items):
        params = {'id': test_items['ids']['file_1']}
        payload = {'type': 'invalid'}
        response = app.put('/v1/item/', json=payload, params=params)
        assert response.status_code == 422

    def test_update_item_wrong_container_type_422(self, app, test_items):
        params = {'id': test_items['ids']['file_1']}
        payload = {'container_type': 'invalid'}
        response = app.put('/v1/item/', json=payload, params=params)
        assert response.status_code == 422

    def test_trash_item_200(self, app, test_items):
        params = {
            'id': test_items['ids']['file_1'],
            'status': ItemStatus.ARCHIVED,
        }
        response = app.patch('/v1/item/', params=params)
        assert response.status_code == 200
        assert response.json()['result'][0]['status'] == ItemStatus.ARCHIVED

    def test_restore_item_200(self, app, test_items):
        params = {
            'id': test_items['ids']['file_1'],
            'status': ItemStatus.ACTIVE,
        }
        response = app.patch('/v1/item/', params=params)
        assert response.status_code == 200
        assert response.json()['result'][0]['status'] == ItemStatus.ACTIVE

    def test_trash_folder_with_children_200(self, app, test_items):
        params = {
            'id': test_items['ids']['folder'],
            'status': ItemStatus.ARCHIVED,
        }
        response = app.patch('/v1/item/', params=params)
        assert response.status_code == 200
        assert len(response.json()['result']) == 4
        for i in range(4):
            assert response.json()['result'][i]['status'] == ItemStatus.ARCHIVED

    def test_restore_folder_with_children_200(self, app, test_items):
        params = {
            'id': test_items['ids']['folder'],
            'status': ItemStatus.ACTIVE,
        }
        response = app.patch('/v1/item/', params=params)
        assert response.status_code == 200
        assert len(response.json()['result']) == 4
        for i in range(4):
            assert response.json()['result'][i]['status'] == ItemStatus.ACTIVE

    def test_rename_item_on_conflict_200(self, app, test_items):
        params = {
            'id': test_items['ids']['file_1'],
            'status': ItemStatus.ARCHIVED,
        }
        app.patch('/v1/item/', params=params)
        item_id = str(uuid.uuid4())
        payload = {
            'id': item_id,
            'parent': test_items['ids']['folder'],
            'parent_path': 'user/test_folder',
            'type': 'file',
            'zone': 0,
            'name': 'test_file_1.txt',
            'size': 100,
            'owner': 'user',
            'container_code': test_items['container_code'],
            'container_type': 'project',
            'location_uri': '',
            'version': '',
            'tags': [],
            'system_tags': [],
        }
        app.post('/v1/item/', json=payload)
        update_payload = {
            'items': [
                {
                    'id': item_id,
                    'status': ItemStatus.ACTIVE,
                }
            ]
        }
        response = app.put('/v1/items/batch/', params={'ids': [item_id]}, json=update_payload)

        params = {
            'id': test_items['ids']['file_1'],
            'status': ItemStatus.ACTIVE,
        }
        response = app.patch('/v1/item/', params=params)
        assert response.status_code == 200
        assert 'test_file_1_' in response.json()['result'][0]['name']
        assert len(response.json()['result'][0]['name']) > len('test_file_1.txt')

    def test_delete_item_200(self, app, test_items):
        params = {'id': test_items['ids']['file_1']}
        response = app.delete('/v1/item/', params=params)
        assert response.status_code == 200

    def test_delete_items_by_id_batch_200(self, app, test_items):
        params = {'ids': [test_items['ids']['file_2'], test_items['ids']['file_3']]}
        response = app.delete('/v1/items/batch/', params=params)
        assert response.status_code == 200

    def test_bequeath_to_children_200(self, app, test_items, test_attribute_template):
        params = {'id': test_items['ids']['folder']}
        payload = {
            'attribute_template_id': test_attribute_template,
            'attributes': {'attribute_1': 'val1'},
            'system_tags': ['copied-to-core'],
        }
        response = app.put('/v1/items/batch/bequeath/', params=params, json=payload)
        assert response.status_code == 200
        assert len(response.json()['result']) == 3
        assert (
            response.json()['result'][0]['extended']['extra']['attributes'][test_attribute_template]
            == payload['attributes']
        )
        assert response.json()['result'][0]['extended']['extra']['system_tags'] == payload['system_tags']

    def test_get_one_file_by_location_200(self, app, test_items):
        params = {
            'name': 'test_file_1.txt',
            'parent_path': 'user/test_folder',
            'container_code': test_items['container_code'],
            'container_type': ContainerType.PROJECT,
            'zone': test_items['zone'],
            'status': ItemStatus.ACTIVE,
        }
        response = app.get('/v1/item/', params=params)
        item = response.json()['result']

        assert response.status_code == 200
        assert item['id'] == test_items['ids']['file_1']

    def test_get_one_folder_by_location_200(self, app, test_items):
        params = {
            'name': 'test_folder',
            'parent_path': 'user',
            'container_code': test_items['container_code'],
            'container_type': ContainerType.PROJECT,
            'zone': test_items['zone'],
            'status': ItemStatus.ACTIVE,
        }
        response = app.get('/v1/item/', params=params)
        item = response.json()['result']

        assert response.status_code == 200
        assert item['id'] == test_items['ids']['folder']

    def test_get_one_file_by_location_404(self, app, test_items):
        params = {
            'name': 'not_exists',
            'parent_path': 'user/test_folder',
            'container_code': test_items['container_code'],
            'container_type': ContainerType.PROJECT,
            'zone': test_items['zone'],
            'status': ItemStatus.ACTIVE,
        }
        response = app.get('/v1/item/', params=params)

        assert response.status_code == 404

    def test_get_one_file_by_location_invalid_container_type_422(self, app, test_items):
        params = {
            'name': 'test_file_1.txt',
            'parent_path': 'user/test_folder',
            'container_code': test_items['container_code'],
            'container_type': 'invalid',
            'zone': test_items['zone'],
            'status': ItemStatus.ACTIVE,
        }
        response = app.get('/v1/item/', params=params)

        assert response.status_code == 422
