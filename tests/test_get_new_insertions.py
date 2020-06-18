import json
import datetime as dt
from pathlib import Path
from urllib.parse import urljoin

import pytest
import requests

import pyniva

TEST_DATA_DIR = Path(__file__).parents[0] / 'test_data'
TSB_URL = 'http://localhost:8504'
META_URL = 'http://localhost:8506'


@pytest.fixture
def populate_database():
    with (TEST_DATA_DIR / 'synthetic_ferrybox_data.json').open('r') as json_data:
        test_data = json.load(json_data)
    unique_paths = list({r[1] for r in test_data["time_series"]}.union(
        {r[1] for r in test_data["locations"]}).union(
        {r[1] for r in test_data["flags"]}))

    response = requests.post(urljoin(META_URL, 'get_thing_from_path'), json={'paths': unique_paths})
    response.raise_for_status()
    response_data = response.json()

    path_uuid_map = {k: response_data[k]['uuid'] for k in unique_paths}

    test_data = {k: [[path_uuid_map[e] if i == 1 else e for i, e in enumerate(r)]for r in v]
                 for k, v in test_data.items()}
    update_response = requests.put(urljoin(TSB_URL, '/upsert/'), json=test_data)
    update_response.raise_for_status()


@pytest.mark.nivacloud_docker
def test_tsb_for_newly_populated_data(populate_database):
    """ Testing that the tsb api responds correctly to requests for newly inserted data"""
    start = dt.datetime.utcnow()-dt.timedelta(hours=1)
    end = dt.datetime.utcnow()+dt.timedelta(hours=1)
    new_data = pyniva.get_newly_inserted_data(start, end, aggregate=True, meta_host=META_URL, ts_host=TSB_URL)
    assert len(new_data) == 26  # 26 paths have new data
    assert all(list(key in new_data[0] for key in ["count", "max", "min", "uuid", "path"]))

    new_data = pyniva.get_newly_inserted_data(start, end, aggregate=False, meta_host=META_URL, ts_host=TSB_URL)
    assert len(new_data) == 1326  # 1326 new pieces of data in total
    assert all(key in new_data[0] for key in ["created_timestamp", "time", "uuid", "path"])
