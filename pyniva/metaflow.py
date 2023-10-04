# -*- coding: utf-8 -*-
"""
Set of helper functions used to get, query, traverse and manipulate
Meta data in the metaflow service
"""

__all__ = [
    "META_HOST",
    "PUB_PLATFORM",
    "PUB_DETAIL",
    "PUB_META",
    "get_thing",
    "update_thing",
    "delete_thing",
    "thing_tree2ts",
    "path2all_ts",
]

import uuid

import requests
import json
import os
import logging

from .__version__ import __version__
from .get_data import PyNIVAError

# "Internal" endpoint for meta dat
META_HOST_ADDR = os.environ.get("METAFLOW_SERVICE_HOST", "localhost")
# META_HOST_PORT = os.environ.get("METAFLOW_SERVICE_PORT", 5557)
META_HOST_PORT = os.environ.get("METAFLOW_SERVICE_PORT", 5556)
META_HOST = "http://" + META_HOST_ADDR + ":" + str(META_HOST_PORT) + "/"

# "Public" endpoints for meta-data
path = "https://ferrybox-api.niva.no"

PUB_PLATFORM = f"{path}/v1/vessels"
PUB_DETAIL = f"{path}/v1/details/"
PUB_META = f"{path}/v1/metaflow/"


def get_thing(meta_host, par, header=None, session=None):
    """Helper function to get thing meta data dictionary from metaflow server

    Args:
        meta_host: URL to meta server (i.e. metaflow service)
        par:       Dictionary with query parameters
        header:    HTTP request header (for JWT authentication and encryption)
        session:   Requests session object

    Returns:
        A list of Thing dictionaries or a single dictionary if only one
        is returned from the meta service
    """
    rq = session or requests

    trace_id = str(uuid.uuid4())
    header["Trace-Id"] = trace_id
    header["User-Agent"] = f"pyniva/{__version__}"

    if meta_host.startswith(PUB_DETAIL) and "uuid" in par:
        meta_host = meta_host + par["uuid"]
        del par["uuid"]

    r = rq.get(meta_host, params=par, headers=header)
    r.raise_for_status()
    t = r.json()

    if "t" not in t:
        raise PyNIVAError(
            message=f"Could not find metadata for requested parameters {par}",
            req_args=par,
            trace_id=trace_id,
        )
    if isinstance(t["t"], list) and len(t["t"]) == 1:
        return t["t"][0]

    return t["t"]


def path2all_ts(meta_host, path, search_depth=100, session=None):
    """Helper function to get all time series from a thing

    Args:
        meta_host:    URL to meta server (i.e. metaflow service)
        par:          Path to parent thing
        search_depth: How many levels of "parts" to search to get the list
        session:      Requests session object

    Returns:
        A list of time series meta dictionaries
    """
    thing = get_thing(meta_host, {"path": path}, session=session)
    assert isinstance(thing, dict) and "uuid" in thing
    thing = get_thing(
        meta_host, {"uuid": thing["uuid"], "parts": search_depth}, session=session
    )
    return [
        get_thing(meta_host, {"uuid": ts["uuid"]}, session=session)
        for ts in thing_tree2ts(thing)
    ]


def update_thing(meta_host, thing, header=None, session=None):
    """Helper function to create or update thing on meta server.

    Args:
        meta_host: URL to meta server (i.e. metaflow service)
        thing:     Dictionary with query parameters
        session:   Requests session object

    Returns:
        The created or updated thing meta dictionary
    """
    rq = session or requests

    data = json.dumps(thing)
    update_r = rq.put(meta_host, data=data, headers=header)
    update_r.raise_for_status()
    u_thing = update_r.json()

    if not "t" in u_thing:
        logging.error("Was not able to update thing %s" % (thing,))
        if "code" in u_thing:
            _msg = "PUT method not avaliable through endpoint"
            logging.error(_msg)
            u_thing["PyNIVAError"] = _msg

        raise PyNIVAError(u_thing)
    return u_thing["t"]


def delete_thing(meta_host, thing, header=None, session=None):
    """Function to delete a thing document (and alter affected documents)
    on the meta server.

    Args:
        meta_host: URL to meta server (i.e. metaflow service)
        thing:     Dictionary with the Thing document to delete
        session:   Requests session object

    Returns:
        The deleted document, and if present a list of all affected documents
        (possibly only a list of UUIDs for affected documents?)
    """
    rq = session or requests

    data = json.dumps(thing)
    del_r = rq.delete(meta_host, data=data, headers=header)
    del_r.raise_for_status()
    d_thing = del_r.json()

    if not "t" in d_thing:
        logging.error("Error when trying to delete %s" % (thing,))
        raise ValueError(d_thing)

    return d_thing["t"]


def thing_tree2ts(top):
    """Walk a tree of parts and yield all time series objects
    (ttype in [tseries, qctseries, gpstrack])

    Args:
        top: Top thing node in the tree

    Returns:
        Next time series dictionary in the iterator

    Useage:
        all_ts = [ts for ts in thing_tree2ts(thing_root)]
    """
    if top.get("parts", False) and len(top["parts"]) > 0:
        for t in top["parts"]:
            for ct in thing_tree2ts(t):
                yield ct
    if top.get("ttype") in ["tseries", "qctseries", "gpstrack"]:
        yield top
