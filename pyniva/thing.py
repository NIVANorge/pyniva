#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Object oriented interface to NIVA Thing universe
"""
__all__ = ["Thing", "Platform", "Vessel", "Sensor", "TimeSeries",
           "FlagTimeSeries", "GPSTrack"]

from datetime import datetime, timedelta
from dateutil.parser import parse

import json
from collections import OrderedDict

from .metaflow import get_thing as meta_get_thing
from .metaflow import update_thing as meta_update_thing
from .metaflow import thing_tree2ts
from .tsb import get_signals


class ThingError(Exception):
    """Exception wrapper for Thing universe
    """
    pass


class Thing():
    """Base class for the Thing universe
    """
    TTYPE = "thing"


    def __init__(self, meta_dict):
        if "ttype" not in meta_dict:
            meta_dict["ttype"] = self.TTYPE
        self._meta_dict = meta_dict


    def __getattr__(self, name):
        try:
            return self._meta_dict[name]
        except:
            raise AttributeError("Attribute %s not found" % (name,))


    def __dir__(self):
        return(super().__dir__() + [k for k in self._meta_dict.keys() if not k.startswith("_")])



    @staticmethod
    def get_thing(meta_host, params, header=None):
        thing_meta = meta_get_thing(meta_host, params, header=header)
        if isinstance(thing_meta, list) and len(thing_meta) == 1:
            thing_meta = _dispatcher[thing_meta[0]["ttype"]](thing_meta[0])
        elif isinstance(thing_meta, list) and len(thing_meta) > 1:
            thing_meta = [_dispatcher[t["ttype"]](t) for t in thing_meta if isinstance(t, dict)]
        elif isinstance(thing_meta, dict) and "ttype" in thing_meta:
            thing_meta = _dispatcher[thing_meta["ttype"]](thing_meta)
        return thing_meta


    @classmethod
    def list(cls, meta_host, header=None, **kwargs):
        params = {"ttype": cls.TTYPE}
        for k, v in kwargs.items():
            params[k] = v
        t_list = cls.get_thing(meta_host, params=params, header=header)
        return t_list if isinstance(t_list, list) else [t_list,]


    @classmethod
    def tdict2thing(cls, tdict, parts=False):
        if parts and "parts" in tdict:
            tdict["parts"] = [cls.tdict2thing(part) for part in tdict["parts"]]
        return _dispatcher[tdict["ttype"]](tdict)


    def as_dict(self):
        """Return data of instance as a dictionary.
        The data will be JSON serializable
        """
        def _dict_iter(c_dict):
            out_dict = c_dict.copy()
            for k in out_dict.keys():
                if isinstance(c_dict[k], Thing):
                    out_dict[k] = out_dict[k].as_dict()
                elif isinstance(out_dict[k], list):
                    c_list = []
                    for e in out_dict[k]:
                        if isinstance(e, Thing):
                            c_list.append(e.as_dict())
                        elif isinstance(e, dict):
                            c_list.append(_dict_iter(e))
                        else:
                            c_list.append(e)
                    out_dict[k] = c_list
                elif isinstance(out_dict[k], dict):
                    out_dict[k] = _dict_iter(out_dict[k])
                else:
                    pass
            return out_dict
        return(_dict_iter(self._meta_dict))



class Component(Thing):
    """Component or part of a thing
    """
    TTYPE = "component"
    pass


class Platform(Thing):
    """Base class for sensor/measurement platforms
    """
    TTYPE = "platform"

    def get_all_tseries(self, meta_host, header=None):
        def _part_uuid2thing(thing, tlookup):
            if isinstance(thing, dict):
                return tlookup[thing["uuid"]]
            if hasattr(thing, "parts"):
                thing._meta_dict["parts"] = [_part_uuid2thing(part, tlookup) for part in thing.parts]
            return tlookup[thing.uuid]

        thing_tree = self.get_thing(meta_host, {"uuid":self.uuid,
                                                "parts": 100},
                                    header=header)

        ts_list = [Thing.tdict2thing(ts) for ts in thing_tree2ts(thing_tree._meta_dict)]
        ts_dict = {ts.uuid:ts for ts in ts_list}
        out_ts_list = [_part_uuid2thing(ts, ts_dict) for ts in ts_list]
        self._meta_dict["parts"] = [ts for ts in out_ts_list if ts.part_of == self.uuid]
        return out_ts_list



class Vessel(Platform):
    """Ship/Vessels
    """
    TTYPE = "vessel"



class Sensor(Component):
    """Measurement system or sensor system
    """
    TTYPE = "sensor"


class TimeSeries(Thing):
    TTYPE = "tseries"
    

    @classmethod
    def get_timeseries_list(cls, ts_host, timeseries,
                            name_headers=False, **kwargs):
        """Metod for querying a time series from the tsb backend

        Params:
           ts_host (str): URL for time series backend (tsb)
           timeseries:    a single TimeSeries instance or a list of TimeSeries instances
           **kwargs:      Keyword arguments for the query, see tsb documentation for
                          further details.
        Returns:
            A Pandas DataFrame with the timeseries
        """
        if isinstance(timeseries, TimeSeries):
            uuid_list = [timeseries.uuid,]
        else:
            uuid_list = [ts.uuid for ts in timeseries]
        # print(uuid_list)
        df = get_signals(ts_host, uuid_list, **kwargs)
        if name_headers:
            uuid2meta = {ts.uuid:{"name":ts.name, "path":ts.path} 
                         for ts in timeseries if hasattr(ts, "name")}
            df.columns = map(lambda x: x if not uuid2meta.get(x, False) else uuid2meta[x]["name"],
                             df.columns)
        return df


    def get_tseries(self, ts_host, **kwargs):
        return self.get_timeseries_list(ts_host, name_headers=True,
                                        **kwargs)

    @property
    def start_time(self):
        if self._meta_dict.get("start_time", False):
            if isinstance(self._meta_dict["start_time"], str):
                self._meta_dict["start_time"] = parse(self._meta_dict["start_time"])
            return self._meta_dict["start_time"]
        else:
            return None

    @property
    def end_time(self):
        if self._meta_dict.get("end_time", False):
            if isinstance(self._meta_dict["end_time"], str):
                self._meta_dict["end_time"] = parse(self._meta_dict["end_time"])
            return self._meta_dict["end_time"]
        else:
            return None


# end of class TimeSeries


class FlagTimeSeries(TimeSeries):
    TTYPE = "qctseries"
    pass


class GPSTrack(TimeSeries):
    TTYPE = "gpstrack"
    pass


# Dictionary to call individual init functions
_dispatcher = {
    "thing": Thing,
    "platform": Platform,
    "vessel": Vessel,
    "sensor": Sensor,
    "tseries": TimeSeries,
    "qctseries": FlagTimeSeries,
    "gpstrack": GPSTrack
}