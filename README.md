# NIVA Platform
Library and API wrapper(s) for programatic (Python) access to data in NIVA's data platform
and services.

Currently the following parts/APIs are supported:
* NIVA Flow (`metaflow` for meta data access)
* `tsb` for access to time series data (including FerryBox)

## metaflow

## tsb


# Installation
The package and all it's dependencies can be installed using `pip` (setuptools)

* Download and unpack the source code
* Navigate to `nivaplatform` directory
```
$ cd nivaplatform
```
* Install package using pip install
```
pip install --editable .
```


## Examples

```python
from datetime import datetime, timedelta

from nivaplatform import Vessel, TimeSeries, token2header, META_HOST, PUB_PLATFORM
from nivaplatform import PUB_DETAIL, TSB_HOST, PUB_SIGNAL

vessel_list = Vessel.list(meta_list, header=header)
for v in vessel_list:
    print(v.name)
    # Get signals the vessel
    signals = v.get_all_tseries(meta_host, header=header)

    interesting_signals = ["raw/ferrybox/INLET_TEMPERATURE",
                       "raw/ferrybox/TURBIDITY",
                       "raw/ferrybox/CTD_SALINITY",
                       "gpstrack"]
    int_ts = [ts for sn in interesting_signals 
                 for ts in signals if sn in ts.path]
    for ts in int_ts:
        print("  ", ts.path)

    if len(int_ts) > 0:
        data = TimeSeries.get_timeseries_list(tsb_host, int_ts,
                                              start_time=datetime.utcnow() - timedelta(7),
                                              end_time=datetime.utcnow(),
                                              header=header,
                                              noffill=True)
        print(data.head())

```