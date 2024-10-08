# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import io
import uuid
from datetime import timezone

import pytest
from fastavro import schemaless_reader
from fastavro import validate

from app.models.models_items import ItemStatus
from tests.conftest import generate_random_container_code
from tests.main import KafkaTestClient

template_id = str(uuid.uuid4())
template_name = 'test_template'


@pytest.fixture
def sample_item():
    item = {
        'id': str(uuid.uuid4()),
        'parent': str(uuid.uuid4()),
        'parent_path': 'user/test_folder',
        'restore_path': None,
        'status': ItemStatus.ACTIVE,
        'type': 'file',
        'zone': 0,
        'name': 'test_file_1.txt',
        'size': 100,
        'owner': 'user',
        'container_code': generate_random_container_code(),
        'container_type': 'project',
        'created_time': '2022-10-19 14:50:42.086273',
        'last_updated_time': '2022-10-19 14:50:42.086282',
        'storage': {'id': str(uuid.uuid4()), 'location_uri': '', 'version': ''},
        'extended': {
            'id': str(uuid.uuid4()),
            'extra': {'tags': [], 'system_tags': [], 'attributes': {template_id: {'attr1': 'value'}}},
            'favourite': False,
        },
    }
    yield item


class TestKafka:
    client = KafkaTestClient()

    def test_load_schema(self):
        schema = self.client._load_schema()
        assert schema['type'] == 'record'

    def test_format_item_without_attributes(self, sample_item):
        sample_item['extended']['extra']['attributes'] = {}
        formatted = self.client._format_item(sample_item)
        assert formatted['id'] == sample_item['id']
        assert formatted['created_time'].tzinfo == timezone.utc
        assert formatted['last_updated_time'].tzinfo == timezone.utc

    def test_format_item_with_attributes(self, sample_item, mocker):
        mocker.patch(
            'app.clients.kafka_client.KafkaProducerClient._get_attribute_template',
            return_value={'name': template_name, 'id': template_id},
        )

        formatted = self.client._format_item(sample_item)
        assert formatted['id'] == sample_item['id']
        assert formatted['created_time'].tzinfo == timezone.utc
        assert formatted['last_updated_time'].tzinfo == timezone.utc
        assert formatted['extended']['template_id'] == template_id
        assert formatted['extended']['template_name'] == template_name

    def test_validate_serialized_message(self, sample_item, mocker):
        mocker.patch(
            'app.clients.kafka_client.KafkaProducerClient._get_attribute_template',
            return_value={'name': template_name, 'id': template_id},
        )

        message = self.client._serialize_msg(sample_item)
        schema = self.client._load_schema()
        deserialized = schemaless_reader(io.BytesIO(message), schema)
        is_valid = validate(deserialized, schema, raise_errors=False)
        assert is_valid

    def test_serialize_invalid_message(self, sample_item, mocker):
        mocker.patch(
            'app.clients.kafka_client.KafkaProducerClient._get_attribute_template',
            return_value={'name': template_name, 'id': template_id},
        )

        del sample_item['zone']
        with pytest.raises(ValueError):
            self.client._serialize_msg(sample_item)
