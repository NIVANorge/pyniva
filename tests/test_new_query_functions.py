import pytest
import pyniva
from pyniva.request_dataframe import get_ship_data, get_available_parameters
from pyniva.metaflow import META_HOST


def get_ship_data():
    t = get_ship_data(vessel_name="FA")
    print(t)


def test_get_available_parameters():
    header = None
    a = get_available_parameters("FA", header=header)
