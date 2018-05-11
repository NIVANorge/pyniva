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


## metaflow - meta data and "Thing" universe
`metaflow` is NIVA's service and API for meta data. This service
allows for searching meta data, and retrieving all stored meta data
for data objects ("Things").

In `metaflow` and in the `pyniva` API-wrapper all data objects are
represented as `Thing` class instances or a subclass of `Thing`.
Using the `pyniva` wrapper search and detailed meta data is also
available through `Thing` classes (see examples bellow).

`pyniva` exposes/includes URLs to public and internal `metaflow`
endpoints.
* PUB\_PLATFORM (public endpoints to get list of FerryBox/Glider platforms)
* PUB\_DETAIL (public endpoint for detailed information about a data object)
* META\_HOST (internal endpoint for all meta data, edit to fit your installation)

```python
# Get list of available vessels in metaflow, print their names
# and the number of avaliable time series for each vessel
from pyniva import Vessel, PUB_DETAIL, PUB_PLATFORM, token2header

header = token2header("path/to/my/tokenfile.json")

vessel_list = Vessel.list(PUB_PLATFORM, header=header)
for v in vessel_list:
    time_series = v.get_all_tseries(PUB_DETAIL, header=header)
    print(v.name, len(time_series))
```

To get all available meta data for a `Thing` (or subclass) instance
you can call the `to_dict()` method which will return all meta data
as a Python dictionary.
```python
print(v.to_dict())
```

Objects in the `Thing` hierarchy will have different attributes,
depending on type, etc. For more information take a look at the
doc-string of the `Thing` instances you are interested in or use the
Python `dir()` method to examine the object data. In general, any
key not starting with an `_` in the dictionary returned by `to_dict()`
is also available as instance attributes.
All `Thing` or subclass of `Thing` instances
persisted by `metaflow` will at least have an `uuid` and a
`ttype` attribute.



## tsb - time series data
Time series data is stored in designated time series database(s) and
the actual data can be accessed through `tsb` service.

The `tsb` API is intended for interactive use, visualization, data
"dril in" and merging of asynchronous-heterogenous time series data.
Including merging of data on GPS tracks.
This means that the typical use of the API is _not_ to downlaod all
avaliable raw data (which can be huge), instead the user will query
and fetches aggregated data for a given time interval (typically 1000 or
less data-ponts pr. time series).

Also note that for time series the API support interactive use and visualization
by doing server side  aggregating of the data (including aggregation of data
on (asynchronous) GPS tracks).
This means that the consumer should avoid using the API to download all raw data
for client side aggregation etc.


Using the `pyniva` library you can access and query data through
`TimeSeries` objects (or subclasses). This allows direct access to the data
while hiding the details of the underlying `tsb` service.
When querying through `pyniva` data is returned as time indexed
[Pandas](https://pandas.pydata.org/) which is convenient for further
analyses, plotting, data export, etc.

The `tsb` system holds and handles three kinds of asynchron time series:
* "normal" time series (`TimeSeries` class),
  which is a time indexes sequence of single numerical
  (floating point) values, i.e. one numerical value for each time stamp,
  for this datatype there can also be a quality flag for each measuremen.
  This flag will typically be -1 for "bad quality",
  0 for quality flag not set, or +1 for "good quality". When querying data
  you can filter on the flag (but the actual flags are not returned).
* Flags and/or event data time series (`FlagTimeSeries` class), implemented as a
  time indexed sequence of integers. This datatype is also used for
  individual data quality flags. For this datatype the standard aggregation
  type is `mode` which returns the most frequent value in the interval.
* GPS tracks (`GPSTrack` class), which is a time indexed sequence of
  longitud and latitude values (WGS84). GPS tracks can be used for geo-fencing
  and they are aggregaetd by keeping actual data at (near) wanted time intervals.


WORKING HERE:
* https://ferrybox-api.niva.no/v1/signal/ListOfUuids/StartTime/EndTime
where the 'ListOfUuids' is a comma separated list of signal UUIDs to query.
The 'StartTime' and 'EndTime' parameters are the start and end time for the
query period (ISO8601 time-stamp string).

In addition the API support the following additional parameters:
* *dt*, time span in aggregation [ISO8601](https://en.wikipedia.org/wiki/ISO_8601#Durations)
  representation of time window
* *agg_type*, aggregation type, possible values:
  "avg" (default), "min", "max", "sum", "count", "stddev", "mode", "median" and "percentile"
* *percentile* if agg\_type is percentile the API also requires this parameter to be
  set, floating point number between 0 and 1



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


## Usage and examples

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

