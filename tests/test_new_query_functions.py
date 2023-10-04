import pytest
import pyniva
from pyniva.request_dataframe import (
    get_ship_data,
    get_available_parameters,
    get_paths_measurements,
)
from pyniva import token2header

# from pyniva.metaflow import META_HOST


def test_get_ship_data():
    header = token2header("tests/niva-service-account.json")
    param_paths = ["FA/FERRYBOX/C3/CDOM_FLUORESCENCE/RAW"]
    start_time = "2023-02-01T11:00:00"
    end_time = "2023-03-26T16:00:59"
    t = get_ship_data(
        vessel_name="FA",
        param_paths=param_paths,
        start_time=start_time,
        end_time=end_time,
        noqc=False,
        header=header,
        dt="P1D",
        pub_tsb="https://ferrybox.t.niva.no/v1/tsb",
        meta_host="https://ferrybox.t.niva.no/v1/metaflow",
    )

    assert not t.empty


def test_get_available_parameters():
    header = token2header("tests/niva-service-account.json")
    a = get_available_parameters(
        "FA", header=header, meta_host="https://ferrybox.t.niva.no/v1/metaflow"
    )
    assert "FA/FERRYBOX/C3/CDOM_FLUORESCENCE/RAW" in a


def test_get_paths_measurements():
    header = token2header("tests/niva-service-account.json")
    vessel_measurements, tseries_paths = get_paths_measurements(
        vessel_name="FA",
        header=header,
        meta_host="https://ferrybox.t.niva.no/v1/metaflow",
    )

    assert "FA/FERRYBOX/C3/CDOM_FLUORESCENCE/RAW/FROZEN_TEST" in tseries_paths
