# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from datetime import timezone
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from fastapi_sqlalchemy import db
from fastavro import schema
from fastavro import schemaless_writer
from kafka import KafkaProducer
from kafka.errors import KafkaError

from app.config import ConfigClass
from app.logger import logger
from app.models.sql_attribute_templates import AttributeTemplateModel


class KafkaProducerClient:
    producer = None
    schema_path = 'app/schemas/metadata.items.avsc'

    def __init__(self):
        self.schema = self._load_schema()

    def init_connection(self) -> None:
        """
        Summary:
            function for producer to inititate the kafka connection.
        """
        if not self.producer:
            try:
                self.producer = KafkaProducer(bootstrap_servers=[ConfigClass.KAFKA_URL])
            except Exception as e:
                logger.exception(f'Kafka connection error {e}')
                self.producer = None
                raise e

    def close_connection(self) -> None:
        """
        Summary:
            function for producer to close the kafka connection.
        """
        if self.producer is not None:
            logger.info('Closing the kafka producer')
            self.producer.close()

    def _load_schema(self) -> dict:
        """
        Summary:
            function for loading metadata avro schema.
        """
        try:
            project_root = Path(__file__).parents[2]
            loaded_schema = schema.load_schema(project_root / self.schema_path)
            logger.info('Successfully loaded avro schema')
            return loaded_schema
        except Exception as e:
            logger.exception('Error loading avro schema')
            raise e

    def _get_attribute_template(self, template_id) -> dict:
        """
        Summary:
                function for querying attribute template by template id.
        """
        query = db.session.query(AttributeTemplateModel).filter_by(id=template_id)
        template = query.first().to_dict()
        return template

    def _format_item(self, item: dict) -> dict:
        """
        Summary:
            function for formatting item date and template name fields before serialization.
        """
        try:
            formatted = item.copy()
            formatted['created_time'] = datetime.strptime(formatted['created_time'], '%Y-%m-%d %H:%M:%S.%f').replace(
                tzinfo=timezone.utc
            )
            formatted['last_updated_time'] = datetime.strptime(
                formatted['last_updated_time'], '%Y-%m-%d %H:%M:%S.%f'
            ).replace(tzinfo=timezone.utc)

            if formatted['extended']['extra']['attributes']:
                attr = formatted['extended']['extra']['attributes']
                template = self._get_attribute_template(template_id=list(attr.keys())[0])
                formatted['extended']['template_name'] = template['name']
                formatted['extended']['template_id'] = template['id']
            return formatted

        except Exception as e:
            logger.exception(f'Error for formatting item: {item["id"]}')
            raise e

    def _serialize_msg(self, item: dict) -> bytes:
        """
        Summary:
            function for avro-serialization of item.
        """
        try:
            bio = BytesIO()
            message = self._format_item(item)
            schemaless_writer(bio, self.schema, message)
            serialized_message = bio.getvalue()
            logger.info(f'Successfully serialized metadata item: {item["id"]}')
            return serialized_message
        except ValueError as ve:
            logger.exception(f'Error of avro serialization for item: {item["id"]}')
            raise ve

    def send(self, item: dict) -> None:
        """
        Summary:
            function for sending message to kafka topic.
        """
        try:
            serialized_msg = self._serialize_msg(item)
            self.producer.send(ConfigClass.KAFKA_TOPIC, serialized_msg)
            self.producer.flush()
            logger.info(f'Sent Kafka message to topic: {ConfigClass.KAFKA_TOPIC}')
        except KafkaError as ke:
            logger.exception('Error sending metadata event to Kafka')
            raise ke


kafka_client = KafkaProducerClient()


@lru_cache(1)
def get_kafka_client() -> KafkaProducerClient:
    kafka_client.init_connection()
    return kafka_client


__all__ = 'get_kafka_client'
