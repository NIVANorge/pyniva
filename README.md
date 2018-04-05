# Python wrapper for NIVA's Data Platform
`pyniva` is a Python library and API wrapper(s) for programatic access to data
in NIVA's data platform and services.

Currently the following parts/APIs are supported:
* NIVA Flow (`metaflow` for meta data access)
* `tsb` for access to time series data (including FerryBox)

The library can connect to public exposed end-points and
directly to our internal services (the latter is usefull for
testing).

## General information
The external APIs uses [jwt](https://jwt.io/) for user authentication and secure
data transfer. In order to use these you'll need to get a JWT access token (JSON file),
which contains account information and a private ssh key.

The internal services does
not require any authentication and they offers no access control to data-sets,
but you'll need access to the network where the services are running. So in practice
this will be used for testing and development towrads local development service
instances.


Note that the APIs are intended for interactive use, where the user fetches and
search for meta data and available data sets, and then query the actual data.

Also note that for time series, the API (`tsb`) is buildt to support interactive
use and visualization by doing server side  aggregating of the data (including
aggregation of data on (asynchronous) GPS tracks).
This means that the consumer should in general avoid using the API to download all raw data
for client side aggregation etc.

Internally, all objects, including time-series (signals), are identified and queried using
[UUIDs](https://en.wikipedia.org/wiki/Universally_unique_identifier).
The `pyniva` library wraps and hides this from the end user, allowing access to
and querying of data objects through Python object instances.

All timestamps returned from the APIs are in UTC.
All the endpoints return data in JSON format.


## metaflow - meta data
Some information on the meta data model and the Thing universe.

At the moment there are two endpoints for querying meta data for FerryBox vessels
and signals:
* https://ferrybox-api.niva.no/v1/vessels
Return a list of FerryBox available vessels.
* https://ferrybox-api.niva.no/v1/details/UuidOfObject
Used to get additional (complete) information about an object, including
meta data for signals attached to the object (if present)



## tsb - time series data
`tsb` is the API (service) used to query, aggregate and join time series
data.

* https://ferrybox-api.niva.no/v1/signal/ListOfUuids/StartTime/EndTime
where the 'ListOfUuids' is a comma separated list of signal UUIDs to query.
The 'StartTime' and 'EndTime' parameters are the start and end time for the
query period (ISO8601 time-stamp string).

In addition the API support the following additional parameters:
* *dt*, time span in aggregation [ISO8601](https://en.wikipedia.org/wiki/ISO_8601#Durations)
  representation of time window
* *agg_type*, aggregation type, possible values:
  "avg" (default), "min", "max", "sum", "count", "stddev", "mode", "median" 


NOTE:
* *Time aggregation*: You are not guarantied to get the exact time spans asked for
  the server will try to match the requested time windows with 1, 2, 5, 10 or 30
  multiples of seconds, minutes, hours and days. And return the nearest match 
* *Geo fencing*: Since only data from withing a particular geographical region is
  returned in the query, you must include the uuid of the vessels GPS-track
  in order to receive data. Also the time spans in the time aggregation will
  match the actual time stamps in the GPS track signal.



# Installation
The package and all it's dependencies can be installed using `pip` (setuptools)

* Download and unpack the source code
```
$ git clone git@github.com:NIVANorge/pyniva.git
```

* Navigate to `pyniva` directory
```
$ cd pyniva
```

* Install package using pip install
```
pip install --editable .
```

## Non-standard dependancies
The package uses these non standard Python libraries.
* [pandas](https://pypi.python.org/pypi/pandas/)
* [numpy](http://www.numpy.org/)
* [requests](https://pypi.python.org/pypi/requests/)
* [pyjwt](https://pypi.python.org/pypi/PyJWT/)
* [cryptography](https://pypi.python.org/pypi/cryptography/)
All the packages will be installed automaticalluy if `pyniva` is installed
using pip (as indicated above).


## Examples
FIXME: more and better examples

```python
from datetime import datetime, timedelta

from pyniva import Vessel, TimeSeries, token2header, META_HOST, PUB_PLATFORM
from pyniva import PUB_DETAIL, TSB_HOST, PUB_SIGNAL

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

