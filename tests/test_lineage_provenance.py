# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import uuid

from app.models.models_items import ContainerType
from app.models.models_items import ItemStatus
from app.models.models_items import ItemType
from app.models.models_lineage_provenance import TransformationType
from app.routers.v1.items.crud_lineage_provenance import get_provenance_snapshots_by_item_id
from tests.conftest import generate_random_container_code
from tests.conftest import generate_random_file_name
from tests.conftest import generate_random_username


class TestLineageProvenance:
    def test_no_transformation_create_item_provenance_exists(self, db_session_for_tests, app):
        produced_item_id = uuid.uuid4()
        payload = {
            'id': str(produced_item_id),
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
        app.post('/v1/item/', json=payload)
        provenance_snapshots = get_provenance_snapshots_by_item_id(produced_item_id)
        assert len(provenance_snapshots) == 1
        provenance_snapshot = provenance_snapshots[0]
        assert not provenance_snapshot.lineage_id

    def test_no_transformation_update_item_provenance_exists(self, db_session_for_tests, app, test_items):
        produced_item_id = test_items['ids']['file_1']
        params = {'id': produced_item_id}
        payload = {'name': 'test_file_updated.txt'}
        app.put('/v1/item/', json=payload, params=params)
        provenance_snapshots = get_provenance_snapshots_by_item_id(produced_item_id)
        assert len(provenance_snapshots) > 0
        provenance_snapshot = provenance_snapshots[-1]
        assert not provenance_snapshot.lineage_id

    def test_transformations_lineage_provenance_exists(self, app, test_lineage):
        response = app.get(f'/v1/lineage/{test_lineage[1]}/')
        assert response.status_code == 200
        lineage = response.json()['result']['lineage']
        provenance = response.json()['result']['provenance']
        assert len(lineage) == 2
        transformations = list(lineage.values())
        assert transformations[0]['tfrm_type'] == str(TransformationType.COPY_TO_ZONE)
        assert transformations[0]['consumes'] == [str(test_lineage[0])]
        assert transformations[0]['produces'] == [str(test_lineage[1])]
        assert transformations[1]['tfrm_type'] == str(TransformationType.ARCHIVE)
        assert transformations[1]['consumes'] == [str(test_lineage[1])]
        assert transformations[1]['produces'] is None
        assert len(provenance) == 2
        snapshot_ids = list(provenance.keys())
        assert snapshot_ids[0] == str(test_lineage[0])
        assert snapshot_ids[1] == str(test_lineage[1])
