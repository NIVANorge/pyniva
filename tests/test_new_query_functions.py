import pytest
import pyniva
from pyniva.request_dataframe import (
    get_ship_data,
    get_data_discrete_dates,
    get_available_parameters,
    get_paths_measurements,
    get_ramses_data
)
from pyniva import token2header
import logging

# from pyniva.metaflow import META_HOST


@pytest.mark.system
def test_get_ship_data():
    header = token2header("tests/niva-service-account.json")
    param_paths = [
        "FA/INLET/SBE38/TEMPERATURE/RAW",
        "FA/INLET/SBE38/TEMPERATURE/RAW/LOCAL_RANGE_TEST",
        "FA/INLET/SBE38/TEMPERATURE/RAW/GLOBAL_RANGE_TEST",
    ]
    start_time = "2022-06-06T12:44:20"
    end_time = "2022-06-06T17:53:38"
    t = get_ship_data(
        vessel_name="FA",
        param_paths=param_paths,
        start_time=start_time,
        end_time=end_time,
        noqc=False,
        header=header,
        dt=0,
        pub_tsb="https://ferrybox.p.niva.no/v1/tsb",
        meta_host="https://ferrybox.p.niva.no/v1/metaflow",
    )

    assert not t.empty


@pytest.mark.system
def test_get_available_parameters():
    header = token2header("tests/niva-service-account.json")
    a = get_available_parameters(
        "FA", header=header, meta_host="https://ferrybox.t.niva.no/v1/metaflow"
    )
    assert "FA/FERRYBOX/C3/CDOM_FLUORESCENCE/RAW" in a


@pytest.mark.system
def test_get_paths_measurements():
    header = token2header("tests/niva-service-account.json")
    vessel_measurements, tseries_paths = get_paths_measurements(
        vessel_name="FA",
        header=header,
        meta_host="https://ferrybox.t.niva.no/v1/metaflow",
    )

    assert "FA/FERRYBOX/C3/CDOM_FLUORESCENCE/RAW/FROZEN_TEST" in tseries_paths


@pytest.mark.system
def test_get_ramses_data():
    header = token2header("tests/niva-service-account.json")
    param_paths = [
        "FA/RAMSES/DERIVED/RRS/CALIBRATED",
        "FA/RAMSES/DERIVED/PAR/CALIBRATED",
    ]
    start_time = "2023-07-14T00:00:00"
    end_time = "2023-07-14T00:05:00"
    t = get_ramses_data(
        vessel_name="FA",
        param_paths=param_paths,
        start_time=start_time,
        end_time=end_time,
        noqc=False,
        header=header,
        dt=0,
        pub_tsb="https://ferrybox.p.niva.no/v1/tsb",
        meta_host="https://ferrybox.p.niva.no/v1/metaflow",
    )

    assert not t.empty