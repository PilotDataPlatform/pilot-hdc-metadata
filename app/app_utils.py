# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import base64
import math
import re

from sqlalchemy_utils import Ltree


def encode_label_for_ltree(raw_string: str) -> str:
    base32_string = str(base64.b32encode(raw_string.encode('utf-8')), 'utf-8')
    return re.sub('=', '', base32_string)


def encode_path_for_ltree(raw_path: str) -> str:
    labels = raw_path.split('/')
    path = ''
    for label in labels:
        path += f'{encode_label_for_ltree(label)}.'
    return path[:-1]


def decode_label_from_ltree(encoded_string: str) -> str:
    missing_padding = math.ceil(len(encoded_string) / 8) * 8 - len(encoded_string)
    if missing_padding:
        encoded_string += '=' * missing_padding
    utf8_string = base64.b32decode(encoded_string.encode('utf-8')).decode('utf-8')
    return utf8_string


def decode_path_from_ltree(encoded_path: str) -> str:
    if type(encoded_path) == Ltree:
        encoded_path = str(encoded_path)
    labels = encoded_path.split('.')
    path = ''
    for label in labels:
        path += f'{decode_label_from_ltree(label)}/'
    return path[:-1]


def get_zone_label(zone: int) -> str:
    zone_labels = {0: 'Greenroom', 1: 'Core'}
    return zone_labels[zone]


def construct_display_path(container_code: str, zone: str, encoded_path: str) -> str:
    decoded_path = decode_path_from_ltree(encoded_path)
    display_path = f'{container_code}/{get_zone_label(zone)}/{decoded_path}'
    return display_path
