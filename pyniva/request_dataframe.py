#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to read time series tsb backend
"""
import sys
import logging
from datetime import datetime, timedelta
import re
from dateutil.parser import parse
from .thing import Vessel, TimeSeries
from .metaflow import PUB_META
from .tsb import PUB_TSB
import pandas as pd


def get_paths_measurements(vessel_name, header, meta_host=PUB_META):
    # Here we can directly get one object for the vessel we need without getting all of them as

    vessel_object = Vessel.get_thing(
        meta_host=meta_host, header=header, params={"path": vessel_name}
    )

    vessel_signals = vessel_object.get_all_tseries(meta_host, header)
    tseries_paths = [m.path for m in vessel_signals]
    return vessel_signals, tseries_paths


def get_available_parameters(platform_code, header, meta_host=None, exclude_tests=True):
    measurements, tseries_paths = get_paths_measurements(
        platform_code, header, meta_host
    )
    if exclude_tests:
        available_paths = [p for p in tseries_paths if "TEST" not in p]
    return available_paths


def get_ship_data(
    vessel_name: str,
    param_paths: list,
    start_time,
    end_time,
    noqc,
    header,
    dt=0,
    pub_tsb=PUB_TSB,
    meta_host=PUB_META,
):
    print("Downloading data for ", vessel_name)

    vessel_signals, vessel_paths = get_paths_measurements(
        vessel_name, meta_host=meta_host, header=header
    )

    df = pd.DataFrame()
    # make sure that all datasets have coordinates
    if f"{vessel_name}/gpstrack" not in param_paths:
        param_paths.append(f"{vessel_name}/gpstrack")
    for path in param_paths:
        print(path)
        try:
            tseries_idx = vessel_paths.index(path)

            var = vessel_signals[tseries_idx].get_tseries(
                pub_tsb,
                header=header,
                noqc=noqc,
                dt=dt,
                start_time=start_time,
                end_time=end_time,
            )

            if var.empty:
                print(f"Not data for path {path}")
            elif df.empty:
                df = var
            else:
                df = df.merge(var, on="time", how="outer")
        except Exception as e:
            print(f"could not download {path, e}")

    if df.empty:
        print("Nothing was downloaded")
    else:
        df = df.sort_values(by="time", ascending=True)
        df = df.reset_index()

    return df


def get_ship_data2(
    vessel_name: str,
    param_paths: list,
    start_time,
    end_time,
    noqc,
    header,
    dt=0,
    pub_tsb=PUB_TSB,
    meta_host=PUB_META,
):
    print("Downloading data for ", vessel_name)

    vessel_object = Vessel.get_thing(
        meta_host=meta_host, header=header, params={"path": vessel_name}
    )
    vessel_signals = vessel_object.get_all_tseries(meta_host, header)
    vessel_signals = [
        s
        for s in vessel_signals
        if s.path in param_paths or s.path == f"{vessel_name}/gpstrack"
    ]

    # make sure that all datasets have coordinates

    var = TimeSeries.get_timeseries_list(
        ts_host=pub_tsb,
        timeseries=vessel_signals,
        header=header,
        noqc=noqc,
        dt=dt,
        start_time=start_time,
        end_time=end_time,
        name_headers=True,
    )

    return var
