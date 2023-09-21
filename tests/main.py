# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi.testclient import TestClient as Client

from app.clients.kafka_client import KafkaProducerClient
from app.clients.kafka_client import get_kafka_client
from app.config import ConfigClass


class KafkaTestClient(KafkaProducerClient):
    def init_connection(self) -> None:
        return None

    def close_connection(self) -> None:
        return None

    def send(self, item: dict) -> None:
        return None


def TestClient(db):
    from app.main import app

    ConfigClass.SQLALCHEMY_DATABASE_URI = db.get_connection_url()

    def get_kafka_test_client():
        return KafkaTestClient()

    app.dependency_overrides[get_kafka_client] = get_kafka_test_client
    app = Client(app)
    return app
