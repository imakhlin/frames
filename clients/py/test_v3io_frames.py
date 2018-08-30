# Copyright 2018 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from io import BytesIO

import msgpack
import pandas as pd
import pytest

import v3io_frames as v3f


class patch_requests:
    orig_requests = v3f.requests

    def __init__(self, data=None):
        self.requests = []
        self.data = [] if data is None else data

    def __enter__(self):
        v3f.requests = self
        return self

    def __exit__(self, exc_type=None, exc_val=None, tb=None):
        v3f.requests = self.orig_requests

    def post(self, *args, **kw):
        self.requests.append((args, kw))
        io = BytesIO()
        for chunk in self.data:
            msgpack.dump(chunk, io)

        io.seek(0, 0)

        class Response:
            raw = io
            ok = True

        return Response


def test_read():
    api_key = 'test api key'
    url = 'https://nuclio.io'
    query = 'SELECT 1'
    data = [
        {
            'columns': ['x', 'y'],
            'slice_cols': {
                'x': {
                    'name': 'x',
                    'ints': [1, 2, 3]
                },
                'y': {
                    'name': 'y',
                    'floats': [4., 5., 6.],
                },
            },
        },
        {
            'columns': ['x', 'y'],
            'slice_cols': {
                'x': {
                    'name': 'x',
                    'ints': [10, 20, 30],
                },
                'y': {
                    'name': 'y',
                    'floats': [40., 50., 60.],
                },
            }
        },
    ]

    c = v3f.Client(url, api_key)
    with patch_requests(data) as patch:
        dfs = c.read(query=query)

    assert len(patch.requests) == 1

    args, kw = patch.requests[0]
    assert args == (url + '/read',)

    df = pd.concat(dfs)
    assert len(df) == 6
    assert list(df.columns) == ['x', 'y']


@pytest.mark.skip(reason='TODO')
def test_write():
    pass
