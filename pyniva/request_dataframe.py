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
from .thing import Vessel
from .metaflow import META_HOST

# from .pyniva import Vessel, TimeSeries, token2header
# from pyniva import META_HOST, PUB_META, TSB_HOST, PUB_TSB


def get_available_parameters(platform_code, header):
    measurements, tseries_paths = get_paths_measurements(platform_code, header)
    available_paths = [
        p for p in tseries_paths if "TEST" not in p and "SYSTEM" not in p
    ]
    return available_paths


def get_available_flags(platform_code):
    measurements, tseries_paths = get_paths_measurements(platform_code)
    available_paths = [p for p in tseries_paths if "TEST" in p]
    return available_paths


def get_available_ferrybox_sensor_group_parameters(platform_code):
    measurements, tseries_paths = get_paths_measurements(platform_code)
    available_paths = [
        p for p in tseries_paths if "TEST" not in p and "FERRYBOX" in p.upper()
    ]
    return available_paths


import pandas as pd


def get_paths_measurements(vessel_name, header):
    # Here we can directly get one object for the vessel we need without getting all of them as above
    vessel_object = Vessel.get_thing(META_HOST, header, params={"path": vessel_name})
    vessel_measurements = vessel_object.get_all_tseries(META_HOST, header)
    tseries_paths = [m.path for m in vessel_measurements]
    return vessel_measurements, tseries_paths


def get_ship_data(vessel_name, param_paths, start_time, end_time, noqc, header, dt=0):
    print("Downloading data for ", vessel_name)
    measurements, tseries_paths = get_paths_measurements(vessel_name)
    df = pd.DataFrame()
    # make sure that all datasets have coordinates
    if f"{vessel_name}/gpstrack" not in param_paths:
        param_paths.append(f"{vessel_name}/gpstrack")
    for path in param_paths:
        print(path)
        try:
            tseries_idx = tseries_paths.index(path)
            var = measurements[tseries_idx].get_tseries(
                PUB_TSB,
                header=header,
                noqc=noqc,
                dt=dt,
                start_time=start_time,
                end_time=end_time,
            )

            if not var.empty:
                var = var.reset_index()
                varname = var.columns[1]
                if not "gpstrack" in path:
                    var.rename(columns={varname: path}, inplace=True)
            else:
                print("no data available")

            if df.empty and not var.empty:
                df = var
            elif not df.empty and not var.empty:
                df = pd.merge(df, var, on="time", how="outer")

        except Exception as e:
            print(f"could not download {path, e}")
            # print (df.head())
    if not df.empty:
        df = df.reset_index()
        df = df.sort_values(by="time", ascending=True)
    else:
        print("Nothing was downloaded")
    return df
