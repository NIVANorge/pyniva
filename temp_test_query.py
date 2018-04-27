#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick and dirty script to explore temperatur data issue in data available for GDM
"""
import sys
import logging
from datetime import datetime, timedelta
import re
import matplotlib.pyplot as plt

from pyniva import Vessel, TimeSeries, token2header, META_HOST, PUB_PLATFORM
from pyniva import PUB_DETAIL, TSB_HOST, PUB_SIGNAL

from dateutil.parser import parse


imos = [9278234, 9233258, 9197404]
# Make list of time series to query


def main(start_time=None, end_time=None, token_file=None, dt=None):
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

    vessels = Vessel.list(meta_list, header=header)
    vessels = [v for v in vessels if hasattr(v, "imo") and v.imo in imos]
    for v in vessels:
        # v = Vessel.get_thing(meta_host, {"imo": imo})
        c_signals = v.get_all_tseries(meta_host, header=header)
        print(v.name, v.imo, len(c_signals))
        ts_list = []
        for s in c_signals:
            # if ('ctd_temp' in s.path.lower() or 'inlet_temp' in s.path.lower()) and 'ferr' in s.path.lower(): #  and '_flag' not in s.path.lower():
            if ('inlet_temp' in s.path.lower() or 'ctd_temp' in s.path.lower()) and 'ferr' in s.path.lower() and '_flag' not in s.path.lower():
                # or 
                # 'oxygen' in s.path.lower()) 
                
                print("   ", s.path, s.uuid)
                ts_list.append(s)

        qcts_list = []
        for s in c_signals:
            if 'ferr' in s.path.lower() and '_flag' in s.path.lower() and ('system' in s.path.lower() or 'inlet_temp' in s.path.lower()):
                print("      ", s.path, ":", s.uuid)
                qcts_list.append(s)

        temp_tests = [s for s in qcts_list if 'inlet_temp' in s.path.lower()]
        glob_tests = [s for s in qcts_list if 'system' in s.path.lower() and 'pump_history' in s.path.lower()]

        ts_total_list = ts_list + temp_tests + glob_tests
        ts_names = [s.name for s in ts_list]
        temp_test_names = [s.name for s in temp_tests]
        glob_test_names = [s.name for s in glob_tests]


        data = TimeSeries.get_timeseries_list(tsb_host, ts_total_list,
                                              start_time=start_time, # parse('2018-04-18'), #datetime.utcnow() - timedelta(5),
                                              end_time=end_time, # parse('2018-04-24'), # datetime.utcnow(),
                                              header=header,
                                              noffill=True,
                                              dt=dt,
                                              name_headers=True) #,
                                              # noqc=True)

        if data.shape[0] > 0:
            # print(data.head())
            # plt.figure()
            # plt.subplot(211)
            fig, axs = plt.subplots(3,1, sharex=True)
            fig.set_size_inches(10, 14, forward=True)
            axs[0].set_title(v.name)
            # plt.title(v.name)
            axs[0].set_ylabel(r'Temperature $[C^o]$')
            axs[2].set_xlabel(r'Time')
            data.loc[:, ts_names].plot(style='.', ax=axs[0]) # , label=data.columns)
            axs[0].grid(True)

            if len(temp_test_names) > 0:
                axs[1].set_ylabel("QC flag")
                axs[1].set_ylim((-1.1,1.1))
                data.loc[:, temp_test_names].plot(style='.', ax=axs[1]) # , label=data.columns)
                axs[1].grid(True)
            if len(glob_test_names) > 0:
                axs[2].set_ylabel("QC flag")
                axs[2].set_ylim((-1.1,1.1))
                data.loc[:, glob_test_names].plot(style='.', ax=axs[2]) # , label=data.columns)
                axs[2].grid(True)


            # plt.subplot(212)
            # Plot the QC flags

            fig.savefig("%s.png" % (re.sub(r'\W', '', v.name),), format='png')
            # fig.show()


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
    parser.add_argument("-w", "--time-window", required=False, dest="dt",
            help="Time window in aggregate, if not included raw data is returned", default=None)    
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
    main(start_time=args.start, end_time=args.end, token_file=args.token, dt=args.dt)
    logging.info("Script finished")
