#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Object oriented interface to NIVA Thing universe
"""
__all__ = ["Thing", "Platform", "Vessel", "Sensor", "TimeSeries",
           "FlagTimeSeries", "GPSTrack"]

from dateutil.parser import parse


from .metaflow import get_thing as meta_get_thing
from .metaflow import update_thing as meta_update_thing
from .metaflow import delete_thing as meta_delete_thing
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


    def __init__(self, meta_dict=None, **kwargs):
        if meta_dict is None:
            meta_dict = {}
        for k, v in kwargs.items():
            meta_dict[k] = v
        if "path" in meta_dict and "name" not in meta_dict:
            assert(isinstance(meta_dict["path"], str))
            meta_dict["name"] = meta_dict["path"].split("/")[-1]

        if "ttype" not in meta_dict:
            meta_dict["ttype"] = self.TTYPE
        self._meta_dict = meta_dict


    def __getattr__(self, attr):
        try:
            return self._meta_dict[attr]
        except:
            raise AttributeError("Attribute '%s' not found" % (attr,))


    def __setattr__(self, attr, value):
        if attr != "_meta_dict":
            self.__dict__["_meta_dict"][attr] = value
        else:
            self.__dict__[attr] = value



    def __dir__(self):
        return(super().__dir__() + [k for k in self._meta_dict.keys() if not k.startswith("_")])


    @classmethod
    def _thing_dispatch(cls, thing_data):
        if isinstance(thing_data, list):
            if len(thing_data) == 0:
                return thing_data
            elif len(thing_data) == 1:
                assert(isinstance(thing_data, dict) and "ttype" in thing_data[0] and thing_data[0]["ttype"] in _valid_types)
                thing_meta = _dispatcher[thing_data[0]["ttype"]](thing_meta[0])
            elif isinstance(thing_data, list) and len(thing_data) > 1:
                thing_meta = [cls._thing_dispatch(t) for t in thing_data]
        elif isinstance(thing_data, dict) and "ttype" in thing_data:
            assert(thing_data["ttype"] in _valid_types)
            for k,v in thing_data.items():
                if isinstance(v, dict) and "ttype" in v:
                    thing_data[k] = cls._thing_dispatch(v)
                elif isinstance(v, list):
                    c_list = []
                    for e in v:
                        if isinstance(e, dict) and "ttype" in e:
                            c_list.append(cls._thing_dispatch(e))
                        else:
                            c_list.append(e)
                    thing_data[k] = c_list

            thing_meta = _dispatcher[thing_data["ttype"]](thing_data)
        else:
            raise ThingError("Unknown data type passed, must be a dictionary or a list of dictionarise")
        return thing_meta


    @classmethod
    def get_thing(cls, meta_host, params={}, header=None, **kwargs):
        for k, v in kwargs.items():
            params[k] = v
        thing_meta = meta_get_thing(meta_host, params, header=header)
        return(cls._thing_dispatch(thing_meta))


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


    # @property
    # def parts(self):
    #     if "parts" in self._meta_dict:
    #         return self._meta_dict["parts"]
    #     else:
    #         return []


    def as_dict(self, shallow=False):
        """Return data of instance as a dictionary.
        The data will be JSON serializable

        Args:
            shallow: if True uuids will be used instead of objects
        """
        def _dict_iter(c_dict):
            out_dict = c_dict.copy()
            for k in out_dict.keys():
                if isinstance(c_dict[k], Thing):
                    if not shallow:
                        out_dict[k] = out_dict[k].as_dict(shallow)
                    else:
                        out_dict[k] = out_dict[k].uuid
                elif isinstance(out_dict[k], list):
                    c_list = []
                    for e in out_dict[k]:
                        if isinstance(e, Thing):
                            if not shallow:
                                c_list.append(e.as_dict())
                            else:
                                c_list.append(e.uuid)
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


    def save(self, meta_host, header=None):
        """Save/update thing in meta-data service

        The method will also recursively update/save
        objects found in self.parts list to ensure
        metaflow is kept in a consistent state.
        """
        # Keep track of parts to ensure metaflow stays
        # consistent after update/save
        c_parts = self._meta_dict.get("parts", None)
        if c_parts is not None:
            del(self._meta_dict["parts"])

        updated_data = meta_update_thing(meta_host, self.as_dict(shallow=True),
                                         header=header)
        updated_thing = self._thing_dispatch(updated_data)

        if c_parts is not None:
            # Handle possible inconsistencies in parts
            assert(isinstance(c_parts, list))
            for p in c_parts:
                p.part_of = updated_thing.uuid
                p = p.save(meta_host)
            updated_thing.parts = c_parts

        return updated_thing


    def delete(self, meta_host, header=None, recursive=False):
        """Delete the object in meta-data service

        The server side API will make sure the part_of structure
        will remain/stay consistent after the delete
        """
        c_parts = self._meta_dict.get("parts", None)
        if recursive and c_parts is not None:
            for p in c_parts:
                p.delete(meta_host, header=header, recursive=recursive)
        if c_parts is not None:
            del(self._meta_dict["parts"])

        deleted_data = meta_delete_thing(meta_host, self.as_dict(shallow=True))
        deleted_thing = self._thing_dispatch(deleted_data)
        return deleted_thing


    def get_tree(self, meta_host, header=None, levels=100):
        return self.get_thing(meta_host, header=header, uuid=self.uuid, parts=levels)


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

        full_thing = self.get_tree(meta_host, header=header)
        thing_tree = full_thing.as_dict()

        ts_list = [Thing.tdict2thing(ts) for ts in thing_tree2ts(thing_tree)]
        ts_dict = {ts.uuid:ts for ts in ts_list}
        out_ts_list = [_part_uuid2thing(ts, ts_dict) for ts in ts_list]
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
        return self.get_timeseries_list(ts_host, [self,], name_headers=True,
                                        **kwargs)

    def get_ts(self, ts_host, **kwargs):
        return self.get_tseries(ts_host, **kwargs)


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
    "component": Component,
    "platform": Platform,
    "vessel": Vessel,
    "sensor": Sensor,
    "tseries": TimeSeries,
    "qctseries": FlagTimeSeries,
    "gpstrack": GPSTrack
}

_valid_types = [k for k in _dispatcher]