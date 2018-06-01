#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to connect to NIVA API to query FerryBox data
"""
__all__ = ["TSB_HOST", "PUB_TSB", "get_signals", "ts_list2df"]
import os
from datetime import datetime, timedelta
import json
from collections import OrderedDict
import pandas as pd
import requests as rq
import jwt

from .get_data import get_data, token2header


# "Public" endpoints for data
# PUB_SIGNAL = "https://ferrybox-api.niva.no/v1/signal/"
PUB_TSB = "https://ferrybox-api.niva.no/v1/tsb/"

# "Internal" endpoints for data
TSB_HOST_ADDR = os.environ.get("TSB_SERVICE_HOST", "localhost")
TSB_HOST_PORT = os.environ.get("TSB_SERVICE_PORT", 5554)
TSB_HOST = "http://" + TSB_HOST_ADDR + ":" + str(TSB_HOST_PORT) + "/ts/"




def ts_list2df(ts_dict_list):
    """Create pandas DataFrame from list of dictionaries

    Params:
        ts_dict_list (list like): List of dictionaries for time series
             like JSON returned by tsb endpoint, each of the dictionaries
             must contain a timestamp (key = time)
    Returns:
        Time indexed pandas dictionary with data in list
    """ 
    assert(len(ts_dict_list) > 0)
    keys_set = set([k for rd in ts_dict_list for k in rd.keys()])
    assert("time" in keys_set)
    data_dict = OrderedDict([("time", []),])

    if "longitude" in keys_set and "latitude" in keys_set:
        data_dict["longitude"] = []
        data_dict["latitude"] = []
    for k in list(keys_set):
        if k not in set(["time", "longitude", "latitude"]):
            data_dict[k] = []

    for ts_row in ts_dict_list:
        c_keys = set()
        for k, v in ts_row.items():
            data_dict[k].append(v)
            c_keys.add(k)
        for c_k in list(keys_set - c_keys):
            data_dict[c_k].append(None)

    df = pd.DataFrame(data_dict)
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)
    return df



# Helper to get data frames with time series data
def get_signals(signals_url, uuids, **kwargs):
 # start_time, end_time,
 #                time_window="PT1H", agg_type="avg", uuid_lookup=None,
 #                headers=None):
    """Get signals (time series data) from NIVA REST endpoints

    Params:
       signals_url (str):     The base url for the time series endpoint
       uuids (list):          List of UUIDs for the signals to query
       **kwargs:              Named parameters for tsb backend


       ### FIXME add examples and more information ###
       start_time (datetime): Start time of query
       end_time (datetime):   End time of query
       time_window (str):     ISO8601 representation of time window of aggregation
       agg_type (str):        Signal aggregation function, possible values:
                              "avg" (default), "min", "max", "sum", "count",
                              "stddev", "mode", "median"
       uuid_lookup (dict):    Lookup table with meta data for the passed uuids 
       headers (dict):        Header data for the request towards NIVA public endpoint,
                              must include JWT access token (internal endpoint requires no
                              header)

    Returns:
       A Pandas DataFrame with the data returned
       If no data is returned an empty DataFrame is returned.
    """
    

    header = kwargs.get("header")
    if "header" in kwargs:
        del kwargs["header"]

    query_url = signals_url
    params = {}
    if "start_time" in kwargs:
        params["start"] = kwargs["start_time"].isoformat()
        del kwargs["start_time"]
    if "end_time" in kwargs:
        params["end"] =  kwargs["end_time"].isoformat()
        del kwargs["end_time"]
    for k, v in kwargs.items():
        params[k] = v
    params["uuid"] = ",".join(uuids)

    data = get_data(query_url, params=params, headers=header)

    if len(data) == 0:
        df = pd.DataFrame()
    else:
        df = ts_list2df(data)

    return df