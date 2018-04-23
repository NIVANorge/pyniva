#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick and dirty script to explore temp data issue in GDM data
"""
import sys
import logging
from datetime import datetime, timedelta
import re
import matplotlib.pyplot as plt

from pyniva import Vessel, TimeSeries, token2header, META_HOST, PUB_PLATFORM
from pyniva import PUB_DETAIL, TSB_HOST, PUB_SIGNAL
from dateutil.parser import parse

header = None
meta_host = META_HOST
meta_list = META_HOST
tsb_host = TSB_HOST
print(meta_host, tsb_host)

imos = [9278234, 9233258, 9197404]
# Make list of time series to query

for imo in imos:
    v = Vessel.get_thing(meta_host, {"imo": imo})
    c_signals = v.get_all_tseries(meta_host)
    print(v.name, imo, len(c_signals))
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
    glob_tests = [s for s in qcts_list if 'system' in s.path.lower()]

    ts_total_list = ts_list + temp_tests + glob_tests
    ts_names = [s.name for s in ts_list]
    temp_test_names = [s.name for s in temp_tests]
    glob_test_names = [s.name for s in glob_tests]


    data = TimeSeries.get_timeseries_list(tsb_host, ts_total_list,
                                          start_time=parse('2018-04-16'), #datetime.utcnow() - timedelta(5),
                                          end_time=parse('2018-04-21'), # datetime.utcnow(),
                                          header=header,
                                          # noffill=True,
                                          dt="PT0H",
                                          name_headers=True)# , # ) #,
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
        axs[1].set_ylabel("QC flag")
        axs[1].set_ylim((-1.1,1.1))
        data.loc[:, temp_test_names].plot(style='.', ax=axs[1]) # , label=data.columns)
        axs[1].grid(True)
        axs[2].set_ylabel("QC flag")
        axs[2].set_ylim((-1.1,1.1))
        data.loc[:, glob_test_names].plot(style='.', ax=axs[2]) # , label=data.columns)
        axs[2].grid(True)




        # plt.subplot(212)
        # Plot the QC flags

        fig.savefig("%s.png" % (re.sub(r'\W', '', v.name),), format='png')
        # fig.show()