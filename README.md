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

The `metaflow` service stores all meta-data as JSON documents with
a set of specific reserved fields, including `ttype` which is
used to identify the object type of the meta data. These
object types is mapped directly to the Thing objects exposed
in the `pyniva` API wrapper.

In `metaflow` and in the `pyniva` API-wrapper all data objects are
represented as `Thing` class instances or a subclass of `Thing`.
Using the `pyniva` wrapper search and detailed meta data is also
available through `Thing` classes (see examples bellow).


The "Thing universe" is a simple hierarchy of classes,
with the generic "Thing" as base class. In `pyniva` all objects
and data are represented as "Thing" instances. Access to meta-data
and data is provided through class and instance methods of "Things"
(including query and retrieval of time-series).

Currently the following classes are implemented and supported by
the `metaflow` back-end:
```
Thing (ttype = 'thing')
  |
  |-> Platform (ttype = 'platform')
  |   |
  |   |-> Vessel (ttype = 'vessel')
  |
  |-> Component (ttype = 'component')
  |  |
  |  |-> Sensor (ttype = 'sensor')
  |
  |-> TimeSeriers (ttype = 'tseries')
     |
     |-> FlagTimeSeries (ttype = 'qctseries')
     |
     |-> GPSTrack (ttype = 'gpstrack')
```
The type of an object is defined by the `ttype` attribute of
an instance (i.e. the `ttype` attribute of the underlying
JSON document), and it is straightforward to extend the data model
with new types and functionality.

All public methods in `pyniva` has informative docstrings.

`pyniva` also exposes/includes URLs to public and internal `metaflow`
endpoints.
* PUB\_META (public endpoints to get meta data)
* META\_HOST (internal endpoint for all meta data, edit to fit your installation)

### Creating new Things
New Thing instances are created using the standard Python constructor,
and it takes named parameters and/or a dictionary with object attributes.

Example:
```python
new_timeseries = TimeSeries(name="testseries", path="test/testseries", unit="V")
new_timeseries2 = TimeSeries({"name": "testseries", "path": "test/testseries",
                              "unit": "V"})
```
these two are equivalent.

Note that new objects are _not persisted_ in `metaflow`, and you'll have to
explicitly save them using the `thing.save()` instance method.
```python
saved_thing = thing.save(meta_host, header=header)
```
Note that `save()` method is recursive, so saving an object with children present in
the `parts` attribute will also save the children, children's children, etc. 

### Getting Things from 'metaflow'
The following class methods will search and/or fetch meta-data
from the `metaflow` and return the data as a Thing instance or
a list of Thing instances.
* `Thing.get_thing(meta_endpoint, header=header, params=params, **kwargs)`
* `Thing.list(meta_endpoint, header=header, params=params, **kwargs)`
* `Thing.get_or_create(meta_endpoint, header=header, params=params, **kwargs)`

Arguments can be passed as a parameter dictionary and/or as keyword arguments.
```python
new_vessel = Vessel.get_or_create(meta_host, header=header, params={"name": "MS New"})
```
is equivalent to
```python
new_vessel = Vessel.get_or_create(meta_host, header=header, name="MS New")
```

### Getting meta data and domain model
To get the full domain model of a Thing instance use the `thing.get_tree()` instance
method:
```python
thing_tree = thing.get_tree(meta_host, header=header)
```
Note that the `thing` instance have to be present in `metaflow`.


### Deleting meta-data
To delete a Thing instance in `metaflow` use the `thing.delete()` instance method.
```python
thing.delete(meta_host, header=header)
```
Note that deleting an object in `metaflow` has the side effect removing the 'part_of' attribute
for any child object in the database (this keeps the DB consistent).

The `delete()` method can also delete a full object tree if the parameter `recursive=True` is set:
```python
thing_tree.delete(meta_host, header=header, recursive=True)
```


