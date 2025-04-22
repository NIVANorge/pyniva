#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functions to authenticate against and grab data from NIVA API endpoints
"""
__all__ = ["get_data", "token2header", "PyNIVAError", "get_newly_inserted_data"]
import logging
import uuid
import datetime as dt
import json
from math import ceil
from urllib.parse import urljoin
import requests
import jwt
import io

from importlib.metadata import version
__version__ = version("pyniva")

class PyNIVAError(Exception):
    """Exception wrapper for Thing universe"""

    def __init__(self, message, trace_id=None, req_args=None):
        super().__init__(message)
        self.message = message
        self.req_args = req_args
        self.trace_id = trace_id

    def __str__(self):
        return (
            f"Error calling API: {self.message}.\n\n"
            f"Please contact cloud@niva.no for assistance and include the following trace id: {self.trace_id}"
        )


def validate_query_parameters(**params):
    if "dt" not in params.keys() and "n" not in params.keys():
        logging.warning(
            "Your data will be aggregated to yield 1000 points."
            " To change this behavior you should set either n or dt parameters."
        )


def get_data(url, params=None, headers=None, session=None):
    """Get data from NIVA REST endpoints

    Params:
       url (str):         The address of the rest endpoint
       params (dict):     Dictionary with query parameters
       headers (dict):    Header data for the request, must include JWT access token
       session (Session): Requests session object

    Returns:
       The data returned from the endpoint. The structure will depend
       on the query and end-point (dictionaries for meta data, list of
       dictionaries for time series data)
    """
    validate_query_parameters(**params)
    rq = session or requests
    if headers is None:
        headers = {}
    trace_id = str(uuid.uuid4())
    headers["Trace-Id"] = trace_id
    headers["User-Agent"] = f"pyniva/{__version__}"
    response = rq.get(url, headers=headers, params=params)
    tsb_response_raise_for_status(response, trace_id)
    full_data = response.json()

    # If no error occurred the data is found in the "t" attribute of
    # returned data
    if isinstance(full_data.get("t"), list):
        return full_data["t"]
    else:
        return full_data


def tsb_response_raise_for_status(response, trace_id):
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if "application/json" in response.headers.get("Content-Type"):
            body = response.json()
            raise PyNIVAError(
                body.get("message", body),
                trace_id=trace_id,
                req_args=body.get("req_args"),
            )
        else:
            raise PyNIVAError(message=response.text, trace_id=trace_id)


def token2header(token_file):
    """Get JWT token header from GCP service account JSON file

    Params:
        token_file (file-like or string): Open file/file-like object or path to token file

    Returns:
        Dictionary with JWT header for subsequent requests towards NIVA end-points
    """
    if isinstance(token_file, str):
        with open(token_file, "r") as f:
            cmrsa = json.load(f)
    elif isinstance(token_file, (io.TextIOBase, io.BufferedIOBase, io.RawIOBase)):
        cmrsa = json.load(token_file)
    else:
        raise TypeError("token_file must be a file path (str) or an open file handle")

    payload = {
        "iss": cmrsa["client_email"],
        "sub": cmrsa["client_email"],
        "aud": "ferrybox-api.niva.no",
        "email": cmrsa["client_email"],
    }

    token = jwt.encode(payload, cmrsa["private_key"], algorithm="RS256")
    header = {"Authorization": b"Bearer " + token.encode("utf-8")}
    return header


def get_newly_inserted_data(
    start_time: dt.datetime,
    end_time: dt.datetime,
    aggregate: bool,
    meta_host: str,
    ts_host: str,
    headers=None,
    session=None,
):
    params = {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "aggregate": aggregate,
    }

    rq = session or requests
    if headers is None:
        headers = {}
    trace_id = str(uuid.uuid4())
    headers["Trace-Id"] = trace_id
    headers["User-Agent"] = f"pyniva/{__version__}"
    response = rq.get(
        urljoin(ts_host, "time-series-by-insert-time"), headers=headers, params=params
    )
    tsb_response_raise_for_status(response, trace_id)
    data = response.json()

    uuids = list({row["uuid"] for row in data})
    uuid_path_map = {}
    query_size = 80  # Number of uuids to query per request, url length is limited so we need to bunch..
    for i in range(ceil(len(uuids) / query_size)):
        r = rq.get(
            meta_host,
            params={"uuid": ",".join(uuids[i * query_size : (i + 1) * query_size])},
            headers=headers,
        )
        r.raise_for_status()
        t = r.json()
        for thing in t["t"]:
            uuid_path_map[thing["uuid"]] = thing["path"]
    return [{**row, "path": uuid_path_map[row["uuid"]]} for row in data]
