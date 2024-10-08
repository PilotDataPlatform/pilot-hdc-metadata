# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import random

from app.app_utils import decode_path_from_ltree
from app.app_utils import encode_path_for_ltree


class TestUtils:
    def generate_random_label(self) -> str:
        random_label = ''
        label_length = random.randint(4, 20)
        for _ in range(label_length):
            random_label += chr(random.randint(32, 126))
        return random_label

    def generate_random_path(self) -> str:
        random_path = ''
        labels = random.randint(1, 8)
        for _ in range(labels):
            random_path += f'{self.generate_random_label()}.'
        return random_path[:-1]

    def test_01_encode_decode_paths(self):
        random_paths = []
        paths_to_test = 100
        for _ in range(paths_to_test):
            random_paths.append(self.generate_random_path())
        for path in random_paths:
            encoded = encode_path_for_ltree(path)
            decoded = decode_path_from_ltree(encoded)
            assert decoded == path
