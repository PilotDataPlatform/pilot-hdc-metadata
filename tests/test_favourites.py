# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import uuid

from app.models.models_items import ItemStatus
from tests.conftest import generate_random_container_code
from tests.conftest import generate_random_username


class TestFavourites:
    cleanup_favourites = []

    def test_get_favourites_200(self, app, test_favourites):
        response = app.get(f'/v1/favourites/{test_favourites["user"]}')
        assert response.status_code == 200
        assert response.json()['total'] == 2

    def test_get_favourites_not_found_200(self, app):
        invalid_user = 'invalid_user'
        response = app.get(f'/v1/favourites/{invalid_user}')
        assert response.json()['total'] == 0
        assert response.status_code == 200

    def test_create_favourite_item_200(self, app, test_items):
        payload = {
            'id': test_items['ids']['file_1'],
            'user': generate_random_username(),
            'type': 'item',
            'container_code': test_items['container_code'],
            'zone': test_items['zone'],
        }
        self.cleanup_favourites.append({'id': payload['id'], 'user': payload['user']})
        response = app.post('/v1/favourite/', json=payload)
        assert response.status_code == 200

    def test_create_favourite_collection_200(self, app, test_collections):
        payload = {
            'id': test_collections[0]['id'],
            'user': test_collections[0]['owner'],
            'type': 'collection',
            'container_code': test_collections[0]['container_code'],
            'zone': 0,
        }
        self.cleanup_favourites.append({'id': payload['id'], 'user': payload['user']})
        response = app.post('/v1/favourite/', json=payload)
        assert response.status_code == 200

    def test_create_favourite_item_not_found_404(self, app):
        payload = {
            'id': str(uuid.uuid4()),
            'user': generate_random_username(),
            'type': 'item',
            'container_code': generate_random_container_code(),
            'zone': 0,
        }
        response = app.post('/v1/favourite/', json=payload)
        assert response.status_code == 404

    def test_create_favourite_item_duplicate_409(self, app, test_items):
        payload = {
            'id': test_items['ids']['file_1'],
            'user': generate_random_username(),
            'type': 'item',
            'container_code': test_items['container_code'],
            'zone': test_items['zone'],
        }
        app.post('/v1/favourite/', json=payload)
        response = app.post('/v1/favourite/', json=payload)
        assert response.status_code == 409

    def test_create_favourite_item_archived_400(self, app, test_items):
        params = {
            'id': test_items['ids']['file_1'],
            'status': ItemStatus.ARCHIVED,
        }
        response = app.patch('/v1/item/', params=params)
        payload = {
            'id': test_items['ids']['file_1'],
            'user': generate_random_username(),
            'type': 'item',
            'container_code': generate_random_container_code(),
            'zone': 0,
        }
        response = app.post('/v1/favourite/', json=payload)
        assert response.status_code == 400

    def test_create_favourite_item_name_folder_400(self, app, test_items):
        payload = {
            'id': test_items['ids']['name_folder'],
            'user': generate_random_username(),
            'type': 'item',
            'container_code': test_items['container_code'],
            'zone': test_items['zone'],
        }
        response = app.post('/v1/favourite/', json=payload)
        assert response.status_code == 400

    def test_create_favourite_collection_unauthorized_403(self, app, test_collections):
        payload = {
            'id': test_collections[0]['id'],
            'user': generate_random_username(),
            'type': 'collection',
            'container_code': test_collections[0]['container_code'],
            'zone': 0,
        }
        response = app.post('/v1/favourite/', json=payload)
        assert response.status_code == 403

    def test_delete_favourite_item_200(self, app, test_favourites):
        params = {'id': test_favourites['entity_ids'][0], 'user': test_favourites['user'], 'type': 'item'}
        response = app.delete('/v1/favourite/', params=params)
        assert response.status_code == 200

    def test_delete_favourite_collection_200(self, app, test_favourites):
        params = {'id': test_favourites['entity_ids'][1], 'user': test_favourites['user'], 'type': 'collection'}
        response = app.delete('/v1/favourite/', params=params)
        assert response.status_code == 200

    def test_delete_favourite_item_wrong_type_404(self, app, test_favourites):
        params = {'id': test_favourites['entity_ids'][0], 'user': test_favourites['user'], 'type': 'collection'}
        response = app.delete('/v1/favourite/', params=params)
        assert response.status_code == 404

    def test_pin_favourite_item_200(self, app, test_favourites):
        params = {
            'id': test_favourites['entity_ids'][0],
            'user': test_favourites['user'],
            'type': 'item',
            'pinned': True,
        }
        response = app.patch('/v1/favourite/', params=params)
        assert response.status_code == 200
        assert response.json()['result']['pinned'] is True

    def test_unpin_favourite_item_200(self, app, test_favourites):
        params = {
            'id': test_favourites['entity_ids'][0],
            'user': test_favourites['user'],
            'type': 'item',
            'pinned': False,
        }
        response = app.patch('/v1/favourite/', params=params)
        assert response.status_code == 200
        assert response.json()['result']['pinned'] is False

    def test_pin_favourite_collection_200(self, app, test_favourites):
        params = {
            'id': test_favourites['entity_ids'][1],
            'user': test_favourites['user'],
            'type': 'collection',
            'pinned': True,
        }
        response = app.patch('/v1/favourite/', params=params)
        assert response.status_code == 200
        assert response.json()['result']['pinned'] is True

    def test_unpin_favourite_collection_200(self, app, test_favourites):
        params = {
            'id': test_favourites['entity_ids'][1],
            'user': test_favourites['user'],
            'type': 'collection',
            'pinned': False,
        }
        response = app.patch('/v1/favourite/', params=params)
        assert response.status_code == 200
        assert response.json()['result']['pinned'] is False

    def test_pin_favourite_item_not_found_404(self, app, test_favourites):
        params = {'id': str(uuid.uuid4()), 'user': test_favourites['user'], 'type': 'item', 'pinned': True}
        response = app.patch('/v1/favourite/', params=params)
        assert response.status_code == 404

    def test_pin_unpin_favourites_bulk_200(self, app, test_favourites):
        params = {'user': test_favourites['user']}
        payload = {
            'favourites': [
                {
                    'id': test_favourites['entity_ids'][0],
                    'user': test_favourites['user'],
                    'type': 'item',
                    'pinned': True,
                },
                {
                    'id': test_favourites['entity_ids'][1],
                    'user': test_favourites['user'],
                    'type': 'collection',
                    'pinned': False,
                },
            ]
        }
        response = app.patch('/v1/favourites/', params=params, json=payload)
        assert len(response.json()['result']) == 2
        assert response.json()['result'][0]['pinned'] is True
        assert response.json()['result'][1]['pinned'] is False
        assert response.status_code == 200

    def test_pin_unpin_favourites_bulk_not_found_404(self, app, test_favourites):
        params = {'user': test_favourites['user']}
        payload = {
            'favourites': [
                {
                    'id': test_favourites['entity_ids'][0],
                    'user': test_favourites['user'],
                    'type': 'item',
                    'pinned': True,
                },
                {
                    'id': str(uuid.uuid4()),
                    'user': test_favourites['user'],
                    'type': 'collection',
                    'pinned': False,
                },
            ]
        }
        response = app.patch('/v1/favourites/', params=params, json=payload)
        assert response.status_code == 404

    def test_delete_favourites_bulk_200(self, app, test_favourites):
        params = {'user': test_favourites['user']}
        payload = {
            'favourites': [
                {'id': test_favourites['entity_ids'][0], 'type': 'item'},
                {'id': test_favourites['entity_ids'][1], 'type': 'collection'},
            ]
        }
        response = app.delete('/v1/favourites/', params=params, json=payload)
        assert response.status_code == 200

    def test_delete_favourites_bulk_not_found_404(self, app, test_favourites):
        params = {'user': test_favourites['user']}
        payload = {
            'favourites': [
                {'id': test_favourites['entity_ids'][0], 'type': 'item'},
                {'id': str(uuid.uuid4()), 'type': 'collection'},
            ]
        }
        response = app.delete('/v1/favourites/', params=params, json=payload)
        assert response.status_code == 404

    def test_favourite_field_true_in_items_search_200(
        self, app, test_items, jwt_token_admin, has_admin_file_permission
    ):
        user = generate_random_username()
        payload = {
            'id': test_items['ids']['file_1'],
            'user': user,
            'type': 'item',
            'container_code': test_items['container_code'],
            'zone': test_items['zone'],
        }
        self.cleanup_favourites.append({'id': payload['id'], 'user': payload['user']})
        app.post('/v1/favourite/', json=payload)
        params = {
            'parent_path': 'user/test_folder',
            'name': 'test_file_1.txt',
            'status': ItemStatus.ACTIVE,
            'zone': 0,
            'container_code': test_items['container_code'],
            'recursive': False,
            'fav_user': user,
        }
        response = app.get('/v1/items/search/', params=params)
        assert response.status_code == 200
        assert len(response.json()['result']) > 0
        assert response.json()['result'][0]['favourite'] is True

    def test_favourite_field_false_in_items_search_200(
        self, app, test_items, jwt_token_admin, has_admin_file_permission
    ):
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
        assert len(response.json()['result']) > 0
        assert response.json()['result'][0]['favourite'] is False

    def test_favourite_field_true_in_collections_get_200(self, app, test_collections):
        payload = {
            'id': test_collections[0]['id'],
            'user': test_collections[0]['owner'],
            'type': 'collection',
            'container_code': test_collections[0]['container_code'],
            'zone': 0,
        }
        self.cleanup_favourites.append({'id': payload['id'], 'user': payload['user']})
        app.post('/v1/favourite/', json=payload)
        params = {'owner': test_collections[0]['owner'], 'container_code': test_collections[0]['container_code']}
        response = app.get('/v1/collection/search/', params=params)
        assert response.status_code == 200
        assert len(response.json()['result']) > 0
        assert response.json()['result'][0]['favourite'] is True

    def test_favourite_field_false_in_collections_get_200(self, app, test_collections):
        params = {'owner': test_collections[0]['owner'], 'container_code': test_collections[0]['container_code']}
        response = app.get('/v1/collection/search/', params=params)
        assert response.status_code == 200
        assert len(response.json()['result']) > 0
        assert response.json()['result'][0]['favourite'] is False
