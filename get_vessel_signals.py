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

from pyniva import Vessel, TimeSeries, token2header, META_HOST, PUB_PLATFORM
from pyniva import PUB_DETAIL, TSB_HOST, PUB_SIGNAL

def main(start_time=None, end_time=None, token_file=None,
         all_signals=False, out_file_prefix=None,
         noffill=None, dt=None):
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
    
    if end_time is not None:
        end_time = parse(end_time)
    else:
        end_time = datetime.utcnow()
    if start_time:
        start_time = parse(start_time)
    else:
        start_time = end_time - timedelta(5)

    logging.info("%s -> %s" % (start_time, end_time))

    if dt is None:
        # Query raw data
        dt = "PT0H"

    # Query list of avaliable vessels
    v_list = Vessel.list(meta_list, header=header)
    for v in v_list:
        logging.info("getting signals from %s : %s" % (v.name, v.uuid))
        # Get signals the vessel
        signals = v.get_all_tseries(meta_host, header=header)

        if all_signals:
            int_ts = signals
        else:
            int_signals = ["TEMPERATURE",
                           "TURBIDITY",
                           "SALINITY",
                           "OXYGEN",
                           "gpstrack"]
            int_ts = [ts for sn in int_signals 
                        for ts in signals 
                        if sn.lower() in ts.path.lower() and ts.ttype in ("gpstrack", "tseries")]
        
        for ts in int_ts:
            logging.info("%s : %s " %  (ts.path, ts.uuid))

        if len(int_ts) > 0:
            if noffill:
                data = TimeSeries.get_timeseries_list(tsb_host, int_ts,
                                                  start_time=start_time, # datetime.utcnow() - timedelta(15),
                                                  end_time=end_time, # datetime.utcnow(),
                                                  header=header,
                                                  nofill=True,
                                                  dt=dt,
                                                  name_headers=True)
            else:
                data = TimeSeries.get_timeseries_list(tsb_host, int_ts,
                                                  start_time=start_time, # datetime.utcnow() - timedelta(15),
                                                  end_time=end_time, # datetime.utcnow(),
                                                  header=header,
                                                  dt=dt,
                                                  name_headers=True)

            if out_file_prefix:
                # save the dataframe
                out_file_name = "%s_%s.csv" % (out_file_prefix,
                                               re.sub(r'\W', '', v.name))
                logging.info("saving data to: %s" % (out_file_name,))
                data.to_csv(out_file_name)
# end of main function


if __name__ == '__main__':
    import argparse

    # Set up and parse command line arguments
    parser = argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-s", "--start-time", required=False, dest="start",
            help="Start time of query interval", default=None)
    parser.add_argument("-e", "--end-time", required=False, dest="end",
            help="End time of query interval", default=None)
    parser.add_argument("-t", "--token-file", required=False, dest="token",
            help="JWT token file (JSON format) for NIVA account", default=None)
    parser.add_argument("-o", "--out-file-prefix", required=False, dest="out_file_prefix",
            help="Prefix for output files, if not included nothing is stored", default=None)
    parser.add_argument("--all-signals", required=False,
            help="Query all available signals, if not set only selected signals will be quied",
            action="store_true", dest="all_signals")
    parser.add_argument("-w", "--time-window", required=False, dest="dt",
            help="Time window in aggregate, if not included raw data is returned", default=None)    
    parser.add_argument("--noffill", required=False,
            help="Turn off ffill when merging with GPS-track",
            action="store_true", dest="noffill")
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
    main(start_time=args.start, end_time=args.end, token_file=args.token,
         all_signals=args.all_signals, out_file_prefix=args.out_file_prefix,
         noffill=args.noffill, dt=args.dt)
    logging.info("Script finished")
