# Changelog

## 0.5.3
  - bugfix

## 0.5.2
  - tiny log change 
  
## 0.5.1
- Fix issues with missing parameter querying and add unit tests for new query functions (get_ship_data)

## 0.5.0
additional query function in request_dataframe.py
- dataframe columns names are paths instead of names

## 0.4.3

- upgraded pandas version to 1.1

## 0.4.2

- upgraded python image used for building and publishing in circleci to 3.8.3
  - hopefully this resolves problems publishing package with markdown format long_description

## 0.4.1

- added pyniva version as user agent header to all requests made to the API
- Updated readme and added it to long_description making it appear at
  - removed all references to update/delete/create functions in pyniva. These do not work and are not exposed.

## 0.4.0

- clientside parameter checking of parameters
- handling of serverside http errors with status 400
  - typical in cases where invalid arguments are passed
- added trace-id to all requests, and a message on errors which print the error from the server
  in addition to the trace id and instructions on how to contact us with reference to cloud@niva.no email

## 0.3.1 - 0.3.2

- fix package metadata and published package on pypi

## 0.3.0 (2019-08-27)

- Added `raise_for_status` to some Requests calls. Some calls will
  raise `HTTPError` instead of for example `JSONDecodeError`.
- Add a `session` parameter to methods that do HTTP requests (directly
  or indirectly) so that we can do connection pooling and tracing, etc.
