# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import base64
import logging
from functools import lru_cache
from typing import Any
from typing import Dict
from typing import Optional

from common import VaultClient
from pydantic import BaseSettings
from pydantic import Extra


class VaultConfig(BaseSettings):
    """Store vault related configuration."""

    APP_NAME: str = 'metadata'
    CONFIG_CENTER_ENABLED: bool = False

    VAULT_URL: Optional[str]
    VAULT_CRT: Optional[str]
    VAULT_TOKEN: Optional[str]

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


def load_vault_settings(settings: BaseSettings) -> Dict[str, Any]:
    config = VaultConfig()

    if not config.CONFIG_CENTER_ENABLED:
        return {}

    client = VaultClient(config.VAULT_URL, config.VAULT_CRT, config.VAULT_TOKEN)
    return client.get_from_vault(config.APP_NAME)


class Settings(BaseSettings):
    version = '2.2.0'
    APP_NAME: str = 'metadata_service'
    PORT: int = 5065
    HOST: str = '0.0.0.0'
    ENV: str = 'test'
    KAFKA_URL: str = 'kafka:29099'
    KAFKA_TOPIC: str = 'metadata.items'

    AUTH_HOST: str = 'http://fakeauth'

    OPSDB_UTILITY_USERNAME: str = 'postgres'
    OPSDB_UTILITY_PASSWORD: str = 'postgres'
    OPSDB_UTILITY_HOST: str = 'db'
    OPSDB_UTILITY_PORT: str = '5432'
    OPSDB_UTILITY_NAME: str = 'metadata'

    METADATA_SCHEMA = str = 'metadata'

    MAX_TAGS = 10
    MAX_SYSTEM_TAGS = 10
    MAX_ATTRIBUTE_LENGTH = 100
    MAX_COLLECTIONS = 10

    LOG_LEVEL_DEFAULT = logging.WARN
    LOG_LEVEL_FILE = logging.WARN
    LOG_LEVEL_STDOUT = logging.WARN
    LOG_LEVEL_STDERR = logging.ERROR

    GREENROOM_ZONE_VALUE: int = 0
    CORE_ZONE_VALUE: int = 1
    RSA_PUBLIC_KEY = ''

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = Extra.allow

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return env_settings, load_vault_settings, init_settings, file_secret_settings

    def __init__(self):
        super().__init__()
        self.AUTH_SERVICE = self.AUTH_HOST + '/v1/'
        self.RSA_PUBLIC_KEY = bytes.decode(base64.b64decode(self.RSA_PUBLIC_KEY), 'utf-8').replace(r'\n', '\n')
        self.SQLALCHEMY_DATABASE_URI = (
            f'postgresql://{self.OPSDB_UTILITY_USERNAME}:'
            f'{self.OPSDB_UTILITY_PASSWORD}@{self.OPSDB_UTILITY_HOST}'
            f':{self.OPSDB_UTILITY_PORT}/{self.OPSDB_UTILITY_NAME}'
        )


@lru_cache(1)
def get_settings():
    settings = Settings()
    return settings


ConfigClass = get_settings()
