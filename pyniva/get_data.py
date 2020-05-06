#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functions to authenticate against and grab data from NIVA API endpoints
"""
__all__ = ["get_data", "token2header", "PyNIVAError"]
import logging
from datetime import timedelta
import json
import requests
import jwt
import io
from isodate import parse_duration


class PyNIVAError(Exception):
    """Exception wrapper for Thing universe
    """
    pass


def validate_query_parameters(**params):

    if "dt" not in params.keys() and "n" not in params.keys():
        logging.warning("Your data will be aggregated to yield 1000 points."
                        " To change this behavior you should set either n or dt parameters.")


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
    r = rq.get(url, headers=headers, params=params)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        raise PyNIVAError(r.json()['error'])

    full_data = r.json()

    # If no error occurred the data is found in the "t" attribute of
    # returned data
    if isinstance(full_data.get("t"), list):
        return full_data["t"]
    else:
        return full_data


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
        "email": cmrsa["client_email"]
    }

    token = jwt.encode(payload, cmrsa["private_key"], algorithm="RS256")
    header = { "Authorization": b"Bearer " + token }
    return header