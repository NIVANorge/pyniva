# Changelog

## 0.3.0 (2019-08-27)

- Added `raise_for_status` to some Requests calls. Some calls will
  raise `HTTPError` instead of for example `JSONDecodeError`.
- Add a `session` parameter to methods that do HTTP requests (directly
  or indirectly) so that we can do connection pooling and tracing, etc.
