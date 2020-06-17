import datetime as dt
import json

import pytest

import pyniva

TSB_URL = 'https://api-test.niva.no/v1/tsb/'
META_URL = 'https://api-test.niva.no/v1/metaflow/'


@pytest.mark.token_and_ms_ferrybox
def test_ms_ferrybox_for_newly_populated_data():
    """ Testing that the ms ferrybox api responds correctly to requests for newly inserted data"""
    header = pyniva.token2header("/home/roald/PycharmProjects/other_nivacloud_stuff/"
                                 "secrets/nivatestdev-1b5ad93f6938.json")

    # Only Norbjorn data was inserted in this time span
    start = dt.datetime(2020, 6, 16, 9, 0, 0)
    end = dt.datetime(2020, 6, 16, 10, 0, 0)
    new_data = pyniva.get_newly_inserted_data(start, end, aggregate=True,
                                              headers=header, meta_host=META_URL, ts_host=TSB_URL)

    assert all('NB' in item['path'] for item in new_data)
    assert len(new_data) == 21  # 21 paths have data
    assert all(list(key in new_data[0] for key in ["count", "max", "min", "uuid", "path"]))


if __name__ == '__main__':
    pytest.main(['-m', 'token_and_ms_ferrybox'])