### Examples
```python
# Get list of available vessels in metaflow, print their names
# and the number of avaliable time series for each vessel
from pyniva import Vessel, PUB_META, PUB_TSB, token2header

header = token2header("path/to/my/tokenfile.json")

# Get list of all available vessels
vessel_list = Vessel.list(PUB_META, header=header)
for v in vessel_list:
    time_series = v.get_all_tseries(PUB_META, header=header)
    print(v.name, len(time_series))

# Get the full domain model for the first vessel in the list
vessel = vessel_list[0]
vessel_full = vessel.get_tree(PUB_META, header=header)
```

To get all available meta data for a `Thing` (or subclass) instance
you can call the `to_dict()` method which will return all meta data
as a Python dictionary.
```python
print(v.as_dict())
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


### Notes and chevats
* Saves, updates and deletes can render your Python model inconsistent,
  since the methods don't change objects in place but return an updated
  object.
  


## tsb - time series data
Time series data is stored in designated time series database(s) and
the actual data can be accessed through `tsb` service.

`pyniva` exposes/includes URLs to public and internal `tsb`
endpoints.
* PUB\_TSB (public endpoint for time series data)
* TSB\_HOST (internal  endpoint for time series data)

The `tsb` API is intended for interactive use, visualization, data
"drill in" and merging of asynchronous-heterogenous time series data.
Including merging of data on GPS tracks.
This means that the typical use of the API is _not_ to download all
avaliable raw data (which can be huge), instead the user will query
and fetches aggregated data for a given time interval (default is
approximately 1000 data-points pr. time series).
The default number of data points can be overridden by setting
the `n` or `dt` parameter in the query. `dt=0` returns raw data
(not reccomended for large datasets).


Using the `pyniva` library you can access and query data through
`TimeSeries` class (or subclasses) or `TimeSeries` instances.
This allows direct access to the data
while hiding the details of the underlying `tsb` service.
When querying through `pyniva` data is returned as time indexed
[Pandas](https://pandas.pydata.org/) which is convenient for further
analyses, plotting, data export, etc.

The `tsb` system holds and handles three kinds of asynchron time series:
* "normal" time series (`TimeSeries` class),
  which is a time indexes sequence of single numerical
  (floating point) values, i.e. one numerical value for each time stamp,
  for this datatype there can also be a quality flag for each measurement.
  This flag will typically be -1 for "bad quality",
  0 for quality flag not set, or +1 for "good quality". When querying data
  you can filter on the flag (but the actual flags are not returned).
* Flags and/or event data time series (`FlagTimeSeries` class), implemented as a
  time indexed sequence of integers. This datatype is also used for
  individual data quality flags. For this datatype the standard aggregation
  type is `mode` which returns the most frequent value in the interval.
* GPS tracks (`GPSTrack` class), which is a time indexed sequence of
  longitude and latitude values (WGS84). GPS tracks can be used for geo-fencing
  and they are aggregaetd by keeping actual data at (near) wanted time intervals.
  Note that if a `GPSTrack` is in the query list data will be merged with the track
  and the aggregation intervals will be dictated by the data in the `GPSTrack`

The `TimeSeries` class has two methods for quering time series data:
* `get_tseries()` (instance method) to queries and fetch data corresponding to
  the instance in question.
* `get_timeseries_list()` (class method) which takes a list of `TimeSeries`
  instances and return a joined dataset for the time series.

### Query parameters
These interfaces takes and requiers the same set of parameters. The following
parameters are must be included:
* *ts_host*, url for the `tsb` service (in practice this will be `PUB_SIGNAL` or `TSB_HOST`)
* *headers*, if `PUB_SIGNAL` is used a `JWT` header must also be included
  (for documentation see `token2header()` documentation above)
* *a time range* for the query

There are two ways to specify the time span The parameters used to set the time range in a query are:
* `start_time` and `end_time` (start and end time of query)
* `ts` (time span of query)

All timestamps and time spans are assumed to be ISO8601 formatted string, with
one exception: `end_time=now` which will force end-time into `datetime.utcnow()`
 
Time intervals can be expressed in several ways with a combination of the three parameters:
1. As an ISO8601 time interval ("ts") parameter with start and end time.
   Examples: `ts=2007-03-01T13:00:00Z/2008-05-11T15:30:00Z`
             `ts=P1Y2M10DT2H30M/2008-05-11T15:30:00Z`
2. As explicit start and end parameters (ISO8601 formatted)
       Example: `start_time=2017-01-01T00:10:10.82812`
                `end_time=2017-02-01T10:21:33.15`
3. As a time interval parameter ("ts") and either a corresponding
       "start" or "end" parameter or implicit end=now by omitting 
       start/end parameters.
       Example: `ts=PT1H10M10.03S`
                `end=2013-10-12T10`
       Example: `ts=P1M` (one month ending now)

Also note that the API has the following default behavior:
1. If start and end parameters are both given any given "ts" parameter will be ignored 
2. If no parameters are given the function will return one week ending now
3. If only a time span (without start or end) are given end time is set to now


#### Optional parameters
In addition the API support the following additional parameters:
* *n* (integer): approximate number of data-points to return from the query. If neither *dt* nor
*n* is set a default value of n = 1000 will be used.
* *dt*, time span in aggregation, corresponding to number of seconds. 
Also note that the API don't guarantee that the returned time spans will match the requested string, it will just try to
match it as close as possible with a valid Timescale [time aggregation string](http://docs.timescale.com/latest/api#select).
If dt is set to zero, raw data are requested. 
* *agg_type*, aggregation type, possible values:
  "avg" (default), "min", "max", "sum", "count", "stddev", "mode", "median" and "percentile"
* *percentile* if agg\_type is percentile the API also requires this parameter to be
  set, floating point number between 0 and 1
* *noqc* (flag, true if included): flag to ignore the Data Quality flag in the query.
  If not included only data which has passed the data quality check will be returned. 
* *region* (WKT string): Only return data from inside a given geographical region.
  The argument must be a region (polygon) defined as a
  [WKT](https://en.wikipedia.org/wiki/Well-known_text) string where the
  coordinates are assumed to be in [WGS84](https://en.wikipedia.org/wiki/World_Geodetic_System)
  format.
  Also note: if a region is supplied the query _must also include_ a uuid for an existing GPS track.



### Notes and chevats
* If data is completely missing for a signal the returned DataFrame will not
  include the corresponding column.
* If the all data is missing in a query, an empty DataFrame will be returned.
* *Time aggregation*: You are not guarantied to get the exact time spans asked for
  the server will try to match the requested time windows with 1, 2, 5, 10 or 30
  multiples of seconds, minutes, hours and days. And return the nearest match.
  Raw data is returned if `dt=0` is set. 
* *Geo fencing*: Since only data from withing a particular geographical region is
  returned in the query, you must include a GPSTrack (i.e. the vessel's GPS-track)
  in order to receive data. Also the time spans in the time aggregation will
  match the actual time stamps in the GPS track signal.
* For normal time series queries are _filtered on the data quality_ flag,
  meaning that only data points which has passed QC is included in the
  returned result. This behavior can be overridden using the `noqc` query flag.
* If a GPS-track is included in the query _data is merged with the track_,
   and the GPS-track data is returned as `longitude` and `latitude`.
     1. Only one GPS-track can be submitted at the time
     1. Aggregation level is forced to the GPS-track, with actual
        GPS-track time stamps.



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

## Jupyter notebook

   
Install jupyter notebook with dependencies
```
pip install --user jupyter

# dependencies
pip install --user gmaps
pip install --user bqplot
```

Run jupyter notebook:

```
jupyter notebook pyniva_API_example.ipynb
```


Access the notebook at http://localhost:8888
   
See General information above for information about JWT access tokens.