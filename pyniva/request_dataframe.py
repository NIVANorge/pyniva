#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to read time series tsb backend
"""
from datetime import datetime, timedelta
import numpy as np
import time
from .thing import Vessel
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


def get_available_parameters(platform_code, header, meta_host=PUB_META, exclude_tests=True):
    measurements, tseries_paths = get_paths_measurements(
        platform_code, header, meta_host
    )
    if exclude_tests:
        available_paths = [p for p in tseries_paths if "TEST" not in p]
    else:
        available_paths = tseries_paths

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
    empty_paths = []
    for path in param_paths:
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
                print(f"No data for path {path}")
                empty_paths.append(path)

            elif df.empty:
                df = var
            else:
                df = df.merge(var, on="time", how="outer")

        except Exception as e:
            print(f"could not download {path, e}")

    if df.empty:
        print("Nothing was downloaded")
    else:

        if not noqc:

            df = df.dropna(subset=["latitude", "longitude"], how="all")
            print(f" downloaded data for {param_paths}")
            # also do not get coordinates if all data columns are empty
            data_cols = [
                p
                for p in param_paths
                if p not in ["time", "latitude", "longitude", f"{vessel_name}/gpstrack"]
                and "TEST" not in p
                and p in df.columns
            ]

            # print(f"drop nans")
            # df = df.dropna(subset=data_cols, how="all")
            # keep columns with nans
        df = df.sort_values(by="time", ascending=True)
        df = df.reset_index()
        # add columns from empty paths and fill with nans
        for path in empty_paths:
            df[path] = None
    return df


def get_data_discrete_dates(
    vessel_name: str,
    param_paths: list,
    noqc,
    header,
    dt=0,
    pub_tsb=PUB_TSB,
    meta_host=PUB_META,
):
    print("Downloading data for ", vessel_name)
    print ("Test")
    raise NotImplementedError("This function is not implemented yet")



def get_ramses_time_slice(              
            vessel_name: str, 
            param_paths: list,
            spectral_paths: list, 
            vessel_paths: list,
            vessel_signals: list,
            start_time,
            end_time,
            noqc,
            header,
            dt=0,
            pub_tsb=PUB_TSB):
    
    # get spectral data
    # first get spectral data
    print(f"Downloading spectral data {spectral_paths[0]} times {start_time} to {end_time}")
    df = pd.DataFrame()
    tseries_idx = vessel_paths.index(spectral_paths[0])
    df = vessel_signals[tseries_idx].get_tseries(
                    pub_tsb,
                    header=header,
                    noqc=noqc,
                    dt=dt,
                    start_time=start_time,
                    end_time=end_time)
    if df.empty:
        print(f"No ramses data found for path {spectral_paths[0]}")
        return df
    df = df.sort_values(by="time", ascending=True)
    df = df.reset_index()
    df = df.pivot(index = "time", columns="wl", values="value") 

    # then get gps data
    print(f"Downloading gps track")
    path = f"{vessel_name}/gpstrack"
    gps_index = vessel_paths.index(path)
    gps_data = vessel_signals[gps_index].get_tseries(
                    pub_tsb,
                    header=header,
                    noqc=noqc,
                    dt=dt,
                    start_time=start_time,
                    end_time=end_time,
    )

    # inperpolate gps data to match ramses
    print(f"Interpolating gps track to ramses frequency")
    gps_data = gps_data.sort_values(by="time", ascending=True)
    gps_data = gps_data.reset_index()
    datetime_ramses = list(set([time.mktime(datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").timetuple()) for v in list(df.index)]))
    gps_datetime = [time.mktime(datetime.strptime(str(v), "%Y-%m-%d %H:%M:%S").timetuple()) for v in list(gps_data["time"])]
    longitude = list(gps_data["longitude"])
    latitude = list(gps_data["latitude"])
    longitude_interp = np.interp(datetime_ramses, gps_datetime, longitude)
    latitude_interp = np.interp(datetime_ramses, gps_datetime, latitude)
    df["longitude"] = longitude_interp
    df["latitude"] = latitude_interp

    # add other ramses data
    for path in param_paths:
        if path in spectral_paths:
                continue
        if "RAMSES" not in path:
            print(f"ship data needs to be downloaded separately. Skipping {path}")
            continue            
        print(f"Add {path} to spectral profile")    
        tseries_idx = vessel_paths.index(path)
        var = vessel_signals[tseries_idx].get_tseries(
                    pub_tsb,
                    header=header,
                    noqc=noqc,
                    dt=dt,
                    start_time=start_time,
                    end_time=end_time,
            )
        df = df.merge(var, on="time", how="outer")        
    return df


def get_ramses_data(
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
    spectral_paths = [path for path in param_paths if vessel_signals[vessel_paths.index(path)].TTYPE=="spectra"]
    assert len(spectral_paths)==1, "Only one spectral profile can be downloaded at a time"

    start_datetime=datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
    end_datetime=datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")

    #slide in 12 h slices
    period = timedelta(hours=12)
    periods = 1
    if (end_datetime-start_datetime)>period:
        periods = int((end_datetime-start_datetime)/period)


    start_times = [t.strftime('%Y-%m-%dT%H:%M:%S') for t in [start_datetime+i*period for i in range(0,periods)]]
    end_times = [t.strftime('%Y-%m-%dT%H:%M:%S') for t in [start_datetime+i*period for i in range(1,periods)]]
    end_times.append(end_time)

   
    df = pd.DataFrame()
    for start_time, end_time in zip(start_times, end_times):
        print(f"Downloading data for {start_time} to {end_time}")
        df_slice =get_ramses_time_slice(              
            vessel_name, 
            param_paths,
            spectral_paths, 
            vessel_paths,
            vessel_signals,
            start_time,
            end_time,
            noqc,
            header,
            dt=0,
            pub_tsb=PUB_TSB)
        if df.empty:
            df = df_slice
        else:
            df = pd.concat([df, df_slice])
    
    return df