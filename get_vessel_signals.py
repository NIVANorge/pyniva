#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to read time series tsb backend
"""
import sys
import logging
from datetime import datetime, timedelta

from pyniva import Vessel, TimeSeries, token2header, META_HOST, PUB_PLATFORM
from pyniva import PUB_DETAIL, TSB_HOST, PUB_SIGNAL

def main(token_file=None):
    if token_file is not None:
        # Use public NIVA endpoint
        header = token2header(token_file)
        meta_host = PUB_DETAIL
        meta_list = PUB_PLATFORM
        tsb_host = PUB_SIGNAL
    else:
        # Use internal metaflow and tsb endpoints
        header = None
        meta_host = META_HOST
        meta_list = META_HOST
        tsb_host = TSB_HOST

    # Query list of avaliable vessels
    v_list = Vessel.list(meta_list, header=header)
    for v in v_list:
        print(v.name)
        # Get signals the vessel
        signals = v.get_all_tseries(meta_host, header=header)

        int_signals = ["TEMPERATURE",
                       "TURBIDITY",
                       "SALINITY",
                       "gpstrack"]

        int_ts = [ts for sn in int_signals 
                     for ts in signals 
                       if sn.lower() in ts.path.lower() and ts.ttype in ("gpstrack", "tseries")]
        for ts in int_ts:
            print("  ", ts.path, ":", ts.uuid)

        if len(int_ts) > 0:
            data = TimeSeries.get_timeseries_list(tsb_host, int_ts,
                                                  start_time=datetime.utcnow() - timedelta(15),
                                                  end_time=datetime.utcnow(),
                                                  header=header,
                                                  noffill=True,
                                                  dt="PT0H",
                                                  name_headers=True)
            print(data.shape)
            print(data.head())

# end of main function


if __name__ == '__main__':
    import argparse

    # Set up and parse command line arguments
    parser = argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-t", "--token-file", required=False, dest="token",
            help="JWT token file (JSON format) for NIVA account", default=None)
    parser.add_argument("--debug", required=False,
            help="Set debug flag for more detailed logging",
            action="store_true", dest="debug")
    parser.add_argument("-l", "--log-file", required=False,
            help="Path to log-file (default STDOUT)",
            default=sys.stdout, dest="logfile")
    args = parser.parse_args()

    # Set up logger
    LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(filename)s:%(lineno)s:%(funcName)s:%(message)s"
    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    if args.logfile == sys.stdout:
        logging.basicConfig(stream=args.logfile, level=log_level, format=LOG_FORMAT)
    else:
        logging.basicConfig(filename=args.logfile, level=log_level, format=LOG_FORMAT)

    logging.info("Script started")
    main(token_file=args.token)
    logging.info("Script finished")
